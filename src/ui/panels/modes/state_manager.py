"""
ModesPanel state manager
Управление состоянием панели режимов симуляции
"""

from typing import Any
import copy

from src.common.settings_manager import SettingsManager, get_settings_manager

from .defaults import (
    DEFAULT_MODES_PARAMS,
    DEFAULT_PHYSICS_OPTIONS,
    MODE_PRESETS,
    get_animation_params,
)


class ModesStateManager:
    """Менеджер состояния панели режимов"""

    def __init__(self, settings_manager: SettingsManager | None = None):
        """Инициализация с дефолтными значениями и загрузкой из SettingsManager"""

        self.settings_manager = settings_manager or get_settings_manager()
        self.parameters: dict[str, Any] = {}
        self.physics_options: dict[str, Any] = {}
        self._current_preset: int = 0  # Standard preset

        self._load_from_settings()

    # ===============================================================
    # Loading / persistence
    # ===============================================================

    def _load_from_settings(self) -> None:
        """Load state from SettingsManager with defaults as fallback."""

        defaults = copy.deepcopy(DEFAULT_MODES_PARAMS)
        physics_defaults = copy.deepcopy(DEFAULT_PHYSICS_OPTIONS)

        stored = self.settings_manager.get_category("modes", {}) or {}
        self.parameters = {**defaults, **{k: v for k, v in stored.items() if k != "physics"}}
        self.physics_options = {**physics_defaults, **stored.get("physics", {})}

        preset_name = str(self.parameters.get("mode_preset", ""))
        self._current_preset = self._resolve_preset_index(preset_name)

    def _persist(self, *, auto_save: bool = True) -> None:
        """Persist current state back to SettingsManager."""

        if not self.settings_manager:
            return

        payload = self._merge_state()
        self.settings_manager.set_category("modes", payload, auto_save=auto_save)

        ambient_c = payload.get("ambient_temperature_c")
        if ambient_c is not None:
            pneumatic = self.settings_manager.get_category("pneumatic", {}) or {}
            pneumatic["atmo_temp"] = float(ambient_c)
            self.settings_manager.set_category("pneumatic", pneumatic, auto_save=auto_save)

    def get_parameters(self) -> dict[str, Any]:
        """Получить копию параметров"""
        return copy.deepcopy(self.parameters)

    def get_physics_options(self) -> dict[str, Any]:
        """Получить копию опций физики"""
        return copy.deepcopy(self.physics_options)

    def update_parameter(self, name: str, value: Any) -> None:
        """Обновить параметр БЕЗ валидации (валидация только при проверке)

        Note: Мы сохраняем значение как есть, чтобы пользователь мог увидеть
        ошибку при вызове validate_state(). Это позволяет показать предупреждение
        вместо молчаливой коррекции.
        """
        self.parameters[name] = value
        self._persist(auto_save=True)

    def update_physics_option(self, name: str, value: Any) -> None:
        """Обновить опцию физики"""
        if name not in self.physics_options:
            return
        default_value = DEFAULT_PHYSICS_OPTIONS.get(name)
        if isinstance(default_value, bool):
            self.physics_options[name] = bool(value)
        elif isinstance(default_value, (int, float)):
            try:
                self.physics_options[name] = float(value)
            except (TypeError, ValueError):
                self.physics_options[name] = float(default_value)
        else:
            self.physics_options[name] = value
        self._persist(auto_save=True)

    def apply_preset(self, preset_index: int) -> dict[str, Any]:
        """Применить пресет и вернуть обновлённые параметры"""
        if preset_index not in MODE_PRESETS:
            preset_index = 0

        preset = MODE_PRESETS[preset_index]

        # Skip custom preset
        if preset.get("custom"):
            self._current_preset = preset_index
            return {}

        # Update simulation type
        if "sim_type" in preset:
            self.parameters["sim_type"] = preset["sim_type"]

        # Update thermo mode
        if "thermo_mode" in preset:
            self.parameters["thermo_mode"] = preset["thermo_mode"]

        # Update physics options
        for key in DEFAULT_PHYSICS_OPTIONS.keys():
            if key in preset:
                self.physics_options[key] = preset[key]

        self._current_preset = preset_index
        self.parameters["mode_preset"] = preset["name"]

        self._persist(auto_save=True)

        return {
            "sim_type": self.parameters.get("sim_type"),
            "thermo_mode": self.parameters.get("thermo_mode"),
            "physics_options": self.get_physics_options(),
        }

    def get_current_preset_index(self) -> int:
        """Получить индекс текущего пресета"""
        return self._current_preset

    def switch_to_custom_preset(self) -> None:
        """Переключить на пользовательский пресет при ручном изменении"""
        if self._current_preset != 4:
            self._current_preset = 4
            self.parameters["mode_preset"] = MODE_PRESETS[4]["name"]
            self._persist(auto_save=True)

    def validate_state(self) -> list[str]:
        """Валидация состояния

        Returns:
            Список сообщений об ошибках (пустой если всё ок)
        """
        errors = []

        # Проверка типа симуляции
        sim_type = self.parameters.get("sim_type")
        if sim_type not in ["KINEMATICS", "DYNAMICS"]:
            errors.append(f"Неверный тип симуляции: {sim_type}")

        # Проверка термо-режима
        thermo_mode = self.parameters.get("thermo_mode")
        if thermo_mode not in ["ISOTHERMAL", "ADIABATIC"]:
            errors.append(f"Неверный термо-режим: {thermo_mode}")

        # Проверка амплитуды
        amplitude = self.parameters.get("amplitude", 0.0)
        if not (0.0 <= amplitude <= 0.2):
            errors.append(f"Амплитуда вне диапазона: {amplitude} (должна быть 0-0.2 м)")

        # Проверка частоты
        frequency = self.parameters.get("frequency", 1.0)
        if not (0.1 <= frequency <= 10.0):
            errors.append(f"Частота вне диапазона: {frequency} (должна быть 0.1-10 Гц)")

        # Проверка фаз (0-360°)
        for phase_key in ["phase", "lf_phase", "rf_phase", "lr_phase", "rr_phase"]:
            phase = self.parameters.get(phase_key, 0.0)
            if not (0.0 <= phase <= 360.0):
                errors.append(
                    f"Фаза {phase_key} вне диапазона: {phase}° (должна быть 0-360°)"
                )

        duration_ms = self.parameters.get("smoothing_duration_ms", 120.0)
        if not (0.0 <= float(duration_ms) <= 600.0):
            errors.append(f"Время сглаживания вне диапазона: {duration_ms} мс (0-600)")

        snap_deg = self.parameters.get("smoothing_angle_snap_deg", 65.0)
        if not (0.0 <= float(snap_deg) <= 180.0):
            errors.append(f"Порог снапинга угла вне диапазона: {snap_deg}° (0-180°)")

        snap_m = self.parameters.get("smoothing_piston_snap_m", 0.05)
        if not (0.0 <= float(snap_m) <= 0.3):
            errors.append(f"Порог снапинга поршня вне диапазона: {snap_m} м (0-0.3)")

        return errors

    def get_animation_parameters(self) -> dict[str, Any]:
        """Получить параметры анимации для передачи в QML"""
        return get_animation_params(self.parameters)

    # ===============================================================
    # Persistence helpers
    # ===============================================================

    def _resolve_preset_index(self, preset_name: str) -> int:
        """Resolve preset index from stored name or identifier."""

        if not preset_name:
            return 0

        normalized = preset_name.lower()
        if normalized in {"standard", "стандартный"}:
            return 0
        if normalized in {"custom", "пользовательский"}:
            return 4
        for idx, preset in MODE_PRESETS.items():
            name = str(preset.get("name", "")).lower()
            if normalized == name or normalized == str(preset.get("id", "")).lower():
                return idx
        return 0

    def check_dependencies(self, param_name: str, value: Any) -> dict[str, Any]:
        """Проверка зависимостей между параметрами

        Returns:
            Словарь с предупреждениями/подсказками
        """
        warnings = {}

        # Если выбрана кинематика, пневматика может быть неактуальна
        if param_name == "sim_type" and value == "KINEMATICS":
            if self.physics_options.get("include_pneumatics"):
                warnings["pneumatics"] = (
                    "В режиме кинематики пневматическая система не учитывается "
                    "даже если опция включена"
                )

        # Если отключены все компоненты в динамике
        if param_name == "sim_type" and value == "DYNAMICS":
            bool_flags = [
                bool(self.physics_options.get(key, False))
                for key in ("include_springs", "include_dampers", "include_pneumatics")
            ]
            if not any(bool_flags):
                warnings["physics"] = (
                    "В режиме динамики рекомендуется включить хотя бы один "
                    "физический компонент"
                )

        # Высокая амплитуда + высокая частота
        if param_name == "amplitude" and value > 0.1:
            freq = self.parameters.get("frequency", 1.0)
            if freq > 5.0:
                warnings["resonance"] = (
                    f"Высокая амплитуда ({value:.3f}м) при высокой частоте "
                    f"({freq:.1f}Гц) может вызвать резонанс"
                )

        return warnings

    def reset_to_defaults(self) -> None:
        """Сброс к дефолтным значениям"""
        self.parameters = copy.deepcopy(DEFAULT_MODES_PARAMS)
        self.physics_options = copy.deepcopy(DEFAULT_PHYSICS_OPTIONS)
        self._current_preset = 0
        self._persist()

    def to_dict(self) -> dict[str, Any]:
        """Сериализация состояния в словарь"""
        return {
            "parameters": self.get_parameters(),
            "physics_options": self.get_physics_options(),
            "preset_index": self._current_preset,
        }

    def from_dict(self, state: dict[str, Any]) -> None:
        """Десериализация состояния из словаря"""
        if "parameters" in state:
            self.parameters.update(state["parameters"])
        if "physics_options" in state:
            self.physics_options.update(state["physics_options"])
        if "preset_index" in state:
            self._current_preset = state["preset_index"]

    def _merge_state(self) -> dict[str, Any]:
        """Return combined settings payload for SettingsManager."""

        payload = copy.deepcopy(self.parameters)
        payload["physics"] = copy.deepcopy(self.physics_options)
        return payload

    def as_settings_payload(self) -> dict[str, Any]:
        """Публичная версия объединённых настроек"""

        return self._merge_state()

    def persist_state(self) -> None:
        """Public entrypoint to persist the current state."""

        self._persist()
