"""Concrete implementation of :class:`~src.core.interfaces.SettingsOrchestrator`."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from typing import Any, Dict, Optional

from src.common import settings_manager as sm

from .interfaces import SettingsOrchestrator as SettingsOrchestratorProtocol


class SettingsOrchestrator(SettingsOrchestratorProtocol):
    """Bridge between :class:`SettingsManager` and service abstractions."""

    def __init__(
        self,
        *,
        settings_manager: sm.SettingsManager | None = None,
        event_bus: sm.SettingsEventBus | None = None,
    ) -> None:
        self._manager = settings_manager or sm.get_settings_manager()
        self._event_bus = event_bus or sm.get_settings_event_bus()
        self._callbacks: set[Callable[[Mapping[str, Any]], None]] = set()
        self._listener_handles: list[Callable[[], None]] = []
        if self._event_bus is not None:
            self._install_event_listeners()

    # ------------------------------------------------------------------ helpers
    def _install_event_listeners(self) -> None:
        assert self._event_bus is not None  # nosec - guarded by caller

        def _forward(payload: dict[str, Any]) -> None:
            for callback in list(self._callbacks):
                callback(dict(payload))

        self._event_bus.settingChanged.connect(_forward)
        self._event_bus.settingsBatchUpdated.connect(_forward)

        def _disconnect() -> None:
            if self._event_bus is None:
                return
            try:
                self._event_bus.settingChanged.disconnect(_forward)
            except (TypeError, RuntimeError):  # pragma: no cover - PySide quirks
                pass
            try:
                self._event_bus.settingsBatchUpdated.disconnect(_forward)
            except (TypeError, RuntimeError):  # pragma: no cover - PySide quirks
                pass

        self._listener_handles.append(_disconnect)

    # ----------------------------------------------------------------- protocol
    def snapshot(self, paths: Sequence[str]) -> Mapping[str, Any]:
        payload: dict[str, Any] = {}
        for path in paths:
            payload[path] = self._manager.get(path, {})
        return payload

    def apply_updates(
        self, updates: Mapping[str, Any], *, auto_save: bool = True
    ) -> Mapping[str, Any]:
        if not updates:
            return {}

        for path, value in updates.items():
            self._manager.set(path, value, auto_save=False)

        if auto_save:
            self._manager.save()
        else:
            self._manager.save_if_dirty()

        return {key: deepcopy(value) for key, value in updates.items()}

    def register_listener(
        self, callback: Callable[[Mapping[str, Any]], None]
    ) -> Callable[[], None]:
        self._callbacks.add(callback)

        def _unsubscribe() -> None:
            self._callbacks.discard(callback)

        return _unsubscribe

    # ---------------------------------------------------------------- lifecycle
    def close(self) -> None:
        for handle in self._listener_handles:
            handle()
        self._listener_handles.clear()
        self._callbacks.clear()


__all__ = ["SettingsOrchestrator"]
