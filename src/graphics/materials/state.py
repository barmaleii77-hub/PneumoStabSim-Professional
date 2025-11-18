"""Runtime helpers for applying and rolling back material updates."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from collections.abc import Mapping

from src.common.settings_manager import SettingsManager, get_settings_manager


class MaterialStateStore:
    """Maintain current and previous material states with rollback support."""

    _CURRENT_PATH = "current.graphics.materials"
    _PREVIOUS_PATH = "current.graphics.materials_previous"

    def __init__(self, settings_manager: SettingsManager | None = None) -> None:
        self._settings_manager = settings_manager or self._safe_manager()
        self._current_state = self._read_from_settings(self._CURRENT_PATH)
        previous = self._read_from_settings(self._PREVIOUS_PATH)
        self._previous_state = previous if previous else deepcopy(self._current_state)

    @property
    def current_state(self) -> dict[str, Any]:
        return deepcopy(self._current_state)

    @property
    def previous_state(self) -> dict[str, Any]:
        return deepcopy(self._previous_state)

    def apply_updates(
        self, payload: Mapping[str, Any] | None, *, auto_save: bool = False
    ) -> dict[str, Any]:
        normalized = self._normalise_payload(payload)
        self._previous_state = deepcopy(self._current_state)
        self._current_state = self._merge_materials(self._current_state, normalized)
        if auto_save:
            self._persist()
        return self.current_state

    def rollback(self, *, auto_save: bool = False) -> dict[str, Any]:
        if not self._previous_state:
            return self.current_state
        self._current_state = deepcopy(self._previous_state)
        if auto_save:
            self._persist()
        return self.current_state

    def refresh_from_settings(self) -> dict[str, Any]:
        self._current_state = self._read_from_settings(self._CURRENT_PATH)
        previous = self._read_from_settings(self._PREVIOUS_PATH)
        self._previous_state = previous if previous else deepcopy(self._current_state)
        return self.current_state

    def _persist(self) -> None:
        if self._settings_manager is None:
            return
        self._settings_manager.set(
            self._PREVIOUS_PATH, self._previous_state, auto_save=False
        )
        self._settings_manager.set(
            self._CURRENT_PATH, self._current_state, auto_save=True
        )

    def _read_from_settings(self, path: str) -> dict[str, Any]:
        if self._settings_manager is None:
            return {}
        try:
            data = self._settings_manager.get(path, {})
        except Exception:
            return {}
        if isinstance(data, Mapping):
            return {key: deepcopy(value) for key, value in data.items()}
        return {}

    @staticmethod
    def _normalise_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
        if isinstance(payload, Mapping):
            return {key: deepcopy(value) for key, value in payload.items()}
        return {}

    @staticmethod
    def _merge_materials(
        base: Mapping[str, Any] | None, update: Mapping[str, Any]
    ) -> dict[str, Any]:
        merged: dict[str, Any] = {
            key: deepcopy(value)
            for key, value in (base.items() if isinstance(base, Mapping) else [])
        }
        for material_id, payload in update.items():
            if not isinstance(payload, Mapping):
                continue
            existing = (
                merged.get(material_id, {})
                if isinstance(merged.get(material_id), Mapping)
                else {}
            )
            next_state = {key: deepcopy(value) for key, value in existing.items()}
            for field, value in payload.items():
                next_state[field] = deepcopy(value)
            merged[material_id] = next_state
        return merged

    @staticmethod
    def _safe_manager() -> SettingsManager | None:
        try:
            return get_settings_manager()
        except Exception:
            return None
