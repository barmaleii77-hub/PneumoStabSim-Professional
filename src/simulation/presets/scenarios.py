"""Shared catalogue of training scenarios referenced by presets and tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class ScenarioDescriptor:
    """Describe a training scenario used across tests and runtime metadata."""

    id: str
    label: str
    difficulty: str
    summary: str
    metrics: Tuple[str, ...]


SCENARIO_INDEX: Dict[str, ScenarioDescriptor] = {
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
}


__all__ = ["ScenarioDescriptor", "SCENARIO_INDEX"]
