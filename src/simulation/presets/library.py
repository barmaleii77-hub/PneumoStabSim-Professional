"""Declarative catalogue of training presets for the simulator."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import math
from typing import TYPE_CHECKING, Any
from collections.abc import Iterable, Mapping, Sequence

from .metadata import TrainingPresetMetadata
from .scenarios import SCENARIO_INDEX

if TYPE_CHECKING:  # pragma: no cover - import only for typing
    from src.common.settings_manager import SettingsManager

Number = float | int


def _normalise_numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _build_metadata(
    *,
    scenario_id: str,
    difficulty: str,
    duration_minutes: int,
    learning_objectives: Iterable[str] | None = None,
    recommended_modules: Iterable[str] | None = None,
    evaluation_metrics: Iterable[str] | None = None,
    notes: str = "",
) -> TrainingPresetMetadata:
    descriptor = SCENARIO_INDEX.get(scenario_id)
    metrics_source: Iterable[str] | None = evaluation_metrics
    if metrics_source is None and descriptor is not None:
        metrics_source = descriptor.metrics

    return TrainingPresetMetadata(
        difficulty=difficulty,
        duration_minutes=duration_minutes,
        learning_objectives=TrainingPresetMetadata.coerce_iterable(learning_objectives),
        recommended_modules=TrainingPresetMetadata.coerce_iterable(recommended_modules),
        evaluation_metrics=TrainingPresetMetadata.coerce_iterable(metrics_source),
        scenario_id=scenario_id,
        scenario_label=descriptor.label if descriptor else "",
        scenario_summary=descriptor.summary if descriptor else "",
        notes=notes,
    )


@dataclass(frozen=True)
class TrainingPreset:
    """Preset describing simulation and pneumatic defaults for training."""

    id: str
    label: str
    description: str
    simulation: Mapping[str, Number]
    pneumatic: Mapping[str, Any] = field(default_factory=dict)
    metadata: TrainingPresetMetadata = field(
        default_factory=lambda: TrainingPresetMetadata(
            difficulty="unspecified",
            duration_minutes=0,
        )
    )
    tags: tuple[str, ...] = field(default_factory=tuple)
    revision: str = "2025.1"

    def to_qml_payload(self) -> dict[str, Any]:
        """Return a serialisable description consumed by QML."""

        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "tags": list(self.tags),
            "revision": self.revision,
            "simulation": {key: float(value) for key, value in self.simulation.items()},
            "pneumatic": deepcopy(dict(self.pneumatic)),
            "metadata": self.metadata.to_payload(),
        }

    def to_summary(self) -> dict[str, Any]:
        """Compact summary for logs and diagnostics."""

        return {
            "id": self.id,
            "simulation": dict(self.simulation),
            "pneumatic": dict(self.pneumatic),
            "metadata": self.metadata.to_payload(),
        }

    def matches_settings(
        self,
        settings: Mapping[str, Any],
        *,
        tolerance: float = 1e-9,
    ) -> bool:
        """Return ``True`` if the mapping contains the preset values."""

        if not settings:
            return False

        simulation_values = settings.get("simulation")
        if not isinstance(simulation_values, Mapping):
            return False
        for key, expected in self.simulation.items():
            actual = _normalise_numeric(simulation_values.get(key))
            expected_number = _normalise_numeric(expected)
            if expected_number is None or actual is None:
                return False
            if not math.isclose(
                actual, expected_number, rel_tol=1e-6, abs_tol=tolerance
            ):
                return False

        pneumatic_values = settings.get("pneumatic")
        if isinstance(pneumatic_values, Mapping):
            for key, expected in self.pneumatic.items():
                actual = pneumatic_values.get(key)
                if isinstance(expected, bool):
                    if bool(actual) != expected:
                        return False
                    continue
                if isinstance(expected, (int, float)):
                    actual_number = _normalise_numeric(actual)
                    expected_number = _normalise_numeric(expected)
                    if actual_number is None or expected_number is None:
                        return False
                    if not math.isclose(
                        actual_number,
                        expected_number,
                        rel_tol=1e-6,
                        abs_tol=tolerance,
                    ):
                        return False
                else:
                    if str(actual).strip().upper() != str(expected).strip().upper():
                        return False
        elif self.pneumatic:
            return False
        return True

    def apply(
        self,
        manager: SettingsManager,
        *,
        auto_save: bool = True,
    ) -> dict[str, Any]:
        """Apply the preset to the provided settings manager."""

        updated_paths: dict[str, Any] = {}
        for key, value in self.simulation.items():
            path = f"current.simulation.{key}"
            manager.set(path, float(value), auto_save=False)
            updated_paths[path] = float(value)
        for key, value in self.pneumatic.items():
            path = f"current.pneumatic.{key}"
            manager.set(path, deepcopy(value), auto_save=False)
            updated_paths[path] = deepcopy(value)

        if auto_save:
            manager.save()
        else:
            manager.save_if_dirty()
        return updated_paths


class TrainingPresetLibrary:
    """Repository of presets backed by an ordered catalogue."""

    def __init__(self, presets: Sequence[TrainingPreset] | None = None) -> None:
        catalogue = list(presets or [])
        if not catalogue:
            catalogue = list(DEFAULT_PRESETS)
        self._presets: tuple[TrainingPreset, ...] = tuple(catalogue)
        self._index: dict[str, TrainingPreset] = {
            preset.id: preset for preset in catalogue
        }

    def list_presets(self) -> tuple[TrainingPreset, ...]:
        return self._presets

    def describe_presets(self) -> list[dict[str, Any]]:
        return [preset.to_qml_payload() for preset in self._presets]

    def get(self, preset_id: str) -> TrainingPreset | None:
        return self._index.get(preset_id)

    def resolve_active_id(
        self,
        settings: Mapping[str, Any] | None,
        *,
        tolerance: float = 1e-9,
    ) -> str:
        if not settings:
            return ""
        for preset in self._presets:
            if preset.matches_settings(settings, tolerance=tolerance):
                return preset.id
        return ""

    def apply(
        self,
        manager: SettingsManager,
        preset_id: str,
        *,
        auto_save: bool = True,
    ) -> dict[str, Any]:
        preset = self.get(preset_id)
        if preset is None:
            raise KeyError(f"Unknown training preset '{preset_id}'")
        return preset.apply(manager, auto_save=auto_save)

    def to_summary(self) -> list[dict[str, Any]]:
        return [preset.to_summary() for preset in self._presets]


DEFAULT_PRESETS: tuple[TrainingPreset, ...] = (
    TrainingPreset(
        id="baseline",
        label="Базовый запуск",
        description="Стартовые параметры из конфигурации приложения.",
        simulation={
            "physics_dt": 0.001,
            "render_vsync_hz": 60.0,
            "max_steps_per_frame": 10,
            "max_frame_time": 0.05,
        },
        pneumatic={
            "volume_mode": "MANUAL",
            "thermo_mode": "ISOTHERMAL",
            "master_isolation_open": False,
            "receiver_volume": 0.02,
        },
        metadata=_build_metadata(
            scenario_id="flat-track",
            difficulty="beginner",
            duration_minutes=20,
            learning_objectives=(
                "Ознакомление с интерфейсом стабилизатора",
                "Проверка корректности датчиков и базовой кинематики",
            ),
            recommended_modules=("safety/overview", "setup/calibration"),
            evaluation_metrics=("stabilizer_error_rmse", "pressure_delta_peak"),
            notes="Использует штатный сценарий ровной дороги.",
        ),
        tags=("baseline", "intro"),
    ),
    TrainingPreset(
        id="precision_mode",
        label="Высокая точность",
        description="Уменьшенный шаг интегрирования для динамических испытаний.",
        simulation={
            "physics_dt": 0.0005,
            "render_vsync_hz": 60.0,
            "max_steps_per_frame": 12,
            "max_frame_time": 0.04,
        },
        pneumatic={
            "volume_mode": "GEOMETRIC",
            "thermo_mode": "ADIABATIC",
            "master_isolation_open": True,
            "receiver_volume": 0.018,
        },
        metadata=_build_metadata(
            scenario_id="rough-step",
            difficulty="advanced",
            duration_minutes=35,
            learning_objectives=(
                "Работа с быстро меняющимися внешними возмущениями",
                "Оценка влияния моделей газа на устойчивость",
            ),
            recommended_modules=("pneumatics/advanced", "control/stability"),
            evaluation_metrics=("overshoot_percent", "settling_time"),
            notes="Сценарий ступенчатых ударов по неровной дороге.",
        ),
        tags=("precision", "research"),
    ),
    TrainingPreset(
        id="rapid_iteration",
        label="Быстрая настройка",
        description="Ослабленные требования для ускоренной отладки алгоритмов.",
        simulation={
            "physics_dt": 0.002,
            "render_vsync_hz": 75.0,
            "max_steps_per_frame": 6,
            "max_frame_time": 0.033,
        },
        pneumatic={
            "volume_mode": "MANUAL",
            "thermo_mode": "ISOTHERMAL",
            "master_isolation_open": False,
            "receiver_volume": 0.02,
        },
        metadata=_build_metadata(
            scenario_id="workshop-loop",
            difficulty="intermediate",
            duration_minutes=15,
            learning_objectives=(
                "Быстрые циклы настройки ПИД-регуляторов",
                "Контроль стабильности на упрощённой модели",
            ),
            recommended_modules=("control/pid", "diagnostics/logging"),
            evaluation_metrics=("cycle_time", "cpu_load"),
            notes="Петлевой тестовый профиль с повторяемыми нагрузками.",
        ),
        tags=("iteration", "lab"),
    ),
    TrainingPreset(
        id="endurance_validation",
        label="Тест выносливости",
        description="Длительная сессия для проверки тепловой стабильности и энергопотребления.",
        simulation={
            "physics_dt": 0.001,
            "render_vsync_hz": 50.0,
            "max_steps_per_frame": 14,
            "max_frame_time": 0.06,
        },
        pneumatic={
            "volume_mode": "GEOMETRIC",
            "thermo_mode": "ADIABATIC",
            "master_isolation_open": True,
            "receiver_volume": 0.022,
        },
        metadata=_build_metadata(
            scenario_id="endurance-run",
            difficulty="advanced",
            duration_minutes=45,
            learning_objectives=(
                "Анализ поведения системы при длительных нагрузках",
                "Отработка стратегии охлаждения и энергосбережения",
            ),
            recommended_modules=("control/energy", "pneumatics/thermal"),
            notes="Сценарий с прогревом узлов и контролем ресурсных ограничений.",
        ),
        tags=("endurance", "thermal", "research"),
    ),
    TrainingPreset(
        id="pneumo_diagnostics",
        label="Диагностика пневмосистемы",
        description="Конфигурация для проверки клапанов, герметичности и реакции ресивера.",
        simulation={
            "physics_dt": 0.0008,
            "render_vsync_hz": 60.0,
            "max_steps_per_frame": 10,
            "max_frame_time": 0.05,
        },
        pneumatic={
            "volume_mode": "GEOMETRIC",
            "thermo_mode": "ISOTHERMAL",
            "master_isolation_open": True,
            "receiver_volume": 0.019,
        },
        metadata=_build_metadata(
            scenario_id="pneumo-diagnostics",
            difficulty="intermediate",
            duration_minutes=25,
            learning_objectives=(
                "Диагностика утечек и дрейфа давления",
                "Визуализация открытия атмосферных и ресиверных клапанов",
            ),
            recommended_modules=("pneumatics/monitoring", "diagnostics/telemetry"),
            evaluation_metrics=(
                "line_pressure_balance",
                "valve_switch_latency",
                "receiver_recovery_time",
            ),
            notes="Использует FlowNetwork для визуализации состояний клапанов и стрелок потока.",
        ),
        tags=("pneumo", "valves", "diagnostics"),
    ),
    TrainingPreset(
        id="road_response_matrix",
        label="Матрица дорожных профилей",
        description="Серия дорожных профилей для сравнения моделей демпфирования и подвески.",
        simulation={
            "physics_dt": 0.0007,
            "render_vsync_hz": 72.0,
            "max_steps_per_frame": 12,
            "max_frame_time": 0.045,
        },
        pneumatic={
            "volume_mode": "MANUAL",
            "thermo_mode": "ADIABATIC",
            "master_isolation_open": False,
            "receiver_volume": 0.021,
        },
        metadata=_build_metadata(
            scenario_id="road-matrix",
            difficulty="advanced",
            duration_minutes=30,
            learning_objectives=(
                "Сравнение road-моделей и профилей возмущений",
                "Оценка устойчивости контроллера на скачкообразных и периодических неровностях",
            ),
            recommended_modules=("roadmodels/library", "control/stability"),
            evaluation_metrics=(
                "road_profile_coverage",
                "unsprung_energy_peak",
                "ride_frequency_response",
            ),
            notes="Включает переключение профилей через TrainingPanel и запись телеметрии в реальном времени.",
        ),
        tags=("road", "profiles", "analysis"),
    ),
    TrainingPreset(
        id="visual_diagnostics_suite",
        label="Визуальная калибровка",
        description="Статичная поза подвески и эталонное освещение для настройки графики и HUD.",
        simulation={
            "physics_dt": 0.001,
            "render_vsync_hz": 90.0,
            "max_steps_per_frame": 8,
            "max_frame_time": 0.033,
        },
        pneumatic={
            "volume_mode": "MANUAL",
            "thermo_mode": "ISOTHERMAL",
            "master_isolation_open": False,
            "receiver_volume": 0.02,
        },
        metadata=_build_metadata(
            scenario_id="visual-diagnostics",
            difficulty="beginner",
            duration_minutes=10,
            learning_objectives=(
                "Настройка шкалы камеры и индикаторов SceneBridge",
                "Проверка панелей телеметрии и трассировки сигналов",
            ),
            recommended_modules=("ui/visual", "graphics/tuning"),
            evaluation_metrics=(
                "telemetry_signal_latency",
                "indicator_refresh_rate",
                "frame_time_budget",
            ),
            notes="Использует TelemetryChartPanel и CameraStateHud для визуальной валидации настроек.",
        ),
        tags=("visual", "hud", "graphics"),
    ),
)


def get_default_training_library() -> TrainingPresetLibrary:
    """Return a library populated with built-in presets."""

    return TrainingPresetLibrary(DEFAULT_PRESETS)
