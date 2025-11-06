"""Utilities for validating and persisting graphics panel settings.

The refactored graphics panel expects a rich configuration structure with seven
independent graphics categories (lighting, environment, quality, camera, materials,
effects and scene) plus the top-level ``current.animation`` container.  Historical
versions of :mod:`config/app_settings.json` only expose a
subset of these categories, so loading them directly would trigger run-time
exceptions inside :class:`GraphicsPanel`.  The goal of this module is to bridge
that gap:

* hydrate missing categories from the canonical baseline payload under
  ``config/baseline/app_settings.json``;
* guarantee that every required material dictionary is present and flag
  unsupported keys explicitly;
* provide explicit validation helpers so the panel can fail fast instead of
  masking exceptions deep inside Qt signal handlers; and
* centralise persistence logic for both the ``current`` and
  ``defaults_snapshot`` sections managed by :class:`SettingsManager`.

By funnelling all read/write operations through this service we make the panel
resilient to configuration drift while keeping the validation rules easy to
exercise in unit tests.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, Optional

from src.common.settings_manager import SettingsManager, get_settings_manager


class GraphicsSettingsError(RuntimeError):
    """Raised when the graphics configuration is invalid."""


def _deep_copy(payload: Any) -> Any:
    """Return a JSON-based deep copy to avoid accidental mutations."""

    return json.loads(json.dumps(payload))


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries without modifying the inputs."""

    result: Dict[str, Any] = {key: _deep_copy(value) for key, value in base.items()}

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = _deep_copy(value)

    return result


