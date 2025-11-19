#!/usr/bin/env python3
"""Bootstrap installer for project dependencies."""

from __future__ import annotations

import importlib.util
import os
import pathlib
import re
import subprocess
import sys
from collections.abc import Iterable

import tomllib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.platform_info import log_platform_context  # noqa: E402

REQ_FILES = [PROJECT_ROOT / "requirements-dev.txt", PROJECT_ROOT / "requirements.txt"]


def pip_install(args: Iterable[str]) -> None:
    items: list[str] = [str(a) for a in args if str(a).strip()]
    if not items:
        return
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", *items])


def install_requirements() -> None:
    for path in REQ_FILES:
        if path.exists():
            print(f"[deps] installing from {path.relative_to(PROJECT_ROOT)}")
            pip_install(["-r", str(path)])


def install_optional_dev() -> None:
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if not pyproject.exists():
        return
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = data.get("project")
    if not isinstance(project, dict):
        return
    optional = project.get("optional-dependencies")
    if not isinstance(optional, dict):
        return
    dev = optional.get("dev")
    if isinstance(dev, dict):
        dependencies = list(dev.values())
    elif isinstance(dev, (list, tuple)):
        dependencies = list(dev)
    else:
        dependencies = []
    flat: list[str] = []
    for entry in dependencies:
        if isinstance(entry, str):
            flat.append(entry)
        elif isinstance(entry, (list, tuple)):
            flat.extend(str(item) for item in entry if str(item).strip())
    if flat:
        print("[deps] installing pyproject optional-dependencies.dev")
        pip_install(flat)


MINIMUM_PYSIDE_VERSION = (6, 10, 0)


def _parse_version_tuple(version: str) -> tuple[int, int, int]:
    parts = [int(part) for part in re.findall(r"\d+", version)]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def _is_supported_version(version: str) -> bool:
    return _parse_version_tuple(version) >= MINIMUM_PYSIDE_VERSION


def install_pyside() -> None:
    candidates = [
        version.strip()
        for version in os.environ.get("PYSIDE_VERSIONS", "6.10.0").split(",")
        if version.strip()
    ]
    minimum_label = ".".join(str(part) for part in MINIMUM_PYSIDE_VERSION)
    for version in candidates:
        if not _is_supported_version(version):
            raise RuntimeError(
                f"Requested PySide6 version '{version}' is below the supported minimum {minimum_label}"
            )
        try:
            print(f"[deps] installing PySide6/shiboken6 {version}")
            pip_install([f"pyside6=={version}", f"shiboken6=={version}"])
        except subprocess.CalledProcessError as exc:
            print(f"[deps] PySide6 {version} unavailable: {exc}")
        else:
            return
    print("[deps] falling back to latest PySide6/shiboken6 from PyPI")
    pip_install(["pyside6>=6.10,<7", "shiboken6>=6.10,<7"])


def install_critical_runtime() -> None:
    install_pyside()
    other = [
        "numpy",
        "scipy",
        "pyyaml",
        "tomli; python_version<'3.11'",
    ]
    print("[deps] installing critical runtime set …")
    pip_install(other)


def check_modules() -> None:
    modules = ["PySide6", "shiboken6", "numpy", "scipy"]
    for name in modules:
        if importlib.util.find_spec(name) is None:
            print(f"[deps] WARNING: module '{name}' not importable")


def main() -> None:
    log_platform_context({"script": "install_deps"})
    install_requirements()
    install_optional_dev()
    install_critical_runtime()
    check_modules()


if __name__ == "__main__":
    main()
