"""Shared catalogue of training scenarios referenced by presets and tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioDescriptor:
    """Describe a training scenario used across tests and runtime metadata."""

    id: str
    label: str
    difficulty: str
    summary: str
    metrics: tuple[str, ...]


SCENARIO_INDEX: dict[str, ScenarioDescriptor] = {
    "flat-track": ScenarioDescriptor(
        id="flat-track",
        label="Ровная дорога",
        difficulty="beginner",
        summary="Базовый сценарий без внешних возмущений.",
        metrics=("stabilizer_error_rmse", "pressure_delta_peak"),
    ),
    "rough-step": ScenarioDescriptor(
        id="rough-step",
        label="Ступенчатая нагрузка",
        difficulty="advanced",
        summary="Неровности с резкими ступеньками для теста устойчивости.",
        metrics=("overshoot_percent", "settling_time"),
    ),
    "workshop-loop": ScenarioDescriptor(
        id="workshop-loop",
        label="Лабораторный цикл",
        difficulty="intermediate",
        summary="Повторяющийся профиль для быстрой отладки контроллеров.",
        metrics=("cycle_time", "cpu_load"),
    ),
    "endurance-run": ScenarioDescriptor(
        id="endurance-run",
        label="Выносливость",
        difficulty="advanced",
        summary="Длительный маршрут с переменной скоростью и температурой.",
        metrics=("stability_index", "thermal_drift", "energy_consumption"),
    ),
    "pneumo-diagnostics": ScenarioDescriptor(
        id="pneumo-diagnostics",
        label="Диагностика пневмосистемы",
        difficulty="intermediate",
        summary="Шаблон для проверки герметичности, откликов клапанов и ресивера.",
        metrics=(
            "line_pressure_balance",
            "valve_switch_latency",
            "receiver_recovery_time",
        ),
    ),
    "road-matrix": ScenarioDescriptor(
        id="road-matrix",
        label="Матрица дорожных профилей",
        difficulty="advanced",
        summary="Чередование булыжного асфальта, стыков и стиральной доски для стресс-тестов.",
        metrics=(
            "road_profile_coverage",
            "unsprung_energy_peak",
            "ride_frequency_response",
        ),
    ),
    "visual-diagnostics": ScenarioDescriptor(
        id="visual-diagnostics",
        label="Визуальная калибровка",
        difficulty="beginner",
        summary="Статические позы и эталонные источники света для настройки графики и индикаторов.",
        metrics=(
            "telemetry_signal_latency",
            "indicator_refresh_rate",
            "frame_time_budget",
        ),
    ),
}


__all__ = ["ScenarioDescriptor", "SCENARIO_INDEX"]
