"""JSON-backed graphics state manager aligned with SettingsManager usage."""

from __future__ import annotations

import copy
import logging
from typing import Any, Optional

from src.common.settings_manager import SettingsManager, get_settings_manager


class GraphicsStateManager:
    """Persist graphics panel settings via the shared SettingsManager.

    The legacy implementation relied on QSettings which conflicted with the
    repository-wide decision to keep all runtime configuration in
    ``config/app_settings.json``.  This helper now forwards all reads and writes
    to the singleton :class:`SettingsManager` instance while keeping a small
    in-memory cache for panels to reuse.
    """

    STATE_KEYS = {
        "lighting",
        "environment",
        "quality",
        "camera",
        "materials",
        "effects",
    }

    def __init__(self, settings_manager: SettingsManager | None = None) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self._settings = settings_manager or get_settings_manager()
        self._state_cache: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _validate_category(category: str) -> None:
        if category not in GraphicsStateManager.STATE_KEYS:
            raise ValueError(f"Unknown graphics category: {category}")

    def _settings_path(self, category: str) -> str:
        return f"graphics.{category}"

    @staticmethod
    def _clone(payload: dict[str, Any] | None) -> dict[str, Any] | None:
        if payload is None:
            return None
        return copy.deepcopy(payload)

    # ----------------------------------------------------------------- public API
    def save_state(self, category: str, state: dict[str, Any]) -> None:
        """Store a category inside ``config/app_settings.json`` without auto-save."""
        self._validate_category(category)
        payload = self._clone(state) or {}
        self._state_cache[category] = payload
        try:
            self._settings.set(self._settings_path(category), payload, auto_save=False)
        except Exception as exc:
            self.logger.error("Failed to persist %s state: %s", category, exc)

    def load_state(self, category: str) -> dict[str, Any] | None:
        """Retrieve a category payload, falling back to cached data if available."""
        self._validate_category(category)

        if category in self._state_cache:
            return self._clone(self._state_cache[category])

        try:
            payload = self._settings.get(self._settings_path(category), default=None)
        except Exception as exc:
            self.logger.error("Failed to load %s state: %s", category, exc)
            return None

        if payload is None:
            return None

        if not isinstance(payload, dict):
            self.logger.warning(
                "Ignoring non-dict payload for %s: %r", category, payload
            )
            return None

        self._state_cache[category] = copy.deepcopy(payload)
        return self._clone(payload)

    def save_all(self, full_state: dict[str, dict[str, Any]]) -> None:
        """Persist every graphics category and flush once at the end."""
        for category, payload in full_state.items():
            try:
                self.save_state(category, payload)
            except ValueError:
                self.logger.debug(
                    "Skipping unknown category %s during save_all", category
                )
        try:
            self._settings.save()
            self.logger.info(
                "Saved %d graphics categories to config/app_settings.json",
                len(full_state),
            )
        except Exception as exc:
            self.logger.error("Failed to write graphics settings to disk: %s", exc)

    def load_all(self) -> dict[str, dict[str, Any]]:
        """Return a dictionary containing all known graphics categories."""
        result: dict[str, dict[str, Any]] = {}
        for category in sorted(self.STATE_KEYS):
            payload = self.load_state(category)
            if payload is not None:
                result[category] = payload
        return result

    def reset_category(self, category: str) -> None:
        """Reset a category to the defaults snapshot maintained by SettingsManager."""
        self._validate_category(category)
        try:
            defaults = self._settings.get(f"defaults_snapshot.graphics.{category}", {})
            self._settings.set(self._settings_path(category), defaults, auto_save=False)
            self._state_cache.pop(category, None)
        except Exception as exc:
            self.logger.error("Failed to reset %s to defaults: %s", category, exc)

    def reset_all(self) -> None:
        """Restore the entire graphics section from defaults."""
        try:
            self._settings.reset_to_defaults(category="graphics", auto_save=False)
            self._state_cache.clear()
            self._settings.save()
        except Exception as exc:
            self.logger.error("Failed to reset graphics settings: %s", exc)

    # ---------------------------------------------------------------- validation
    def _validate_state(self, category: str, state: dict[str, Any]) -> dict[str, Any]:
        """Placeholder validation hook retained for backward compatibility."""
        # The refactored panel performs validation per control; we keep this method
        # to avoid breaking callers that expect it to exist.
        return copy.deepcopy(state)
