"""
ModesPanel defaults and presets
Значения по умолчанию и предустановки панели режимов симуляции
"""

from typing import Dict, Any

# ===============================================================
# DEFAULT VALUES
# ===============================================================

DEFAULT_MODES_PARAMS: dict[str, Any] = {
    # Simulation modes
    "sim_type": "KINEMATICS",
    "thermo_mode": "ISOTHERMAL",
    "mode_preset": "standard",
    # Road excitation
    "amplitude": 0.05,  # m
    "frequency": 1.0,  # Hz
    "phase": 0.0,  # degrees
    "lf_phase": 0.0,  # degrees (Left Front)
    "rf_phase": 0.0,  # degrees (Right Front)
    "lr_phase": 0.0,  # degrees (Left Rear)
    "rr_phase": 0.0,  # degrees (Right Rear)
    # Animation smoothing
    "smoothing_enabled": True,
    "smoothing_duration_ms": 120.0,
    "smoothing_angle_snap_deg": 65.0,
    "smoothing_piston_snap_m": 0.05,
    "smoothing_easing": "OutCubic",
}

DEFAULT_PHYSICS_OPTIONS: dict[str, Any] = {
    "include_springs": True,
    "include_dampers": True,
    "include_pneumatics": True,
    "spring_constant": 50_000.0,
    "damper_coefficient": 2_000.0,
    "lever_inertia_multiplier": 1.0,
}

# ===============================================================
# MODE PRESETS
# ===============================================================

MODE_PRESETS: dict[int, dict[str, Any]] = {
    0: {  # Стандартный
        "name": "Стандартный",
        "sim_type": "KINEMATICS",
        "thermo_mode": "ISOTHERMAL",
        "include_springs": True,
        "include_dampers": True,
        "include_pneumatics": True,
        "spring_constant": 50_000.0,
        "damper_coefficient": 2_000.0,
        "lever_inertia_multiplier": 1.0,
        "description": "Базовый режим с кинематикой и всеми компонентами",
    },
    1: {  # Только кинематика
        "name": "Только кинематика",
        "sim_type": "KINEMATICS",
        "thermo_mode": "ISOTHERMAL",
        "include_springs": False,
        "include_dampers": False,
        "include_pneumatics": False,
        "spring_constant": 50_000.0,
        "damper_coefficient": 2_000.0,
        "lever_inertia_multiplier": 1.0,
        "description": "Чистая геометрическая кинематика без физики",
    },
    2: {  # Полная динамика
        "name": "Полная динамика",
        "sim_type": "DYNAMICS",
        "thermo_mode": "ADIABATIC",
        "include_springs": True,
        "include_dampers": True,
        "include_pneumatics": True,
        "spring_constant": 55_000.0,
        "damper_coefficient": 2_200.0,
        "lever_inertia_multiplier": 1.1,
        "description": "Полная динамическая модель с адиабатической пневматикой",
    },
    3: {  # Тест пневматики
        "name": "Тест пневматики",
        "sim_type": "DYNAMICS",
        "thermo_mode": "ISOTHERMAL",
        "include_springs": False,
        "include_dampers": False,
        "include_pneumatics": True,
        "spring_constant": 50_000.0,
        "damper_coefficient": 2_000.0,
        "lever_inertia_multiplier": 1.0,
        "description": "Изолированный тест пневматической системы",
    },
    4: {  # Пользовательский
        "name": "Пользовательский",
        "custom": True,
        "description": "Ручная настройка всех параметров",
    },
}

PRESET_NAMES = [preset["name"] for preset in MODE_PRESETS.values()]

# ===============================================================
# PARAMETER RANGES
# ===============================================================

PARAMETER_RANGES: dict[str, dict[str, float]] = {
    "amplitude": {
        "min": 0.0,
        "max": 0.2,
        "step": 0.001,
        "decimals": 3,
        "default": 0.05,
        "unit": "м",
    },
    "frequency": {
        "min": 0.1,
        "max": 10.0,
        "step": 0.1,
        "decimals": 1,
        "default": 1.0,
        "unit": "Гц",
    },
    "phase": {
        "min": 0.0,
        "max": 360.0,
        "step": 15.0,
        "decimals": 0,
        "default": 0.0,
        "unit": "°",
    },
    "wheel_phase": {  # Per-wheel phase offsets
        "min": 0.0,
        "max": 360.0,
        "step": 15.0,
        "decimals": 0,
        "default": 0.0,
        "unit": "°",
    },
    "smoothing_duration_ms": {
        "min": 0.0,
        "max": 600.0,
        "step": 10.0,
        "decimals": 0,
        "default": 120.0,
        "unit": "мс",
    },
    "smoothing_angle_snap_deg": {
        "min": 0.0,
        "max": 180.0,
        "step": 5.0,
        "decimals": 0,
        "default": 65.0,
        "unit": "°",
    },
    "smoothing_piston_snap_m": {
        "min": 0.0,
        "max": 0.3,
        "step": 0.005,
        "decimals": 3,
        "default": 0.05,
        "unit": "м",
    },
}

# ===============================================================
# SIMULATION TYPES
# ===============================================================

SIMULATION_TYPES = {"KINEMATICS": "Кинематика", "DYNAMICS": "Динамика"}

THERMO_MODES = {"ISOTHERMAL": "Изотермический", "ADIABATIC": "Адиабатический"}

# ===============================================================
# WHEEL LABELS
# ===============================================================

WHEEL_LABELS = {
    "lf": "ЛП",  # Left Front
    "rf": "ПП",  # Right Front
    "lr": "ЛЗ",  # Left Rear
    "rr": "ПЗ",  # Right Rear
}

WHEEL_NAMES = {
    "lf": "Левое переднее",
    "rf": "Правое переднее",
    "lr": "Левое заднее",
    "rr": "Правое заднее",
}

# ===============================================================
# HELPER FUNCTIONS
# ===============================================================


def get_preset(preset_index: int) -> dict[str, Any]:
    """Получить пресет по индексу"""
    return MODE_PRESETS.get(preset_index, MODE_PRESETS[4])


def validate_parameter(param_name: str, value: float) -> float:
    """Валидация параметра по диапазону"""
    if param_name in PARAMETER_RANGES:
        ranges = PARAMETER_RANGES[param_name]
        return max(ranges["min"], min(ranges["max"], value))
    return value


def get_animation_params(parameters: dict[str, Any]) -> dict[str, Any]:
    """Извлечь параметры анимации из общего словаря"""
    return {
        "amplitude": parameters.get("amplitude", 0.05),
        "frequency": parameters.get("frequency", 1.0),
        "phase": parameters.get("phase", 0.0),
        "lf_phase": parameters.get("lf_phase", 0.0),
        "rf_phase": parameters.get("rf_phase", 0.0),
        "lr_phase": parameters.get("lr_phase", 0.0),
        "rr_phase": parameters.get("rr_phase", 0.0),
        "smoothing_enabled": parameters.get("smoothing_enabled", True),
        "smoothing_duration_ms": parameters.get("smoothing_duration_ms", 120.0),
        "smoothing_angle_snap_deg": parameters.get("smoothing_angle_snap_deg", 65.0),
        "smoothing_piston_snap_m": parameters.get("smoothing_piston_snap_m", 0.05),
        "smoothing_easing": parameters.get("smoothing_easing", "OutCubic"),
    }
