"""Utilities for configuring Visual Studio Insiders integration."""

from __future__ import annotations

from collections import OrderedDict
import json
from pathlib import Path, PureWindowsPath
from typing import Dict, Iterable

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
    "POWERSHELL_UPDATECHECK",
    "POWERSHELL_TELEMETRY_OPTOUT",
)


def _as_windows_path(path: Path) -> str:
    """Return a Windows-formatted path string for *path*.

    Visual Studio Insiders runs on Windows.  We nevertheless execute the
    generator on Linux during CI, therefore this helper normalises the path to
    the format expected by Visual Studio regardless of the host platform.
    """

    return str(PureWindowsPath(path))


def _candidate_site_packages_roots(venv_root: Path) -> Iterable[Path]:
    """Yield possible site-packages directories for *venv_root*."""

    # Prefer the Windows-style layout used by Visual Studio virtual
    # environments.  Fall back to POSIX layouts to support validation during
    # CI runs executed on Linux hosts.
    yield venv_root / "Lib" / "site-packages"
    for prefix in ("lib", "lib64"):
        site_packages_root = venv_root / prefix
        if not site_packages_root.exists():
            continue
        yield from site_packages_root.glob("python*/site-packages")
    yield venv_root / "site-packages"


def _resolve_pyside_root(venv_root: Path, *, ensure_exists: bool) -> Path:
    """Return the path to the PySide6 installation inside *venv_root*."""

    candidates = [
        root / "PySide6" for root in _candidate_site_packages_roots(venv_root)
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    if ensure_exists:
        raise FileNotFoundError(
            "PySide6 was not found in the virtual environment. Run "
            "'initialize_insiders_environment.ps1' to provision dependencies."
        )

    # Fall back to the first candidate even if it does not exist.  This keeps
    # generation idempotent when validation is intentionally skipped, e.g. in
    # documentation builds that do not ship the virtual environment.
    return (
        candidates[0] if candidates else venv_root / "Lib" / "site-packages" / "PySide6"
    )


def _ensure_path(path: Path, description: str, *, ensure_exists: bool) -> Path:
    if ensure_exists and not path.exists():
        raise FileNotFoundError(f"{description} was not found at '{path}'.")
    return path


def build_insiders_environment(
    project_root: Path, *, ensure_paths: bool = False
) -> Dict[str, str]:
    """Build the environment map used by the Insiders configuration."""

    resolved_root = project_root.resolve()
    venv_root = _ensure_path(
        resolved_root / ".venv", "Virtual environment root", ensure_exists=ensure_paths
    )
    pyside_root = _ensure_path(
        _resolve_pyside_root(venv_root, ensure_exists=ensure_paths),
        "PySide6 root",
        ensure_exists=ensure_paths,
    )
    qml_runtime_root = _ensure_path(
        pyside_root / "qml", "PySide6 QML runtime", ensure_exists=ensure_paths
    )
    plugin_root = _ensure_path(
        pyside_root / "plugins", "PySide6 plugin directory", ensure_exists=ensure_paths
    )
    assets_qml_root = _ensure_path(
        resolved_root / "assets" / "qml",
        "Project QML assets directory",
        ensure_exists=ensure_paths,
    )

    windows_root = _as_windows_path(resolved_root)
    env: Dict[str, str] = {
        "QML2_IMPORT_PATH": _as_windows_path(qml_runtime_root)
        + ";"
        + _as_windows_path(assets_qml_root),
        "QML_IMPORT_PATH": _as_windows_path(qml_runtime_root)
        + ";"
        + _as_windows_path(assets_qml_root),
        "QT_PLUGIN_PATH": _as_windows_path(plugin_root),
        "QT_QML_IMPORT_PATH": _as_windows_path(qml_runtime_root),
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
        "POWERSHELL_UPDATECHECK": "Off",
        "POWERSHELL_TELEMETRY_OPTOUT": "1",
    }

    missing_keys = [key for key in _ENV_KEYS if key not in env]
    if missing_keys:
        raise ValueError(f"Missing expected keys: {', '.join(missing_keys)}")

    ordered = OrderedDict((key, env[key]) for key in _ENV_KEYS)
    return dict(ordered)


def validate_insiders_environment(project_root: Path) -> Dict[str, str]:
    """Validate that the Insiders profile can be generated for *project_root*."""

    return build_insiders_environment(project_root, ensure_paths=True)


def dumps_environment(environment: Dict[str, str], *, indent: int | None = 2) -> str:
    """Serialise *environment* to JSON using UTF-8 ordering."""

    return json.dumps(environment, indent=indent, ensure_ascii=False)


__all__ = [
    "build_insiders_environment",
    "validate_insiders_environment",
    "dumps_environment",
]
