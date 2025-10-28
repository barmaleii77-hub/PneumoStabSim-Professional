# -*- coding: utf-8 -*-
"""State manager for the pneumatic panel."""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any, Dict, Iterable, Optional, Tuple

from src.common.settings_manager import SettingsManager, get_settings_manager

from .defaults import (
    DEFAULT_PNEUMATIC,
    PRESSURE_DROP_LIMITS,
    RELIEF_PRESSURE_LIMITS,
    STORAGE_DIAMETER_KEYS_MM,
    STORAGE_PRESSURE_KEYS,
    THROTTLE_DIAMETER_LIMITS,
    VALVE_DIAMETER_LIMITS,
    clamp,
    MM_PER_M,
    convert_pressure_value,
    get_pressure_factor,
)

LOGGER = logging.getLogger(__name__)


class PneumoStateManager:
    """Manage pneumatic state, validation and persistence."""

    def __init__(
        self,
        settings_manager: Optional[SettingsManager] = None,
    ) -> None:
        self._settings = settings_manager or get_settings_manager()
        self._state: Dict[str, Any] = deepcopy(DEFAULT_PNEUMATIC)
        self._defaults: Dict[str, Any] = deepcopy(DEFAULT_PNEUMATIC)
        self._load_from_settings()

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _convert_from_storage(payload: Dict[str, Any]) -> Dict[str, Any]:
        converted = deepcopy(payload)
        units = str(
            converted.get("pressure_units", DEFAULT_PNEUMATIC["pressure_units"])
        )
        factor = get_pressure_factor(units)
        if factor <= 0:
            units = DEFAULT_PNEUMATIC["pressure_units"]
            factor = get_pressure_factor(units)
        converted["pressure_units"] = units
        for key in STORAGE_PRESSURE_KEYS:
            if key in converted:
                try:
                    value_pa = float(converted[key])
                except (TypeError, ValueError):
                    continue
                converted[key] = convert_pressure_value(value_pa, "Па", units)
        for key in STORAGE_DIAMETER_KEYS_MM:
            if key in converted:
                value = float(converted[key])
                if value <= 0.0:
                    converted[key] = value
                elif value >= 0.1:
                    converted[key] = value
                else:
                    converted[key] = value * MM_PER_M
        return converted

    @staticmethod
    def _convert_to_storage(payload: Dict[str, Any]) -> Dict[str, Any]:
        converted = deepcopy(payload)
        units = str(
            converted.get("pressure_units", DEFAULT_PNEUMATIC["pressure_units"])
        )
        factor = get_pressure_factor(units)
        if factor <= 0:
            units = DEFAULT_PNEUMATIC["pressure_units"]
            factor = get_pressure_factor(units)
            converted["pressure_units"] = units
        else:
            converted["pressure_units"] = units
        for key in STORAGE_PRESSURE_KEYS:
            if key in converted:
                try:
                    converted[key] = convert_pressure_value(
                        float(converted[key]), units, "Па"
                    )
                except (TypeError, ValueError):
                    continue
        for key in STORAGE_DIAMETER_KEYS_MM:
            if key in converted:
                converted[key] = float(converted[key]) / MM_PER_M
        return converted

    @staticmethod
    def _pressure_limit_bounds(
        limits: Dict[str, float], units: str
    ) -> tuple[float, float]:
        base_units = DEFAULT_PNEUMATIC["pressure_units"]
        minimum = convert_pressure_value(limits["min"], base_units, units)
        maximum = convert_pressure_value(limits["max"], base_units, units)
        if minimum > maximum:
            minimum, maximum = maximum, minimum
        return minimum, maximum

    def export_storage_payload(self) -> Dict[str, Any]:
        """Return a snapshot ready to persist in settings storage."""

        return self._convert_to_storage(self._state)

    def _load_from_settings(self) -> None:
        try:
            current = self._settings.get("current.pneumatic", {}) or {}
            defaults = self._settings.get("defaults_snapshot.pneumatic", {}) or {}
        except Exception as exc:  # pragma: no cover - defensive path
            LOGGER.warning("Failed to load pneumatic settings", exc_info=exc)
            current, defaults = {}, {}

        if isinstance(defaults, dict):
            defaults.pop("link_rod_dia", None)
        if defaults:
            self._defaults.update(self._convert_from_storage(defaults))
        if isinstance(current, dict):
            current.pop("link_rod_dia", None)
        merged = deepcopy(self._defaults)
        merged.update(self._convert_from_storage(current))
        self._state = merged

    # ------------------------------------------------------------------- access
    def get_state(self) -> Dict[str, Any]:
        return deepcopy(self._state)

    def get_parameter(self, name: str, default: Any = None) -> Any:
        return self._state.get(name, default)

    def set_parameter(self, name: str, value: Any) -> None:
        self._state[name] = value

    # Receiver -----------------------------------------------------------
    def get_volume_mode(self) -> str:
        return str(self._state.get("volume_mode", "MANUAL"))

    def set_volume_mode(self, mode: str) -> None:
        self._state["volume_mode"] = mode

    def get_manual_volume(self) -> float:
        return float(self._state.get("receiver_volume", 0.0))

    def set_manual_volume(self, volume: float) -> None:
        limits = self.get_volume_limits()
        clamped = clamp(volume, limits["min_m3"], limits["max_m3"])
        self._state["receiver_volume"] = clamped

    def get_volume_limits(self) -> Dict[str, float]:
        return deepcopy(
            self._state.get(
                "receiver_volume_limits", DEFAULT_PNEUMATIC["receiver_volume_limits"]
            )
        )

    def get_receiver_diameter(self) -> float:
        return float(
            self._state.get("receiver_diameter", DEFAULT_PNEUMATIC["receiver_diameter"])
        )

    def set_receiver_diameter(self, diameter_m: float) -> float:
        from .defaults import RECEIVER_DIAMETER_LIMITS

        clamped = clamp(
            diameter_m, RECEIVER_DIAMETER_LIMITS["min"], RECEIVER_DIAMETER_LIMITS["max"]
        )
        self._state["receiver_diameter"] = clamped
        return self._recompute_volume_if_needed()

    def get_receiver_length(self) -> float:
        return float(
            self._state.get("receiver_length", DEFAULT_PNEUMATIC["receiver_length"])
        )

    def set_receiver_length(self, length_m: float) -> float:
        from .defaults import RECEIVER_LENGTH_LIMITS

        clamped = clamp(
            length_m, RECEIVER_LENGTH_LIMITS["min"], RECEIVER_LENGTH_LIMITS["max"]
        )
        self._state["receiver_length"] = clamped
        return self._recompute_volume_if_needed()

    def _recompute_volume_if_needed(self) -> float:
        if self.get_volume_mode() != "GEOMETRIC":
            return float(self._state.get("receiver_volume", 0.0))
        volume = self.calculate_geometric_volume(
            self.get_receiver_diameter(), self.get_receiver_length()
        )
        self._state["receiver_volume"] = volume
        return volume

    def refresh_geometric_volume(self) -> float:
        """Recompute receiver volume when geometric mode is active."""

        return self._recompute_volume_if_needed()

    @staticmethod
    def calculate_geometric_volume(diameter_m: float, length_m: float) -> float:
        import math

        radius = diameter_m / 2.0
        return math.pi * radius * radius * length_m

    # Pressures ---------------------------------------------------------
    def get_pressure_drop(self, name: str) -> float:
        return float(self._state.get(name, DEFAULT_PNEUMATIC.get(name, 0.0)))

    def set_pressure_drop(self, name: str, value_bar: float) -> None:
        units = self.get_pressure_units()
        minimum, maximum = self._pressure_limit_bounds(PRESSURE_DROP_LIMITS, units)
        value = clamp(value_bar, minimum, maximum)
        self._state[name] = value

    def get_relief_pressure(self, name: str) -> float:
        return float(self._state.get(name, DEFAULT_PNEUMATIC.get(name, 0.0)))

    def set_relief_pressure(self, name: str, value_bar: float) -> None:
        units = self.get_pressure_units()
        minimum, maximum = self._pressure_limit_bounds(RELIEF_PRESSURE_LIMITS, units)
        value = clamp(value_bar, minimum, maximum)
        self._state[name] = value

    # Diameters ---------------------------------------------------------
    def get_valve_diameter(self, name: str) -> float:
        return float(self._state.get(name, DEFAULT_PNEUMATIC.get(name, 0.0)))

    def set_valve_diameter(self, name: str, value_mm: float) -> None:
        value = clamp(
            value_mm, VALVE_DIAMETER_LIMITS["min"], VALVE_DIAMETER_LIMITS["max"]
        )
        self._state[name] = value

    def set_throttle_diameter(self, name: str, value_mm: float) -> None:
        value = clamp(
            value_mm, THROTTLE_DIAMETER_LIMITS["min"], THROTTLE_DIAMETER_LIMITS["max"]
        )
        self._state[name] = value

    # Options -----------------------------------------------------------
    def get_option(self, name: str) -> bool:
        return bool(self._state.get(name, DEFAULT_PNEUMATIC.get(name, False)))

    def set_option(self, name: str, value: bool) -> None:
        self._state[name] = bool(value)

    def get_pressure_units(self) -> str:
        return str(
            self._state.get("pressure_units", DEFAULT_PNEUMATIC["pressure_units"])
        )

    def set_pressure_units(self, units: str) -> None:
        new_units = str(units)
        old_units = self.get_pressure_units()
        if new_units == old_units:
            return

        new_factor = get_pressure_factor(new_units)
        if new_factor <= 0:
            return

        def _convert_pressure_payload(payload: Dict[str, Any]) -> None:
            payload_units = str(
                payload.get("pressure_units", DEFAULT_PNEUMATIC["pressure_units"])
            )
            payload_factor = get_pressure_factor(payload_units)
            if payload_factor <= 0:
                payload_factor = get_pressure_factor(
                    DEFAULT_PNEUMATIC["pressure_units"]
                )
                payload_units = DEFAULT_PNEUMATIC["pressure_units"]

            for key in STORAGE_PRESSURE_KEYS:
                if key not in payload:
                    continue
                try:
                    value = float(payload[key])
                except (TypeError, ValueError):
                    continue
                value_pa = convert_pressure_value(value, payload_units, "Па")
                payload[key] = convert_pressure_value(value_pa, "Па", new_units)

            payload["pressure_units"] = new_units

        _convert_pressure_payload(self._state)
        _convert_pressure_payload(self._defaults)

    def get_thermo_mode(self) -> str:
        return str(self._state.get("thermo_mode", DEFAULT_PNEUMATIC["thermo_mode"]))

    def set_thermo_mode(self, mode: str) -> None:
        self._state["thermo_mode"] = mode

    def get_atmo_temp(self) -> float:
        return float(self._state.get("atmo_temp", DEFAULT_PNEUMATIC["atmo_temp"]))

    def set_atmo_temp(self, temp_c: float) -> None:
        self._state["atmo_temp"] = temp_c

    # Validation --------------------------------------------------------
    def validate_pneumatic(self) -> Tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []

        volume = float(self._state.get("receiver_volume", 0.0))
        limits = self.get_volume_limits()
        if self.get_volume_mode() == "MANUAL":
            if not (limits["min_m3"] <= volume <= limits["max_m3"]):
                errors.append(
                    "Объём ресивера (ручной) должен быть в диапазоне"
                    f" {limits['min_m3']}..{limits['max_m3']} м³"
                )
        else:
            diameter = self.get_receiver_diameter()
            length = self.get_receiver_length()
            if diameter <= 0 or length <= 0:
                errors.append("Геометрические параметры ресивера должны быть > 0")

        p_min = self.get_relief_pressure("relief_min_pressure")
        p_stiff = self.get_relief_pressure("relief_stiff_pressure")
        p_safe = self.get_relief_pressure("relief_safety_pressure")
        if p_min and p_stiff and p_min >= p_stiff:
            errors.append("Мин. сброс должен быть меньше давления сброса жёсткости")
        if p_stiff and p_safe and p_stiff >= p_safe:
            errors.append("Давление сброса жёсткости должно быть меньше аварийного")

        throttle_min = self.get_valve_diameter("throttle_min_dia")
        throttle_stiff = self.get_valve_diameter("throttle_stiff_dia")
        if throttle_min and (throttle_min < 0.2 or throttle_min > 10):
            warnings.append("Диаметр минимального дросселя вне диапазона 0.2..10 мм")
        if throttle_stiff and (throttle_stiff < 0.2 or throttle_stiff > 10):
            warnings.append("Диаметр дросселя жёсткости вне диапазона 0.2..10 мм")

        dp_atmo = self.get_pressure_drop("cv_atmo_dp")
        dp_tank = self.get_pressure_drop("cv_tank_dp")
        if dp_atmo < 0 or dp_tank < 0:
            errors.append("ΔP для обратных клапанов не может быть отрицательной")

        return errors, warnings

    # Persistence -------------------------------------------------------
    def reset_to_defaults(self) -> None:
        self._state = deepcopy(self._defaults)

    def save_current_as_defaults(self) -> None:
        payload = self._convert_to_storage(self._state)
        self._settings.set("defaults_snapshot.pneumatic", payload)

    def save_state(self) -> None:
        payload = self._convert_to_storage(self._state)
        self._settings.set("current.pneumatic", payload)

    # Utilities ---------------------------------------------------------
    def update_from(self, updates: Dict[str, Any]) -> None:
        for key, value in updates.items():
            self._state[key] = value

    def update_many(self, pairs: Iterable[Tuple[str, Any]]) -> None:
        for key, value in pairs:
            self._state[key] = value