class GraphicsSettingsService:
    """Validate and persist the graphics configuration for the panel."""

    GRAPHICS_CATEGORIES: tuple[str, ...] = (
        "lighting",
        "environment",
        "quality",
        "camera",
        "materials",
        "effects",
        "scene",
    )
    ANIMATION_CATEGORY: str = "animation"
    REQUIRED_CATEGORIES: tuple[str, ...] = GRAPHICS_CATEGORIES + (ANIMATION_CATEGORY,)

    REQUIRED_MATERIAL_KEYS: tuple[str, ...] = (
        "frame",
        "lever",
        "tail_rod",
        "cylinder",
        "piston_body",
        "piston_rod",
        "joint_tail",
        "joint_arm",
        "joint_rod",
    )

    FORBIDDEN_MATERIAL_ALIASES: dict[str, str] = {
        "tail": "tail_rod",
    }

    DEFAULT_BASELINE_PATH = Path("config/baseline/app_settings.json")

    def __init__(
        self,
        settings_manager: SettingsManager | None = None,
        baseline_path: Path | str | None = None,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._settings_manager = settings_manager or get_settings_manager()
        self._baseline_path = (
            Path(baseline_path)
            if baseline_path is not None
            else self.DEFAULT_BASELINE_PATH
        )

        baseline_payload = self._load_json(self._baseline_path)
        self._baseline_graphics_current = self._extract_graphics_section(
            baseline_payload, "current"
        )
        self._baseline_graphics_defaults = self._extract_graphics_section(
            baseline_payload, "defaults_snapshot"
        )
        self._baseline_animation_current = self._extract_animation_section(
            baseline_payload, "current"
        )
        self._baseline_animation_defaults = self._extract_animation_section(
            baseline_payload, "defaults_snapshot"
        )
        self._baseline_current = _deep_copy(self._baseline_graphics_current)
        self._baseline_current[self.ANIMATION_CATEGORY] = _deep_copy(
            self._baseline_animation_current
        )
        self._baseline_defaults = _deep_copy(self._baseline_graphics_defaults)
        self._baseline_defaults[self.ANIMATION_CATEGORY] = _deep_copy(
            self._baseline_animation_defaults
        )

    # ------------------------------------------------------------------ helpers
    @property
    def settings_manager(self) -> SettingsManager:
        return self._settings_manager

    @property
    def settings_file(self) -> Path | None:
        path = getattr(self._settings_manager, "settings_file", None)
        return Path(path) if path is not None else None

    def _load_json(self, path: Path) -> Dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:  # pragma: no cover - defensive branch
            raise GraphicsSettingsError(f"Baseline settings not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise GraphicsSettingsError(
                f"Baseline settings are not valid JSON: {path}: {exc}"
            ) from exc

    def _extract_graphics_section(
        self, payload: Dict[str, Any], section: str
    ) -> Dict[str, Any]:
        container = payload.get(section)
        if not isinstance(container, dict):
            raise GraphicsSettingsError(f"Baseline payload missing '{section}' object")

        graphics = container.get("graphics")
        if not isinstance(graphics, dict):
            raise GraphicsSettingsError(
                f"Baseline payload missing graphics section under '{section}'"
            )
        return _deep_copy(graphics)

    def _extract_animation_section(
        self, payload: Dict[str, Any], section: str
    ) -> Dict[str, Any]:
        container = payload.get(section)
        if not isinstance(container, dict):
            raise GraphicsSettingsError(f"Baseline payload missing '{section}' object")

        animation = container.get(self.ANIMATION_CATEGORY)
        if animation is None:
            return {}
        if not isinstance(animation, dict):
            raise GraphicsSettingsError(
                f"Baseline payload has invalid animation section under '{section}'"
            )
        return _deep_copy(animation)

    def _split_legacy_animation(
        self,
        payload: Dict[str, Any] | None,
        *,
        source: str,
    ) -> tuple[Dict[str, Any], Dict[str, Any] | None]:
        if payload is None:
            return {}, None
        if not isinstance(payload, dict):
            raise GraphicsSettingsError(
                f"graphics state from {source} must be an object, got {type(payload).__name__}"
            )

        sanitized = _deep_copy(payload)
        legacy = sanitized.pop(self.ANIMATION_CATEGORY, None)
        if legacy is not None:
            self._logger.info(
                "Detected legacy graphics.animation in %s settings; treating as deprecated",
                source,
            )
        return sanitized, legacy

    def _resolve_animation_payload(
        self,
        *,
        top_level: Dict[str, Any] | None,
        legacy: Dict[str, Any] | None,
        source: str,
    ) -> Dict[str, Any] | None:
        if top_level is not None:
            if legacy is not None:
                self._logger.warning(
                    "Ignoring legacy graphics.animation in %s settings because current.animation is present",
                    source,
                )
            return top_level
        if legacy is not None:
            self._logger.warning(
                "Dropping legacy graphics.animation in %s settings; the value is no longer consumed",
                source,
            )
            return None
        return None

    def _normalise_materials(
        self,
        materials: Dict[str, Any],
        *,
        baseline: Dict[str, Any],
        allow_missing: bool,
        provided_keys: set[str] | None,
    ) -> Dict[str, Any]:
        normalised: Dict[str, Any] = {}

        for key, value in materials.items():
            if key in self.FORBIDDEN_MATERIAL_ALIASES:
                target = self.FORBIDDEN_MATERIAL_ALIASES[key]
                raise GraphicsSettingsError(
                    "graphics.materials содержит устаревший ключ "
                    f"'{key}' (используйте '{target}')"
                )

            if not isinstance(value, dict):
                raise GraphicsSettingsError(
                    f"graphics.materials['{key}'] must be an object, got {type(value).__name__}"
                )

            base_value = normalised.get(key) or baseline.get(key, {})
            normalised[key] = _deep_merge(base_value, value)

        missing = [key for key in self.REQUIRED_MATERIAL_KEYS if key not in normalised]
        if missing:
            if allow_missing:
                for key in missing:
                    if key in baseline:
                        normalised[key] = _deep_copy(baseline[key])
                still_missing = [
                    key for key in self.REQUIRED_MATERIAL_KEYS if key not in normalised
                ]
                if still_missing:
                    raise GraphicsSettingsError(
                        "graphics.materials is missing required entries: "
                        + ", ".join(sorted(still_missing))
                    )
            else:
                raise GraphicsSettingsError(
                    "graphics.materials is missing required entries: "
                    + ", ".join(sorted(missing))
                )

        if not allow_missing and provided_keys is not None:
            missing_payload = [
                key for key in self.REQUIRED_MATERIAL_KEYS if key not in provided_keys
            ]
            if missing_payload:
                raise GraphicsSettingsError(
                    "graphics.materials payload is missing required entries: "
                    + ", ".join(sorted(missing_payload))
                )

        return normalised

    @staticmethod
    def _coerce_quality_int(value: Any) -> Optional[int]:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            if math.isfinite(value):
                return int(round(value))
            return None
        if isinstance(value, str):
            token = value.strip()
            if not token:
                return None
            try:
                numeric = float(token)
            except ValueError:
                return None
            if not math.isfinite(numeric):
                return None
            return int(round(numeric))
        return None

    def _normalise_quality_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        shadows = payload.get("shadows")
        if isinstance(shadows, dict):
            resolution = self._coerce_quality_int(shadows.get("resolution"))
            if resolution is not None:
                shadows["resolution"] = resolution
        return payload

    def _coerce_state(
        self,
        raw_state: Dict[str, Any] | None,
        *,
        baseline: Dict[str, Any],
        allow_missing: bool,
        source: str,
    ) -> Dict[str, Dict[str, Any]]:
        if raw_state is None:
            raw_state = {}
        if not isinstance(raw_state, dict):
            raise GraphicsSettingsError(
                f"graphics state from {source} must be an object, got {type(raw_state).__name__}"
            )

        state: Dict[str, Dict[str, Any]] = {}

        for category in self.GRAPHICS_CATEGORIES:
            payload = raw_state.get(category)
            baseline_section = baseline.get(category, {})

            if payload is None:
                if allow_missing and baseline_section:
                    state[category] = _deep_copy(baseline_section)
                    continue
                raise GraphicsSettingsError(
                    f"graphics.{category} missing in {source} settings"
                )

            if not isinstance(payload, dict):
                raise GraphicsSettingsError(
                    f"graphics.{category} must be an object, got {type(payload).__name__}"
                )

            if category == "effects" and "color_adjustments_active" in payload:
                payload = dict(payload)
                alias_value = payload["color_adjustments_active"]
                if "color_adjustments_enabled" not in payload:
                    payload["color_adjustments_enabled"] = alias_value
                    self._logger.debug(
                        "Normalised color_adjustments_active alias from %s payload",
                        source,
                    )
                if "color_adjustments_active" not in baseline_section:
                    payload.pop("color_adjustments_active", None)

            if category == "materials":
                alias_candidates = [
                    key for key in payload if key in self.FORBIDDEN_MATERIAL_ALIASES
                ]
                alias_conflicts = sorted(alias_candidates)
                if alias_conflicts:
                    details = ", ".join(
                        f"{alias}->{self.FORBIDDEN_MATERIAL_ALIASES[alias]}"
                        for alias in alias_conflicts
                    )
                    raise GraphicsSettingsError(
                        f"graphics.materials contains legacy keys in {source} settings: {details}"
                    )

            allowed_keys = set(baseline_section.keys())
            unknown_keys = [key for key in payload.keys() if key not in allowed_keys]

            if unknown_keys:
                details = ", ".join(sorted(unknown_keys))
                if allow_missing:
                    self._logger.warning(
                        "Dropping unknown graphics.%s keys from %s payload: %s",
                        category,
                        source,
                        details,
                    )
                    filtered_payload = {
                        key: payload[key] for key in payload if key in allowed_keys
                    }
                else:
                    raise GraphicsSettingsError(
                        "graphics.%s contains unknown keys in %s settings: %s"
                        % (category, source, details)
                    )
            else:
                filtered_payload = payload

            merged = _deep_merge(baseline_section, filtered_payload)

            if category == "materials":
                provided_keys = set(payload.keys())
                merged = self._normalise_materials(
                    merged,
                    baseline=baseline_section,
                    allow_missing=allow_missing,
                    provided_keys=provided_keys if not allow_missing else None,
                )
            elif category == "quality":
                merged = self._normalise_quality_payload(merged)

            state[category] = merged

        return state

    def _coerce_animation(
        self,
        payload: Dict[str, Any] | None,
        *,
        baseline: Dict[str, Any],
        allow_missing: bool,
        source: str,
    ) -> Dict[str, Any]:
        if payload is None:
            if allow_missing and baseline:
                return _deep_copy(baseline)
            if allow_missing:
                return {}
            raise GraphicsSettingsError(
                f"current.animation missing in {source} settings"
            )

        if not isinstance(payload, dict):
            raise GraphicsSettingsError(
                f"current.animation must be an object, got {type(payload).__name__}"
            )

        allowed_keys = set(baseline.keys())
        if allowed_keys:
            unknown_keys = [key for key in payload if key not in allowed_keys]
        else:
            unknown_keys = []

        if unknown_keys:
            details = ", ".join(sorted(unknown_keys))
            if allow_missing:
                self._logger.warning(
                    "Dropping unknown current.animation keys from %s payload: %s",
                    source,
                    details,
                )
                filtered_payload = {
                    key: payload[key] for key in payload if key in allowed_keys
                }
            else:
                raise GraphicsSettingsError(
                    "current.animation contains unknown keys in %s settings: %s"
                    % (source, details)
                )
        else:
            filtered_payload = payload

        return (
            _deep_merge(baseline, filtered_payload)
            if baseline
            else _deep_copy(filtered_payload)
        )

    # -------------------------------------------------------------------- API
    def _apply_persistence_aliases(
        self, state: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Return a deep copy of *state* for persistence."""

        return _deep_copy(state)

    def load_current(self) -> Dict[str, Dict[str, Any]]:
        """Load and normalise the current graphics configuration."""

        raw_graphics = self._settings_manager.get_category("graphics")
        graphics_payload, legacy_animation = self._split_legacy_animation(
            raw_graphics, source="current"
        )
        state = self._coerce_state(
            graphics_payload,
            baseline=self._baseline_graphics_current,
            allow_missing=True,
            source="current",
        )

        top_level_animation = self._settings_manager.get_category(
            self.ANIMATION_CATEGORY
        )
        animation_payload = self._resolve_animation_payload(
            top_level=top_level_animation,
            legacy=legacy_animation,
            source="current",
        )
        state[self.ANIMATION_CATEGORY] = self._coerce_animation(
            animation_payload,
            baseline=self._baseline_animation_current,
            allow_missing=True,
            source="current",
        )

        self._logger.debug(
            "Loaded graphics configuration with categories: %s",
            ", ".join(sorted(state.keys())),
        )
        return state

    def load_defaults(self) -> Dict[str, Dict[str, Any]]:
        """Load and normalise the defaults snapshot."""

        raw_graphics = self._settings_manager.get("defaults_snapshot.graphics")
        graphics_payload, legacy_animation = self._split_legacy_animation(
            raw_graphics, source="defaults_snapshot"
        )
        state = self._coerce_state(
            graphics_payload,
            baseline=self._baseline_graphics_defaults,
            allow_missing=True,
            source="defaults_snapshot",
        )

        top_level_animation = self._settings_manager.get("defaults_snapshot.animation")
        animation_payload = self._resolve_animation_payload(
            top_level=top_level_animation,
            legacy=legacy_animation,
            source="defaults_snapshot",
        )
        state[self.ANIMATION_CATEGORY] = self._coerce_animation(
            animation_payload,
            baseline=self._baseline_animation_defaults,
            allow_missing=True,
            source="defaults_snapshot",
        )

        return state

    def ensure_valid_state(self, state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Validate a state payload originating from the UI before persisting."""

        if not isinstance(state, dict):
            raise GraphicsSettingsError("UI state must be an object")

        unknown_categories = [
            key for key in state if key not in self.REQUIRED_CATEGORIES
        ]
        if unknown_categories:
            details = ", ".join(sorted(unknown_categories))
            raise GraphicsSettingsError(
                f"graphics state contains unknown categories: {details}"
            )

        graphics_payload = {
            category: state.get(category) for category in self.GRAPHICS_CATEGORIES
        }
        validated = self._coerce_state(
            graphics_payload,
            baseline=self._baseline_graphics_current,
            allow_missing=False,
            source="UI",
        )
        validated[self.ANIMATION_CATEGORY] = self._coerce_animation(
            state.get(self.ANIMATION_CATEGORY),
            baseline=self._baseline_animation_current,
            allow_missing=False,
            source="UI",
        )
        return validated

    def save_current(self, state: Dict[str, Any]) -> None:
        """Persist the provided state into the ``current`` section."""

        normalised = self.ensure_valid_state(state)
        animation_state = _deep_copy(normalised[self.ANIMATION_CATEGORY])
        graphics_payload = {
            category: normalised[category] for category in self.GRAPHICS_CATEGORIES
        }
        persistable = self._apply_persistence_aliases(graphics_payload)
        self._settings_manager.set_category("graphics", persistable, auto_save=False)
        self._settings_manager.set_category(
            self.ANIMATION_CATEGORY, animation_state, auto_save=False
        )
        self._settings_manager.save()

    def save_current_as_defaults(self, state: Dict[str, Any]) -> None:
        """Persist the provided state as both current values and defaults."""

        normalised = self.ensure_valid_state(state)
        animation_state = _deep_copy(normalised[self.ANIMATION_CATEGORY])
        graphics_payload = {
            category: normalised[category] for category in self.GRAPHICS_CATEGORIES
        }
        persistable = self._apply_persistence_aliases(graphics_payload)
        self._settings_manager.set_category("graphics", persistable, auto_save=False)
        self._settings_manager.set_category(
            self.ANIMATION_CATEGORY, animation_state, auto_save=False
        )
        self._settings_manager.save_current_as_defaults(
            category="graphics", auto_save=False
        )
        self._settings_manager.save_current_as_defaults(
            category=self.ANIMATION_CATEGORY, auto_save=False
        )
        self._settings_manager.save()

    def reset_to_defaults(self) -> Dict[str, Dict[str, Any]]:
        """Reset the ``current`` settings and return the refreshed state."""

        self._settings_manager.reset_to_defaults(category="graphics", auto_save=False)
        self._settings_manager.reset_to_defaults(
            category=self.ANIMATION_CATEGORY, auto_save=False
        )
        self._settings_manager.save()
        return self.load_current()


__all__ = [
    "GraphicsSettingsError",
    "GraphicsSettingsService",
]
