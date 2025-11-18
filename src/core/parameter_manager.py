"""Centralised parameter loading and dependency validation.

Phase 2 of the roadmap calls for a dedicated ParameterManager that owns the
rules spanning pneumatic and geometry subsystems.  The manager reads
``config/app_settings.json`` via :class:`~src.core.settings_service.SettingsService`
(or the lightweight :class:`~src.common.settings_manager.SettingsManager`) and
performs dependency checks that are difficult to express in JSON Schema.

The rules implemented here mirror the bullet list in ``ROADMAP.md``:

* Cylinder volumes: the rod-side chamber must always be smaller than the head
  chamber (``V_r < V_h``) which translates to a rod diameter that is smaller
  than the cylinder bore and positive stroke length.
* Pressure hierarchy: the pneumatic relief thresholds must be strictly
  increasing with a 20%% headroom between the stiff threshold and the safety
  pressure (``relief_safety_pressure >= relief_stiff_pressure * 1.2``).
* Range constraints: ``receiver_volume`` must lie strictly between
  ``receiver_volume_limits.min_m3`` and ``receiver_volume_limits.max_m3``.

Panels can depend on this module instead of duplicating bespoke checks; tests
exercise every rule to keep the contract stable for downstream integrations.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Any, Mapping

from src.common import settings_manager as sm
from src.core.settings_models import dump_settings
from src.core.settings_service import SettingsService, SettingsValidationError


class ParameterValidationError(ValueError):
    """Raised when parameter dependencies are violated."""

    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class ParameterSnapshot:
    """Key sections required for dependency validation."""

    geometry: Mapping[str, Any]
    pneumatic: Mapping[str, Any]


class ParameterManager:
    """Load settings and enforce cross-parameter dependency rules."""

    def __init__(
        self,
        *,
        settings_service: SettingsService | None = None,
        settings_manager: sm.SettingsManager | None = None,
    ) -> None:
        if settings_service is None and settings_manager is None:
            settings_service = SettingsService()
        self._service = settings_service
        self._manager = settings_manager

    # ------------------------------------------------------------------ loaders
    def _load_payload(self) -> Mapping[str, Any]:
        if self._service is not None:
            try:
                model = self._service.load()
            except SettingsValidationError as exc:
                message = str(exc)
                if "geometry" in message.lower():
                    message = message.replace("rod_diameter_m", "rod diameter")
                raise ParameterValidationError([message]) from exc
            return dump_settings(model)

        manager = self._manager or sm.get_settings_manager()
        return {"current": manager.get("", {})}

    @classmethod
    def build_snapshot(cls, payload: Mapping[str, Any]) -> ParameterSnapshot:
        current = payload.get("current") if isinstance(payload, Mapping) else None
        geometry = current.get("geometry") if isinstance(current, Mapping) else None
        pneumatic = current.get("pneumatic") if isinstance(current, Mapping) else None

        if not isinstance(geometry, Mapping) or not isinstance(pneumatic, Mapping):
            raise ParameterValidationError(
                [
                    "Payload is missing current.geometry or current.pneumatic sections",
                ]
            )

        return ParameterSnapshot(dict(geometry), dict(pneumatic))

    def load_snapshot(self) -> ParameterSnapshot:
        payload = self._load_payload()
        if not isinstance(payload, Mapping):  # pragma: no cover - guardrail
            raise ParameterValidationError(["Settings payload must be a mapping"])
        return self.build_snapshot(payload)

    # --------------------------------------------------------------- validations
    @staticmethod
    def _validate_cylinder_volumes(geometry: Mapping[str, Any]) -> list[str]:
        errors: list[str] = []
        try:
            bore = float(geometry["cyl_diam_m"])
            rod = float(geometry["rod_diameter_m"])
            stroke = float(geometry["stroke_m"])
        except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - guardrail
            errors.append(f"Geometry parameters are incomplete or invalid: {exc}")
            return errors

        if bore <= 0 or rod <= 0 or stroke <= 0:
            errors.append(
                "Cylinder geometry must provide positive diameters and stroke length",
            )
            return errors

        if rod >= bore:
            errors.append(
                "Rod diameter must be smaller than cylinder bore to satisfy V_r < V_h",
            )
            return errors

        area_head = pi * (bore / 2.0) ** 2
        area_rod = area_head - pi * (rod / 2.0) ** 2
        head_volume = area_head * stroke
        rod_volume = area_rod * stroke

        if rod_volume >= head_volume:
            errors.append(
                (
                    "Computed rod chamber volume must be smaller than head volume "
                    f"(V_r={rod_volume:.6f} m³, V_h={head_volume:.6f} m³)"
                ),
            )

        return errors

    @staticmethod
    def _validate_pressure_hierarchy(pneumatic: Mapping[str, Any]) -> list[str]:
        errors: list[str] = []
        required_keys = (
            "relief_min_pressure",
            "relief_stiff_pressure",
            "relief_safety_pressure",
        )
        try:
            min_pressure = float(pneumatic["relief_min_pressure"])
            stiff_pressure = float(pneumatic["relief_stiff_pressure"])
            safety_pressure = float(pneumatic["relief_safety_pressure"])
        except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - guardrail
            missing = [key for key in required_keys if key not in pneumatic]
            errors.append(
                f"Pneumatic relief thresholds are incomplete ({missing}): {exc}",
            )
            return errors

        if not (min_pressure > 0 and stiff_pressure > 0 and safety_pressure > 0):
            errors.append("Relief pressures must be positive values")
            return errors

        if not min_pressure < stiff_pressure < safety_pressure:
            errors.append("Relief thresholds must increase: min < stiff < safety")

        if safety_pressure < stiff_pressure * 1.2:
            errors.append(
                "Safety pressure must be at least 20% higher than stiff threshold",
            )

        return errors

    @staticmethod
    def _validate_receiver_volume(pneumatic: Mapping[str, Any]) -> list[str]:
        errors: list[str] = []
        limits = pneumatic.get("receiver_volume_limits")
        try:
            receiver_volume = float(pneumatic["receiver_volume"])
            min_volume = (
                float(limits["min_m3"]) if isinstance(limits, Mapping) else None
            )
            max_volume = (
                float(limits["max_m3"]) if isinstance(limits, Mapping) else None
            )
        except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - guardrail
            errors.append(f"Receiver volume constraints are incomplete: {exc}")
            return errors

        if min_volume is None or max_volume is None:
            errors.append("Receiver volume limits must include min_m3 and max_m3")
            return errors

        if min_volume >= max_volume:
            errors.append("Receiver volume limits must satisfy min_m3 < max_m3")
            return errors

        if not (min_volume < receiver_volume < max_volume):
            errors.append(
                (
                    "Receiver volume must fall within configured limits "
                    f"({min_volume} < {receiver_volume} < {max_volume})"
                ),
            )

        return errors

    # ------------------------------------------------------------------- public
    @classmethod
    def _validate_snapshot(cls, snapshot: ParameterSnapshot) -> list[str]:
        errors: list[str] = []
        errors.extend(cls._validate_cylinder_volumes(snapshot.geometry))
        errors.extend(cls._validate_pressure_hierarchy(snapshot.pneumatic))
        errors.extend(cls._validate_receiver_volume(snapshot.pneumatic))
        return errors

    @classmethod
    def validate_payload(cls, payload: Mapping[str, Any]) -> ParameterSnapshot:
        """Validate an already loaded payload and return the snapshot."""

        snapshot = cls.build_snapshot(payload)
        errors = cls._validate_snapshot(snapshot)
        if errors:
            raise ParameterValidationError(errors)
        return snapshot

    def validate(self) -> ParameterSnapshot:
        """Load settings and validate dependency rules.

        Returns the loaded :class:`ParameterSnapshot` if validation succeeds or
        raises :class:`ParameterValidationError` otherwise.
        """

        snapshot = self.load_snapshot()
        errors = self._validate_snapshot(snapshot)

        if errors:
            raise ParameterValidationError(errors)

        return snapshot


__all__ = [
    "ParameterManager",
    "ParameterSnapshot",
    "ParameterValidationError",
]
