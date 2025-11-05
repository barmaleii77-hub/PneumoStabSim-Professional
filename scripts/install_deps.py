#!/usr/bin/env python
"""Bootstrap installer for project dependencies."""
from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
import tomllib
from typing import Iterable, List

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQ_FILES = [ROOT / "requirements-dev.txt", ROOT / "requirements.txt"]


def pip_install(args: Iterable[str]) -> None:
    items: List[str] = [str(a) for a in args if str(a).strip()]
    if not items:
        return
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", *items])


def install_requirements() -> None:
    for path in REQ_FILES:
        if path.exists():
            print(f"[deps] installing from {path.relative_to(ROOT)}")
            pip_install(["-r", str(path)])


def install_optional_dev() -> None:
    pyproject = ROOT / "pyproject.toml"
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
    flat: List[str] = []
    for entry in dependencies:
        if isinstance(entry, str):
            flat.append(entry)
        elif isinstance(entry, (list, tuple)):
            flat.extend(str(item) for item in entry if str(item).strip())
    if flat:
        print("[deps] installing pyproject optional-dependencies.dev")
        pip_install(flat)


def install_critical_runtime() -> None:
    critical = [
        "pyside6==6.10.0",
        "shiboken6==6.10.0",
        "numpy",
        "scipy",
        "pyyaml",
        "tomli; python_version<'3.11'",
    ]
    print("[deps] installing critical runtime set …")
    pip_install(critical)


def check_modules() -> None:
    modules = ["PySide6", "shiboken6", "numpy", "scipy"]
    for name in modules:
        if importlib.util.find_spec(name) is None:
            print(f"[deps] WARNING: module '{name}' not importable")


def main() -> None:
    install_requirements()
    install_optional_dev()
    install_critical_runtime()
    check_modules()


if __name__ == "__main__":
    main()
