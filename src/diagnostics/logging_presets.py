"""Utilities for managing consistent logging presets across launch scripts."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Mapping
from collections.abc import MutableMapping


@dataclass(frozen=True)
class LoggingPreset:
    """Description of a logging preset applied during bootstrap."""

    name: str
    python_level: int
    qt_logging_rules: str
    qsg_info: str
    enable_diag_details: bool = False


_PRESETS: dict[str, LoggingPreset] = {
    "normal": LoggingPreset(
        name="normal",
        python_level=logging.INFO,
        qt_logging_rules="*.debug=false;*.info=false",
        qsg_info="0",
    ),
    "debug": LoggingPreset(
        name="debug",
        python_level=logging.DEBUG,
        qt_logging_rules="qt.qml.connections=true;qt.quick.3d=true",
        qsg_info="1",
    ),
    "trace": LoggingPreset(
        name="trace",
        python_level=logging.DEBUG,
        qt_logging_rules=(
            "qt.qml.connections=true;qt.quick.3d=true;"
            "qt.quick.animations=true;qt.scenegraph.general=true"
        ),
        qsg_info="1",
        enable_diag_details=True,
    ),
}

_DEFAULT_PRESET = _PRESETS["normal"]


def _normalise_key(value: object | None) -> str:
    if value is None:
        return ""
    try:
        return str(value).strip().lower()
    except Exception:
        return ""


def select_logging_preset(name: object | None) -> LoggingPreset:
    """Return the preset matching ``name`` falling back to ``normal``."""

    key = _normalise_key(name)
    preset = _PRESETS.get(key)
    if preset is not None:
        return preset
    return _DEFAULT_PRESET


def apply_logging_preset(
    env: MutableMapping[str, str],
    *,
    requested: object | None = None,
) -> LoggingPreset:
    """Apply the logging preset to ``env`` and return its configuration."""

    preset = select_logging_preset(requested or env.get("PSS_LOG_PRESET"))

    env["PSS_LOG_PRESET"] = preset.name
    env["QT_LOGGING_RULES"] = preset.qt_logging_rules
    env["QSG_INFO"] = preset.qsg_info

    if preset.enable_diag_details:
        env["PSS_DIAG_DETAILS"] = "1"
    else:
        if isinstance(env, MutableMapping):
            env.pop("PSS_DIAG_DETAILS", None)

    return preset


def describe_presets() -> Mapping[str, LoggingPreset]:
    """Expose the available presets for documentation and tooling."""

    return dict(_PRESETS)


__all__ = [
    "LoggingPreset",
    "apply_logging_preset",
    "describe_presets",
    "select_logging_preset",
]
