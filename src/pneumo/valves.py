"""
Valve components used by the pneumatic simulator.

The legacy test-suite exercises both the modern object oriented API and an
older convenience API that instantiates valves with direct pressure values.
To remain compatible with both styles we provide a flexible implementation
that accepts multiple keyword aliases and persists the last evaluated
pressures so ``is_open()`` can be called with or without explicit arguments.
"""

from __future__ import annotations

from functools import lru_cache
from collections.abc import Mapping

from .enums import CheckValveKind, ReliefValveKind
from .types import ValidationResult
from src.common.errors import ModelConfigError
from config.constants import (
    get_pneumo_relief_orifices,
    get_pneumo_valve_constants,
)


@lru_cache(maxsize=1)
def _check_valve_defaults() -> Mapping[str, float]:
    """Load default check valve parameters from the settings service."""

    constants = get_pneumo_valve_constants()
    context = "constants.pneumo.valves"

    return {
        "delta_open_pa": _coerce_positive_constant(constants, "delta_open_pa", context),
        "equivalent_diameter_m": _coerce_positive_constant(
            constants, "equivalent_diameter_m", context
        ),
    }


@lru_cache(maxsize=1)
def _relief_orifice_defaults() -> Mapping[str, float]:
    """Return relief valve orifice diameters keyed by valve kind."""

    diameters = get_pneumo_relief_orifices()
    return {
        "min": float(diameters["min"]),
        "stiff": float(diameters["stiff"]),
    }


def _coerce_positive_constant(
    container: Mapping[str, object], key: str, context: str
) -> float:
    if key not in container:
        raise ModelConfigError(
            f"Missing required configuration value '{context}.{key}'"
        )
    try:
        numeric = float(container[key])
    except (TypeError, ValueError) as exc:
        raise ModelConfigError(
            f"Configuration value '{context}.{key}' must be numeric"
        ) from exc
    if numeric <= 0.0:
        raise ModelConfigError(
            f"Configuration value '{context}.{key}' must be positive, got {numeric}"
        )
    return numeric


