"""Simulation service implementations backed by training presets."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from typing import Any

from src.core.interfaces import SettingsOrchestrator, SimulationService
from src.infrastructure.container import (
    ServiceContainer,
    ServiceToken,
    get_default_container,
)
from src.simulation.presets import (
    TrainingPreset,
    TrainingPresetLibrary,
    get_default_training_library,
)


class TrainingPresetService(SimulationService):
    """Coordinate preset management with a :class:`SettingsOrchestrator`."""

    def __init__(
        self,
        *,
        orchestrator: SettingsOrchestrator,
        library: TrainingPresetLibrary | None = None,
        tolerance: float = 1e-9,
    ) -> None:
        self._orchestrator = orchestrator
        self._library = library or get_default_training_library()
        self._tolerance = tolerance
        self._active_id = self._resolve_active_id()
        self._callbacks: set[Callable[[str], None]] = set()
        self._unsubscribe = self._orchestrator.register_listener(
            self._handle_settings_event
        )

    # ------------------------------------------------------------------ helpers
    def _handle_settings_event(self, _payload: Mapping[str, Any]) -> None:
        self._refresh_active_id()

    def _refresh_active_id(self) -> None:
        new_id = self._resolve_active_id()
        if new_id == self._active_id:
            return
        self._active_id = new_id
        for callback in list(self._callbacks):
            callback(new_id)

    def _resolve_active_id(self) -> str:
        snapshot = self._orchestrator.snapshot(
            ["current.simulation", "current.pneumatic"]
        )
        payload = {
            "simulation": snapshot.get("current.simulation", {}),
            "pneumatic": snapshot.get("current.pneumatic", {}),
        }
        return self._library.resolve_active_id(payload, tolerance=self._tolerance)

    def _build_updates(self, preset: TrainingPreset) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        for key, value in preset.simulation.items():
            updates[f"current.simulation.{key}"] = float(value)
        for key, value in preset.pneumatic.items():
            updates[f"current.pneumatic.{key}"] = deepcopy(value)
        return updates

    # ----------------------------------------------------------------- protocol
    def list_presets(self) -> Sequence[Mapping[str, Any]]:
        return tuple(self._library.describe_presets())

    def describe_preset(self, preset_id: str) -> Mapping[str, Any]:
        preset = self._library.get(preset_id)
        if preset is None:
            return {}
        return preset.to_qml_payload()

    def apply_preset(
        self, preset_id: str, *, auto_save: bool = True
    ) -> Mapping[str, Any]:
        preset = self._library.get(preset_id)
        if preset is None:
            raise KeyError(f"Unknown training preset '{preset_id}'")
        updates = self._build_updates(preset)
        result = self._orchestrator.apply_updates(updates, auto_save=auto_save)
        self._refresh_active_id()
        return result

    def active_preset_id(self) -> str:
        return self._active_id

    def register_active_observer(
        self, callback: Callable[[str], None]
    ) -> Callable[[], None]:
        self._callbacks.add(callback)
        callback(self._active_id)

        def _unsubscribe() -> None:
            self._callbacks.discard(callback)

        return _unsubscribe

    # ---------------------------------------------------------------- lifecycle
    def close(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None
        self._callbacks.clear()


__all__ = ["TrainingPresetService"]


SIMULATION_SERVICE_TOKEN = ServiceToken[SimulationService](
    "simulation.training_presets",
    "Training preset coordinator bound to the settings orchestrator",
)


def get_simulation_service(
    container: ServiceContainer | None = None,
) -> SimulationService:
    """Resolve the shared simulation service from the container."""

    target = container or get_default_container()
    return target.resolve(SIMULATION_SERVICE_TOKEN)


__all__.extend(["SIMULATION_SERVICE_TOKEN", "get_simulation_service"])
