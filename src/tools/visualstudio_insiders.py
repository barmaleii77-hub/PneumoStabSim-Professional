"""Utilities for configuring Visual Studio Insiders integration."""

from __future__ import annotations

import json
from pathlib import Path, PureWindowsPath
from typing import Dict

_ENV_KEYS = (
    "QML2_IMPORT_PATH",
    "QML_IMPORT_PATH",
    "QT_PLUGIN_PATH",
    "QT_QML_IMPORT_PATH",
    "QT_QUICK_CONTROLS_STYLE",
    "PYTHONPATH",
    "PYTHONUTF8",
    "PYTHONIOENCODING",
    "PIP_DISABLE_PIP_VERSION_CHECK",
    "PIP_NO_PYTHON_VERSION_WARNING",
    "LC_ALL",
    "LANG",
    "PNEUMOSTABSIM_PROFILE",
    "VIRTUAL_ENV",
)


def _as_windows_path(path: Path) -> str:
    """Return a Windows-formatted path string for *path*.

    Visual Studio Insiders runs on Windows.  We nevertheless execute the
    generator on Linux during CI, therefore this helper normalises the path to
    the format expected by Visual Studio regardless of the host platform.
    """

    return str(PureWindowsPath(path))


def build_insiders_environment(project_root: Path) -> Dict[str, str]:
    """Build the environment map used by the Insiders configuration."""

    resolved_root = project_root.resolve()
    venv_root = resolved_root / ".venv"
    site_packages = venv_root / "Lib" / "site-packages"
    pyside_root = site_packages / "PySide6"

    windows_root = _as_windows_path(resolved_root)
    env: Dict[str, str] = {
        "QML2_IMPORT_PATH": _as_windows_path(pyside_root / "qml")
        + ";"
        + _as_windows_path(resolved_root / "assets" / "qml"),
        "QML_IMPORT_PATH": _as_windows_path(pyside_root / "qml")
        + ";"
        + _as_windows_path(resolved_root / "assets" / "qml"),
        "QT_PLUGIN_PATH": _as_windows_path(pyside_root / "plugins"),
        "QT_QML_IMPORT_PATH": _as_windows_path(pyside_root / "qml"),
        "QT_QUICK_CONTROLS_STYLE": "Basic",
        "PYTHONPATH": ";".join(
            (
                windows_root,
                _as_windows_path(resolved_root / "src"),
                _as_windows_path(resolved_root / "tests"),
            )
        ),
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_NO_PYTHON_VERSION_WARNING": "1",
        "LC_ALL": "C.UTF-8",
        "LANG": "en_US.UTF-8",
        "PNEUMOSTABSIM_PROFILE": "insiders",
        "VIRTUAL_ENV": _as_windows_path(venv_root),
    }

    missing_keys = [key for key in _ENV_KEYS if key not in env]
    if missing_keys:
        raise ValueError(f"Missing expected keys: {', '.join(missing_keys)}")

    return env


def dumps_environment(environment: Dict[str, str], *, indent: int | None = 2) -> str:
    """Serialise *environment* to JSON using UTF-8 ordering."""

    return json.dumps(environment, indent=indent, ensure_ascii=False)


__all__ = [
    "build_insiders_environment",
    "dumps_environment",
]
