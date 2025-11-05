#!/usr/bin/env python3
"""Bootstrap script for installing and initialising the uv package manager."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

INSTALL_SCRIPT_SH = "https://astral.sh/uv/install.sh"
INSTALL_SCRIPT_PS = "https://astral.sh/uv/install.ps1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ensure the uv package manager is installed and optionally run `uv sync` "
            "for the current project."
        )
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project directory where pyproject.toml resides (default: repository root).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reinstall uv even if it is already available in PATH.",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Run `uv sync` after ensuring uv is installed.",
    )
    parser.add_argument(
        "--lock",
        action="store_true",
        help="Run `uv lock` to refresh the lockfile after ensuring uv is installed.",
    )
    parser.add_argument(
        "--export-requirements",
        action="store_true",
        help=(
            "Regenerate requirements exports via `uv export` after syncing. "
            "Implies --lock so the exports always reflect the current lockfile."
        ),
    )
    parser.add_argument(
        "--executable",
        type=str,
        default="uv",
        help="Explicit uv executable to invoke (default: 'uv').",
    )
    return parser.parse_args()


def find_uv(explicit: str) -> Optional[str]:
    """Locate the uv executable, respecting an explicit path if provided."""
    explicit_path = Path(explicit)
    if explicit_path.is_file() and os.access(explicit_path, os.X_OK):
        return str(explicit_path)
    return shutil.which(explicit)


def install_uv() -> None:
    system = platform.system()
    if system == "Windows":
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"irm {INSTALL_SCRIPT_PS} | iex",
        ]
    else:
        command = [
            "sh",
            "-c",
            f"curl -LsSf {INSTALL_SCRIPT_SH} | sh",
        ]
    print("Installing uv using official bootstrap script…", file=sys.stderr)
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            "uv installation script failed. Check the command output above for details."
        )


def ensure_uv(executable: str, force: bool) -> str:
    current = find_uv(executable)
    if current and not force:
        return current
    install_uv()
    refreshed = find_uv(executable)
    if not refreshed:
        raise RuntimeError(
            "uv was not found on PATH after installation. Make sure the installer "
            "updated PATH or specify --executable explicitly."
        )
    return refreshed


def run_uv_command(uv_executable: str, project_dir: Path, args: list[str]) -> None:
    command = [uv_executable, *args]
    print(f"Running {' '.join(command)} in {project_dir}", file=sys.stderr)
    result = subprocess.run(command, cwd=project_dir, check=False)
    if result.returncode != 0:
        joined = " ".join(command)
        raise RuntimeError(
            f"Command '{joined}' failed with exit code {result.returncode}."
        )


def export_requirements(uv_executable: str, project_dir: Path) -> None:
    lockfile = project_dir / "uv.lock"
    if not lockfile.exists():
        raise RuntimeError(
            f"Lockfile '{lockfile}' is required before exporting requirements."
        )
    commands: list[list[str]] = [
        [
            "export",
            "--format",
            "requirements.txt",
            "--output-file",
            "requirements.txt",
            "--no-dev",
            "--locked",
            "--no-emit-project",
        ],
        [
            "export",
            "--format",
            "requirements.txt",
            "--output-file",
            "requirements-dev.txt",
            "--extra",
            "dev",
            "--locked",
            "--no-emit-project",
        ],
        [
            "export",
            "--format",
            "requirements.txt",
            "--output-file",
            "requirements-compatible.txt",
            "--no-dev",
            "--locked",
            "--no-emit-project",
            "--no-annotate",
            "--no-hashes",
        ],
    ]
    for command in commands:
        run_uv_command(uv_executable, project_dir, command)


def main() -> None:
    args = parse_args()
    try:
        uv_path = ensure_uv(args.executable, args.force)
        print(f"uv executable: {uv_path}")
        if args.sync:
            run_uv_command(uv_path, args.project_dir, ["sync", "--locked", "--frozen"])
        if args.lock or args.export_requirements:
            run_uv_command(uv_path, args.project_dir, ["lock"])
        if args.export_requirements:
            export_requirements(uv_path, args.project_dir)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
