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
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


LINUX_SYSTEM_PACKAGES: tuple[str, ...] = (
    "git",
    "curl",
    "ca-certificates",
    "pkg-config",
    "build-essential",
    "xvfb",
    "xauth",
    "dbus-x11",
    "mesa-utils",
    "mesa-utils-extra",
    "libgl1",
    "libgl1-mesa-dri",
    "libglu1-mesa",
    "libglu1-mesa-dev",
    "libegl1",
    "libegl-dev",
    "libegl-mesa0",
    "libgles2",
    "libgles-dev",
    "libgles2-mesa-dev",
    "libosmesa6",
    "libosmesa6-dev",
    "libgbm1",
    "libdrm2",
    "libx11-6",
    "libx11-xcb1",
    "libxext6",
    "libxrender1",
    "libxi6",
    "libxfixes3",
    "libxrandr2",
    "libxcursor1",
    "libxinerama1",
    "libxdamage1",
    "libxcb1",
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
    "qt6-shader-tools",
)

WINDOWS_CHOCOLATEY_PACKAGES: tuple[str, ...] = ("make",)


REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_DEPENDENCY_SENTINELS: tuple[str, ...] = (
    "pytestqt.plugin",
    "PySide6.QtWidgets",
    "PySide6.QtQml",
)

LINUX_GL_RUNTIME_PACKAGES: tuple[str, ...] = (
    "libgl1",
    "libgl1-mesa-dri",
    "libglu1-mesa",
    "libegl1",
    "libosmesa6",
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
        print("   Install the following packages manually to enable Qt headless runs:")
        for package in packages:
            print(f"     - {package}")
        return

    prefix = _apt_prefix()
    update_cmd = [*prefix, "apt-get", "update"]
    _run_step(CommandStep(update_cmd, "Update APT package index"))

    available_packages: list[str] = []
    missing_packages: list[str] = []
    for package in packages:
        result = subprocess.run(
            ["apt-cache", "show", package],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            available_packages.append(package)
        else:
            missing_packages.append(package)

    if missing_packages:
        print("⚠️ Skipping unavailable packages: " + ", ".join(sorted(missing_packages)))

    if not available_packages:
        print(
            "⚠️ No installable Linux packages detected; continuing without system provisioning."
        )
        return

    install_cmd = [
        *prefix,
        "apt-get",
        "install",
        "-y",
        "--no-install-recommends",
        *available_packages,
    ]

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


def _resolve_uv_python_interpreter() -> Path | None:
    """Return the Python interpreter provisioned by ``uv sync`` when available."""

    env_root = REPO_ROOT / ".venv"
    if not env_root.exists():
        return None

    if os.name == "nt":
        candidates = [
            env_root / "Scripts" / "python.exe",
            env_root / "Scripts" / "python",
        ]
    else:
        candidates = [
            env_root / "bin" / "python3",
            env_root / "bin" / "python",
        ]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def install_python_dependencies(use_uv: bool) -> Path | None:
    """Install project Python dependencies for the full test matrix.

    Returns the interpreter that should be used for runtime validation. When
    ``uv`` provisions the environment, the interpreter resolves to
    ``.venv/bin/python`` (or the Windows equivalent). Otherwise the current
    interpreter is returned so that module checks execute inside the active
    virtualenv.
    """

    if use_uv and shutil.which("uv") is not None:
        _run_step(
            CommandStep(
                ["uv", "sync", "--frozen", "--extra", "dev"],
                "Synchronise Python environment with uv",
            )
        )
        return _resolve_uv_python_interpreter()

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
    project_target = [sys.executable, "-m", "pip", "install", "-e", ".[dev]"]
    _run_step(CommandStep(project_target, "Install project with dev extras"))
    return Path(sys.executable)


def verify_python_runtime(
    interpreter: Path | None,
    *,
    platform_system: str,
    skip_system_packages: bool,
) -> None:
    """Ensure critical Python dependencies for cross-platform tests are importable."""

    if interpreter is None:
        interpreter = Path(sys.executable)

    script = (
        "import importlib\n"
        "import sys\n\n"
        f"sentinels = {list(PYTHON_DEPENDENCY_SENTINELS)!r}\n"
        "missing = []\n"
        "for module_name in sentinels:\n"
        "    try:\n"
        "        importlib.import_module(module_name)\n"
        "    except Exception as exc:  # pragma: no cover - delegated to subprocess\n"
        '        missing.append(f"{module_name}: {exc}")\n\n'
        "if missing:\n"
        "    for line in missing:\n"
        "        print(line)\n"
        "    sys.exit(1)\n"
    )

    result = subprocess.run(  # noqa: S603 - trusted interpreter discovered above
        [str(interpreter), "-c", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        combined_output = (result.stdout or "") + (result.stderr or "")
        details = combined_output.strip()
        hints: list[str] = []
        if skip_system_packages and platform_system == "Linux" and details:
            missing_tokens = ("libGL", "libEGL", "libxcb", "libX11")
            if any(token in details for token in missing_tokens):
                apt_packages = " ".join(LINUX_GL_RUNTIME_PACKAGES)
                hints.append(
                    "Detected missing OpenGL system libraries required by Qt."
                    " Re-run without --skip-system or install the packages manually:\n"
                    "  sudo apt-get install --no-install-recommends " + apt_packages
                )

        message = (
            "Required Python modules for Qt/pytest integration are unavailable."
            "\nInstall missing modules and rerun provisioning."
        )
        if details:
            message += "\n" + details
        if hints:
            message += "\n\n" + "\n\n".join(hints)
        raise RuntimeError(message)


def provision_qt_runtime(version: str) -> None:
    """Install the standalone Qt runtime via ``tools/setup_qt.py``."""

    args = [sys.executable, "tools/setup_qt.py", "--qt-version", version, "--force"]
    _run_step(CommandStep(args, f"Provision Qt runtime {version}"))


def run_test_suite(extra_args: Sequence[str], interpreter: Path | None) -> None:
    """Execute the pytest suite with headless defaults for the active platform."""

    system = platform.system()
    env = os.environ.copy()
    env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    env.setdefault("PYTEST_QT_API", "pyside6")
    env.setdefault("PSS_ENV_PRESET", "trace")
    env.setdefault("QT_QUICK_CONTROLS_STYLE", "Fusion")

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

    pytest_args = list(extra_args)
    if not pytest_args:
        pytest_args = ["tests"]

    runtime_python = (
        interpreter or _resolve_uv_python_interpreter() or Path(sys.executable)
    )
    python_executable = str(runtime_python)
    command = [python_executable, "-m", "pytest", "-vv", *pytest_args]
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

    runtime_interpreter: Path | None = None
    if not args.skip_python:
        runtime_interpreter = install_python_dependencies(use_uv=args.use_uv)
    verify_python_runtime(
        runtime_interpreter,
        platform_system=system,
        skip_system_packages=args.skip_system,
    )

    if args.qt_version:
        provision_qt_runtime(args.qt_version)

    if args.run_tests:
        run_test_suite(tuple(args.pytest_args), runtime_interpreter)

    print("✅ Cross-platform test preparation completed.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
