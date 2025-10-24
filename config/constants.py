"""Centralized access to static configuration constants."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Mapping

_SETTINGS_FILE_ENV = "PSS_SETTINGS_FILE"
_SETTINGS_FILE_NAME = "app_settings.json"


def _resolve_settings_file(custom_path: str | os.PathLike[str] | None = None) -> Path:
    """Resolve the path to app_settings.json.

    Lookup order matches SettingsManager to keep sources consistent:
    1) Explicit custom_path (mainly for tests)
    2) PSS_SETTINGS_FILE environment variable
    3) app_settings.json located next to this module (config/)
    """
    if custom_path is not None:
        path = Path(custom_path).expanduser().resolve()
        if path.exists():
            return path

    env_path = os.environ.get(_SETTINGS_FILE_ENV)
    if env_path:
        path = Path(env_path).expanduser().resolve()
        if path.exists():
            return path

    return Path(__file__).resolve().with_name(_SETTINGS_FILE_NAME)


@lru_cache(maxsize=1)
def _load_settings(custom_path: str | os.PathLike[str] | None = None) -> Dict[str, Any]:
    """Load the JSON settings file and cache the parsed structure."""
    settings_path = _resolve_settings_file(custom_path)
    with settings_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def _get_constants_root(
    root_key: str = "current",
    *,
    custom_path: str | os.PathLike[str] | None = None,
) -> Mapping[str, Any]:
    """Return the constants section for the requested root key (current/defaults_snapshot)."""
    data = _load_settings(custom_path)
    root = data.get(root_key, {})
    constants = root.get("constants")
    if constants is None:
        raise KeyError(
            f"Missing 'constants' section under '{root_key}' in app_settings.json"
        )
    return constants


def _get_constants_section(
    section: str,
    *,
    root_key: str = "current",
    custom_path: str | os.PathLike[str] | None = None,
) -> Mapping[str, Any]:
    """Helper that returns a nested constants section by name."""
    constants = _get_constants_root(root_key, custom_path=custom_path)
    try:
        return constants[section]
    except KeyError as exc:  # pragma: no cover - defensive branch
        raise KeyError(
            f"Missing constants section '{section}' under '{root_key}'"
        ) from exc


def refresh_cache() -> None:
    """Clear the cached JSON payload (useful for tests)."""
    _load_settings.cache_clear()


def get_geometry_constants(
    *,
    custom_path: str | os.PathLike[str] | None = None,
) -> Mapping[str, Any]:
    """Return the entire geometry constants mapping."""
    return _get_constants_section("geometry", custom_path=custom_path)


def get_geometry_kinematics_constants(
    *,
    custom_path: str | os.PathLike[str] | None = None,
) -> Mapping[str, Any]:
    """Return geometry constants for kinematic calculations."""
    geometry = get_geometry_constants(custom_path=custom_path)
    return geometry.get("kinematics", {})


def get_geometry_cylinder_constants(
    *,
    custom_path: str | os.PathLike[str] | None = None,
) -> Mapping[str, Any]:
    """Return cylinder-related geometry constants."""
    geometry = get_geometry_constants(custom_path=custom_path)
    return geometry.get("cylinder", {})


def get_geometry_visual_constants(
    *,
    custom_path: str | os.PathLike[str] | None = None,
) -> Mapping[str, Any]:
    """Return visualization-related geometry constants."""
    geometry = get_geometry_constants(custom_path=custom_path)
    return geometry.get("visualization", {})


def get_geometry_initial_state_constants(
    *,
    custom_path: str | os.PathLike[str] | None = None,
) -> Mapping[str, Any]:
    """Return constants that define the neutral geometry state."""
    geometry = get_geometry_constants(custom_path=custom_path)
    return geometry.get("initial_state", {})
