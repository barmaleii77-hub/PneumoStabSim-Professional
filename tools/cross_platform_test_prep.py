#!/usr/bin/env python3
"""Provision cross-platform test dependencies and run the validation suite.

The script is the single entry point for preparing Linux *and* Windows hosts
for the full PneumoStabSim test matrix.  It installs system packages when
available, synchronises Python dependencies, ensures the Qt runtime can be
imported, and optionally executes pytest with the correct environment guards.

The workflow intentionally mirrors the manual steps from
``docs/ENVIRONMENT_SETUP.md`` so that CI agents and local workstations share
the exact same bootstrap sequence.
"""

from __future__ import annotations

import argparse
import importlib
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


LINUX_SYSTEM_PACKAGES: tuple[str, ...] = (
    "xvfb",
    "xauth",
    "dbus-x11",
    "mesa-utils",
    "libgl1",
    "libgl1-mesa-dri",
    "libglu1-mesa",
    "libglu1-mesa-dev",
    "libegl1",
    "libegl-mesa0",
    "libgles2",
    "libgles2-mesa-dev",
    "libosmesa6",
    "libosmesa6-dev",
    "libgbm1",
    "libdrm2",
    "libxcb-xinerama0",
    "libxkbcommon0",
    "libxkbcommon-x11-0",
    "libxcb-keysyms1",
    "libxcb-image0",
    "libxcb-icccm4",
    "libxcb-render-util0",
    "libxcb-xfixes0",
    "libxcb-shape0",
    "libxcb-randr0",
    "libxcb-glx0",
    "libvulkan1",
    "mesa-vulkan-drivers",
    "vulkan-tools",
)

WINDOWS_CHOCOLATEY_PACKAGES: tuple[str, ...] = ("make",)


REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_DEPENDENCY_SENTINELS: tuple[str, ...] = (
    "pytestqt.plugin",
    "PySide6.QtWidgets",
    "PySide6.QtQml",
)


@dataclass
class CommandStep:
    """Describe a command that needs to be executed."""

    command: Sequence[str]
    description: str
    env: dict[str, str] | None = None
    cwd: Path | None = None


def _run_step(step: CommandStep) -> None:
    """Run a command and raise a helpful error when it fails."""

    printable = " ".join(step.command)
    print(f"→ {step.description}: {printable}")
    try:
        subprocess.run(
            step.command,
            cwd=step.cwd or REPO_ROOT,
            env=step.env,
            check=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - external command
        raise RuntimeError(
            f"Command '{printable}' failed with exit code {exc.returncode}"
        ) from exc


def _is_root() -> bool:
    """Return ``True`` when the current process has administrative privileges."""

    if hasattr(os, "geteuid"):
        return os.geteuid() == 0
    return False


def _apt_prefix() -> list[str]:
    return [] if _is_root() else ["sudo"]


def install_linux_system_packages(packages: Iterable[str]) -> None:
    """Install the system packages required for Qt headless execution."""

    if shutil.which("apt-get") is None:
        print("⚠️ Skipping system package installation: apt-get is not available.")
        print(
            "   Install the following packages manually to enable Qt headless runs:"
        )
        for package in packages:
            print(f"     - {package}")
        return

    prefix = _apt_prefix()
    update_cmd = [*prefix, "apt-get", "update"]
    install_cmd = [
        *prefix,
        "apt-get",
        "install",
        "-y",
        "--no-install-recommends",
        *packages,
    ]

    _run_step(CommandStep(update_cmd, "Update APT package index"))
    _run_step(CommandStep(install_cmd, "Install Linux Qt runtime dependencies"))


def install_windows_system_packages(packages: Iterable[str]) -> None:
    """Install Windows utilities required for the Make-based workflow."""

    if shutil.which("choco") is None:
        print("⚠️ Skipping Chocolatey installation: choco is not available.")
        print(
            "   Install Chocolatey from https://chocolatey.org/install and rerun "
            "the script to provision Windows toolchain prerequisites."
        )
        return

    for package in packages:
        _run_step(
            CommandStep(
                ["choco", "install", package, "--no-progress", "-y"],
                f"Install Windows dependency '{package}' via Chocolatey",
            )
        )


def install_python_dependencies(use_uv: bool) -> None:
    """Install project Python dependencies for the full test matrix."""

    if use_uv and shutil.which("uv") is not None:
        _run_step(
            CommandStep(
                ["uv", "sync", "--frozen", "--extra", "dev"],
                "Synchronise Python environment with uv",
            )
        )
    else:
        _run_step(
            CommandStep(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                "Upgrade pip",
            )
        )
        requirements_path = REPO_ROOT / "requirements-dev.txt"
        if requirements_path.exists():
            _run_step(
                CommandStep(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "-r",
                        str(requirements_path),
                    ],
                    "Install Python development dependencies",
                )
            )
        else:
            _run_step(
                CommandStep(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "-r",
                        str(REPO_ROOT / "requirements.txt"),
                    ],
                    "Install base Python dependencies",
                )
            )


