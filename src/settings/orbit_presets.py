"""Orbit preset manifest location helpers."""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["ORBIT_PRESETS_ENV_VAR", "ORBIT_PRESETS_PATH", "orbit_presets_path"]

ORBIT_PRESETS_ENV_VAR = "PSS_ORBIT_PRESETS_FILE"
_ORBIT_PRESETS_DEFAULT = Path("config/orbit_presets.json")


def _expand(path: Path | str) -> Path:
    raw = str(path)
    expanded = os.path.expandvars(raw)
    return Path(expanded).expanduser()


def orbit_presets_path(override: Path | str | None = None) -> Path:
    """Return the path to the orbit preset manifest."""

    if override is not None:
        return _expand(override)

    env_override = os.environ.get(ORBIT_PRESETS_ENV_VAR)
    if env_override:
        return _expand(env_override)

    return _expand(_ORBIT_PRESETS_DEFAULT)


ORBIT_PRESETS_PATH = orbit_presets_path()