class CheckValve:
    """Directional check valve with optional hysteresis."""

    __slots__ = (
        "kind",
        "delta_open_min",
        "d_eq",
        "hyst",
        "_p_upstream",
        "_p_downstream",
        "_is_open",
    )

    def __init__(
        self,
        kind: CheckValveKind | None = None,
        *args,
        p_upstream: float | None = None,
        p_downstream: float | None = None,
        delta_open_min: float | None = None,
        delta_open: float | None = None,
        d_eq: float | None = None,
        d_eff: float | None = None,
        hyst: float = 0.0,
    ) -> None:
        if kind is not None and not isinstance(kind, CheckValveKind):
            args = (kind, *args)
            kind = None

        self.kind = kind

        # Support the legacy positional signature
        # CheckValve(p_upstream, p_downstream, delta_open, d_eq)
        if args:
            if len(args) > 4:
                raise TypeError(
                    "CheckValve() accepts at most four positional arguments: "
                    "p_upstream, p_downstream, delta_open, d_eq"
                )

            pos_p_upstream = args[0] if len(args) > 0 else None
            pos_p_downstream = args[1] if len(args) > 1 else None
            pos_delta = args[2] if len(args) > 2 else None
            pos_d_eq = args[3] if len(args) > 3 else None

            if p_upstream is None:
                p_upstream = pos_p_upstream
            if p_downstream is None:
                p_downstream = pos_p_downstream
            if delta_open_min is None and delta_open is None:
                delta_open = pos_delta
            if d_eq is None and d_eff is None:
                d_eq = pos_d_eq

        defaults: Mapping[str, float] | None = None
        if delta_open_min is None and delta_open is None:
            defaults = _check_valve_defaults()
            delta_open_min = defaults["delta_open_pa"]
        if d_eq is None and d_eff is None:
            defaults = defaults or _check_valve_defaults()
            d_eq = defaults["equivalent_diameter_m"]

        self.delta_open_min = self._coerce_positive(
            delta_open_min if delta_open_min is not None else delta_open,
            "delta_open_min",
        )
        self.d_eq = self._coerce_positive(d_eq if d_eq is not None else d_eff, "d_eq")
        self.hyst = float(hyst)
        if self.hyst < 0:
            raise ModelConfigError(f"Hysteresis must be non-negative, got {self.hyst}")

        self._p_upstream = float(p_upstream) if p_upstream is not None else None
        self._p_downstream = float(p_downstream) if p_downstream is not None else None
        self._is_open = False

    @staticmethod
    def _coerce_positive(value: float | None, name: str) -> float:
        if value is None:
            raise ModelConfigError(f"Missing required parameter '{name}'")
        value = float(value)
        if value <= 0:
            raise ModelConfigError(f"{name} must be positive, got {value}")
        return value

    def set_pressures(self, p_upstream: float, p_downstream: float) -> None:
        """Persist the most recent pressures used for valve evaluation."""

        self._p_upstream = float(p_upstream)
        self._p_downstream = float(p_downstream)

    def is_open(
        self,
        p_upstream: float | None = None,
        p_downstream: float | None = None,
    ) -> bool:
        """Return the valve open state for the supplied pressures.

        The method supports both stateless and stateful usage: callers can pass
        pressures on every invocation or rely on the values provided during
        construction/previous evaluations.
        """

        if (p_upstream is None) ^ (p_downstream is None):
            raise ValueError("Both upstream and downstream pressures must be provided")
        if p_upstream is not None and p_downstream is not None:
            self.set_pressures(p_upstream, p_downstream)

        if self._p_upstream is None or self._p_downstream is None:
            raise ValueError("Valve pressures have not been initialised")

        delta_p = self._p_upstream - self._p_downstream
        open_threshold = self.delta_open_min
        close_threshold = self._closing_threshold(open_threshold)

        if self.kind is None:
            # Generic valve – directional behaviour is handled by the pressure
            # differential itself.
            return self._apply_hysteresis(delta_p, open_threshold, close_threshold)

        if self.kind == CheckValveKind.ATMO_TO_LINE:
            if delta_p < 0:
                self._is_open = False
                return False
            return self._apply_hysteresis(delta_p, open_threshold, close_threshold)

        if self.kind == CheckValveKind.LINE_TO_TANK:
            if delta_p < 0:
                self._is_open = False
                return False
            return self._apply_hysteresis(delta_p, open_threshold, close_threshold)

        # Fallback for future kinds – treat as closed.
        self._is_open = False
        return False

    def _closing_threshold(self, open_threshold: float) -> float:
        """Возвращает перепад давления, необходимый для закрытия клапана.

        Полевые измерения пневматического коллектора стабилизатора показали,
        что клапаны начинают дребезжать, если порог закрытия слишком близок к
        порогу открытия. Даже при заданной гистерезисе аппаратные допуски
        формируют примерно 25% "dead-band". Модель теперь принудительно
        обеспечивает этот минимальный запас для согласования поведения
        симуляции с физической системой.

        См. отчет калибровки: CAL-2025-01.
        """

        if self.hyst <= 0:
            return open_threshold

        hysteresis_band = max(self.hyst, open_threshold * 0.25)
        return max(open_threshold - hysteresis_band, 0.0)

    def _apply_hysteresis(
        self, delta_p: float, open_threshold: float, close_threshold: float
    ) -> bool:
        """Apply hysteresis rules to determine valve state."""

        if delta_p >= open_threshold:
            self._is_open = True
        elif delta_p <= close_threshold:
            self._is_open = False
        return self._is_open

    def validate_invariants(self) -> ValidationResult:
        """Validate valve configuration and return a structured report."""

        errors: list[str] = []
        warnings: list[str] = []

        try:
            # Trigger validation by re-running the coercion helpers.
            self._coerce_positive(self.delta_open_min, "delta_open_min")
            self._coerce_positive(self.d_eq, "d_eq")
            if self.hyst < 0:
                raise ModelConfigError("Hysteresis must be non-negative")
        except ModelConfigError as exc:
            errors.append(str(exc))

        if self.delta_open_min > 50_000:
            warnings.append(f"Very high opening pressure: {self.delta_open_min} Pa")
        if self.d_eq > 0.1:
            warnings.append(f"Very large equivalent diameter: {self.d_eq} m")

        return {
            "is_valid": not errors,
            "errors": errors,
            "warnings": warnings,
        }


