"""Test doubles for external components interacting with the simulator."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable

from src.core.interfaces import SettingsOrchestrator as SettingsOrchestratorProtocol
from src.runtime.sync import LatestOnlyQueue


class FakeSettingsOrchestrator(SettingsOrchestratorProtocol):
    """In-memory implementation of :class:`SettingsOrchestrator` for tests."""

    def __init__(self, initial_state: Mapping[str, Any] | None = None) -> None:
        self._state: Dict[str, Any] = {}
        if initial_state:
            self._merge_state(self._state, initial_state)
        self._listeners: set[Callable[[Mapping[str, Any]], None]] = set()

    # ------------------------------------------------------------------ protocol
    def snapshot(self, paths: Sequence[str]) -> Mapping[str, Any]:
        payload: Dict[str, Any] = {}
        for path in paths:
            payload[path] = deepcopy(self._lookup(path))
        return payload

    def apply_updates(
        self, updates: Mapping[str, Any], *, auto_save: bool = True
    ) -> Mapping[str, Any]:  # noqa: ARG002 - parity with protocol
        if not updates:
            return {}
        materialised: Dict[str, Any] = {}
        for path, value in updates.items():
            self._assign(path, value)
            materialised[path] = deepcopy(value)
        self._notify_listeners(materialised)
        return materialised

    def register_listener(
        self, callback: Callable[[Mapping[str, Any]], None]
    ) -> Callable[[], None]:
        self._listeners.add(callback)

        def _unsubscribe() -> None:
            self._listeners.discard(callback)

        return _unsubscribe

    # --------------------------------------------------------------- test helpers
    def inject_external_change(self, updates: Mapping[str, Any]) -> Mapping[str, Any]:
        """Simulate an update that originates outside of the service under test."""

        applied: Dict[str, Any] = {}
        for path, value in updates.items():
            self._assign(path, value)
            applied[path] = deepcopy(value)
        self._notify_listeners(applied)
        return applied

    # ------------------------------------------------------------------ internals
    def _notify_listeners(self, payload: Mapping[str, Any]) -> None:
        if not payload:
            return
        for callback in list(self._listeners):
            callback(dict(payload))

    def _assign(self, dotted_path: str, value: Any) -> None:
        target = self._state
        parts = [part for part in dotted_path.split(".") if part]
        if not parts:
            raise ValueError("Empty dotted path")
        *parents, leaf = parts
        for key in parents:
            bucket = target.setdefault(key, {})
            if not isinstance(bucket, dict):
                raise TypeError(f"Path '{key}' already occupied by non-dict value")
            target = bucket
        target[leaf] = deepcopy(value)

    def _lookup(self, dotted_path: str) -> Any:
        target: Any = self._state
        for key in [part for part in dotted_path.split(".") if part]:
            if not isinstance(target, dict) or key not in target:
                return {}
            target = target[key]
        return target

    def _merge_state(self, target: Dict[str, Any], payload: Mapping[str, Any]) -> None:
        for key, value in payload.items():
            if isinstance(value, Mapping):
                bucket = target.setdefault(key, {})
                if not isinstance(bucket, dict):
                    raise TypeError(f"Cannot merge mapping into scalar at '{key}'")
                self._merge_state(bucket, value)
            else:
                target[key] = deepcopy(value)


@dataclass
class FakeEcuGateway:
    """Collect simulation states delivered to the electronic control unit."""

    queue: LatestOnlyQueue = field(default_factory=LatestOnlyQueue)
    received: list[Any] = field(default_factory=list)

    def publish_state(self, snapshot: Any) -> None:
        """Push a new state update produced by the simulation loop."""

        self.queue.put_nowait(snapshot)

    def poll(self) -> Any | None:
        """Retrieve the latest state update, mirroring ECU polling semantics."""

        payload = self.queue.get_nowait()
        if payload is not None:
            self.received.append(payload)
        return payload

    def statistics(self) -> Mapping[str, float]:
        """Expose queue statistics for assertions in contract tests."""

        return self.queue.get_stats()


class FakeVisualizationClient:
    """Subscribe to :class:`SceneBridge` signals and store payloads."""

    def __init__(self) -> None:
        self.events: list[tuple[str, Dict[str, Any]]] = []
        self._connections: list[Callable[[], None]] = []

    def bind(self, bridge: Any) -> None:
        """Connect to all category signals exposed by the bridge."""

        signal_names: Iterable[str] = (
            "geometryChanged",
            "cameraChanged",
            "lightingChanged",
            "environmentChanged",
            "sceneChanged",
            "qualityChanged",
            "materialsChanged",
            "effectsChanged",
            "animationChanged",
            "threeDChanged",
            "renderChanged",
            "simulationChanged",
            "updatesDispatched",
        )
        for name in signal_names:
            signal = getattr(bridge, name, None)
            if signal is None:
                continue

            def _capture(payload: Any, *, _name: str = name) -> None:
                if isinstance(payload, Mapping):
                    self.events.append((_name, dict(payload)))
                else:
                    self.events.append((_name, {"value": payload}))

            signal.connect(_capture)  # type: ignore[call-arg]
            self._connections.append(lambda s=signal, h=_capture: s.disconnect(h))

    def dispose(self) -> None:
        for disconnect in self._connections:
            try:
                disconnect()
            except Exception:
                pass
        self._connections.clear()