def verify_python_runtime() -> None:
    """Ensure critical Python dependencies for cross-platform tests are importable."""

    missing: list[str] = []
    for module_name in PYTHON_DEPENDENCY_SENTINELS:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - platform dependant imports
            missing.append(f"{module_name}: {exc}")

    if missing:
        details = "\n".join(f"  - {line}" for line in missing)
        raise RuntimeError(
            "Required Python modules for Qt/pytest integration are unavailable.\n"
            f"Install missing modules and rerun provisioning.\n{details}"
        )


def provision_qt_runtime(version: str) -> None:
    """Install the standalone Qt runtime via ``tools/setup_qt.py``."""

    args = [sys.executable, "tools/setup_qt.py", "--qt-version", version, "--force"]
    _run_step(CommandStep(args, f"Provision Qt runtime {version}"))


def run_test_suite(extra_args: Sequence[str]) -> None:
    """Execute the pytest suite with headless defaults for the active platform."""

    system = platform.system()
    env = os.environ.copy()
    env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    env.setdefault("PYTEST_QT_API", "pyside6")
    env.setdefault("PSS_ENV_PRESET", "trace")

    if system == "Linux":
        env.setdefault("PSS_HEADLESS", "1")
        env.setdefault("QT_QPA_PLATFORM", "offscreen")
        env.setdefault("QT_QUICK_BACKEND", "software")
        env.setdefault("QSG_RHI_BACKEND", "opengl")
        env.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
        env.setdefault("MESA_GL_VERSION_OVERRIDE", "4.1")
        env.setdefault("MESA_GLSL_VERSION_OVERRIDE", "410")
    elif system == "Windows":
        env.setdefault("QT_QPA_PLATFORM", "offscreen")
        env.setdefault("QT_QUICK_BACKEND", "rhi")
        env.setdefault("QSG_RHI_BACKEND", "d3d11")

    command = [sys.executable, "-m", "pytest", "-vv", *extra_args]
    _run_step(CommandStep(command, "Run cross-platform pytest suite", env=env))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-system",
        action="store_true",
        help="Skip installation of operating system packages",
    )
    parser.add_argument(
        "--skip-python",
        action="store_true",
        help="Skip installation of Python dependencies",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Execute pytest after provisioning is complete",
    )
    parser.add_argument(
        "--use-uv",
        action="store_true",
        help="Prefer uv for Python dependency management when available",
    )
    parser.add_argument(
        "--qt-version",
        default=os.environ.get("QT_VERSION"),
        help="Optional Qt version to provision via tools/setup_qt.py",
    )
    parser.add_argument(
        "--pytest-args",
        nargs=argparse.REMAINDER,
        default=(),
        help="Additional arguments forwarded to pytest",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    os.chdir(REPO_ROOT)
    system = platform.system()
    print(f"ℹ️ Detected platform: {system}")

    if not args.skip_system:
        if system == "Linux":
            install_linux_system_packages(LINUX_SYSTEM_PACKAGES)
        elif system == "Windows":
            install_windows_system_packages(WINDOWS_CHOCOLATEY_PACKAGES)

    if not args.skip_python:
        install_python_dependencies(use_uv=args.use_uv)
        verify_python_runtime()

    if args.qt_version:
        provision_qt_runtime(args.qt_version)

    if args.run_tests:
        run_test_suite(tuple(args.pytest_args))

    print("✅ Cross-platform test preparation completed.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