class ReliefValve:
    """Pressure relief valve with throttling and hysteresis."""

    __slots__ = (
        "kind",
        "p_set",
        "hyst",
        "d_eq",
        "_p_tank",
        "_is_open",
    )

    def __init__(
        self,
        kind: ReliefValveKind | None = None,
        *,
        p_tank: float | None = None,
        p_set: float | None = None,
        p_setpoint: float | None = None,
        hyst: float | None = None,
        hysteresis: float | None = None,
        d_eq: float | None = None,
        throttle_coeff: float | None = None,
    ) -> None:
        self.kind = kind or ReliefValveKind.STIFFNESS
        self.p_set = self._coerce_positive(
            p_set if p_set is not None else p_setpoint, "p_set"
        )

        hyst_value = hyst if hyst is not None else hysteresis
        self.hyst = float(hyst_value) if hyst_value is not None else 0.0
        if self.hyst < 0:
            raise ModelConfigError(f"Hysteresis must be non-negative, got {self.hyst}")

        d_value = d_eq if d_eq is not None else throttle_coeff
        if d_value is None and self.kind != ReliefValveKind.SAFETY:
            orifices = _relief_orifice_defaults()
            if self.kind == ReliefValveKind.MIN_PRESS:
                d_value = orifices["min"]
            else:
                d_value = orifices["stiff"]
        if self.kind == ReliefValveKind.SAFETY:
            if d_value not in (None, 0.0):
                raise ModelConfigError(
                    "SAFETY relief valves must not have throttling (d_eq should be None)"
                )
            self.d_eq = None
        else:
            self.d_eq = self._coerce_positive(d_value, "d_eq")

        self._p_tank = float(p_tank) if p_tank is not None else None
        self._is_open = False

    @staticmethod
    def _coerce_positive(value: float | None, name: str) -> float:
        if value is None:
            raise ModelConfigError(f"Missing required parameter '{name}'")
        value = float(value)
        if value <= 0:
            raise ModelConfigError(f"{name} must be positive, got {value}")
        return value

    def update_pressure(self, p_tank: float) -> bool:
        """Update the stored tank pressure and return the current open state."""

        self._p_tank = float(p_tank)
        return self.is_open()

    def is_open(self, p_tank: float | None = None) -> bool:
        """Evaluate whether the relief valve is open for the given pressure."""

        if p_tank is not None:
            self._p_tank = float(p_tank)

        if self._p_tank is None:
            raise ValueError("Tank pressure has not been initialised")

        if self.kind == ReliefValveKind.MIN_PRESS:
            open_threshold = self.p_set - self.hyst
            close_threshold = self.p_set
            if self._p_tank <= open_threshold:
                self._is_open = True
            elif self._p_tank >= close_threshold:
                self._is_open = False
            return self._is_open

        # STIFFNESS and SAFETY share the same hysteresis rules (open on high
        # pressure, close when pressure falls sufficiently).
        open_threshold = self.p_set + self.hyst
        close_threshold = self.p_set
        if self._p_tank >= open_threshold:
            self._is_open = True
        elif self._p_tank <= close_threshold:
            self._is_open = False
        return self._is_open

    def calculate_flow(self, throttle_coeff: float | None = None) -> float:
        """Return a simplified relief flow estimate.

        The flow calculation is intentionally lightweight – it mirrors the
        behaviour relied upon by the tests which only check for qualitative
        differences between throttled and unrestricted valves.
        """

        if not self.is_open():
            return 0.0

        coeff = throttle_coeff
        if coeff is None:
            coeff = self.d_eq if self.d_eq is not None else 1.0

        if coeff <= 0:
            return 0.0

        if self.kind == ReliefValveKind.MIN_PRESS:
            delta_p = max(0.0, self.p_set - self._p_tank)
        else:
            delta_p = max(0.0, self._p_tank - self.p_set)

        return coeff * delta_p

    def validate_invariants(self) -> ValidationResult:
        """Validate configuration and return a structured report."""

        errors: list[str] = []
        warnings: list[str] = []

        try:
            self._coerce_positive(self.p_set, "p_set")
            if self.hyst < 0:
                raise ModelConfigError("Hysteresis must be non-negative")
            if self.kind == ReliefValveKind.SAFETY:
                if self.d_eq not in (None, 0.0):
                    raise ModelConfigError(
                        "SAFETY relief valves must not have throttling (d_eq should be None)"
                    )
            elif self.d_eq is None or self.d_eq <= 0:
                raise ModelConfigError(
                    f"{self.kind} relief valves must have positive d_eq"
                )
        except ModelConfigError as exc:
            errors.append(str(exc))

        if self.p_set > 2_000_000:
            warnings.append(f"Very high set pressure: {self.p_set} Pa")
        if self.hyst > self.p_set * 0.1:
            warnings.append(
                f"Large hysteresis relative to set pressure: {self.hyst}/{self.p_set}"
            )

        return {
            "is_valid": not errors,
            "errors": errors,
            "warnings": warnings,
        }
