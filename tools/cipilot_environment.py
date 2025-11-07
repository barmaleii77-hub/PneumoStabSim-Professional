"""Bootstrap the Qt/PySide6 runtime for Copilot GPT sessions.

The script enforces that GitHub Copilot GPT (or any automated assistant)
operates inside the fully provisioned Qt environment described in the
renovation master plan.  It performs three key tasks:

1. Optionally runs ``uv sync`` to materialise the Python virtual environment.
2. Detects the Qt plugin and QML import paths from PySide6.
3. Emits helper artefacts so shell sessions can source the environment and CI
   bots can record the detected configuration.

Usage examples::

    # First time bootstrap from a plain shell
    python -m tools.cipilot_environment

    # Refresh artefacts from inside ``uv run`` to avoid re-running ``uv sync``
    uv run -- python -m tools.cipilot_environment --skip-uv-sync --probe-mode=python

    # Through the Makefile convenience target
    make cipilot-env
"""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from collections.abc import Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env.cipilot"
DEFAULT_REPORT_FILE = PROJECT_ROOT / "reports" / "quality" / "cipilot_environment.json"
DEFAULTS: dict[str, str] = {
    "QT_QPA_PLATFORM": "offscreen",
    "QT_QUICK_BACKEND": "software",
    "QT_QUICK_CONTROLS_STYLE": "Basic",
}
ORDERED_KEYS: tuple[str, ...] = (
    "QT_QPA_PLATFORM",
    "QT_QUICK_BACKEND",
    "QT_QUICK_CONTROLS_STYLE",
    "QT_PLUGIN_PATH",
    "QML2_IMPORT_PATH",
    "QT_TRANSLATIONS_PATH",
)


@dataclass(slots=True)
class QtMetadata:
    """Version information for the detected Qt runtime."""

    qt_version: str
    pyside6_version: str

    def to_dict(self) -> dict[str, str]:
        return {
            "qt_version": self.qt_version,
            "pyside6_version": self.pyside6_version,
        }


@dataclass(slots=True)
class EnvironmentSnapshot:
    """Container for environment variables and metadata."""

    env_vars: dict[str, str]
    metadata: QtMetadata

    def to_dict(self) -> dict[str, object]:
        return {"env": self.env_vars, "metadata": self.metadata.to_dict()}


def _run_command(command: Iterable[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=PROJECT_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def run_uv_sync() -> bool:
    """Execute ``uv sync`` if the ``uv`` CLI is available."""

    uv_executable = shutil.which("uv")
    if not uv_executable:
        raise RuntimeError(
            "uv executable not found. Install uv or run inside an existing environment."
        )

    result = _run_command([uv_executable, "sync"])
    print(result.stdout, end="")
    if result.returncode != 0:
        raise RuntimeError("uv sync failed with exit code %d" % result.returncode)
    return True


def _probe_via_python() -> EnvironmentSnapshot:
    try:
        import PySide6  # type: ignore
        from PySide6 import QtCore  # type: ignore
        from PySide6.QtCore import QLibraryInfo, qVersion  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on runtime deps
        raise RuntimeError(
            "PySide6 is not available. Run 'uv sync' or install project dependencies."
        ) from exc

    env_vars = dict(DEFAULTS)

    library_enum: Any = getattr(QtCore, "LibraryLocation", None)
    if library_enum is None:
        library_enum = QLibraryInfo.LibraryPath

    def _enum_member(*names: str) -> Any:
        for name in names:
            if hasattr(library_enum, name):
                return getattr(library_enum, name)
        raise AttributeError(
            f"PySide6 QLibraryInfo does not expose any of: {', '.join(names)}"
        )

    def _record(location: Any, key: str) -> None:
        try:
            value = QLibraryInfo.path(location)
        except Exception:  # pragma: no cover - defensive fallback
            value = ""
        if value:
            env_vars[key] = value

    _record(_enum_member("PluginsPath", "Plugins"), "QT_PLUGIN_PATH")
    qml_import_path = _enum_member("QmlImportsPath", "ImportsPath", "QmlImports")
    _record(qml_import_path, "QML2_IMPORT_PATH")
    translations_path = _enum_member("TranslationsPath", "Translations")
    _record(translations_path, "QT_TRANSLATIONS_PATH")

    metadata = QtMetadata(qt_version=qVersion(), pyside6_version=PySide6.__version__)
    return EnvironmentSnapshot(env_vars=env_vars, metadata=metadata)


_UV_PROBE_SCRIPT = """
import json
import os
from PySide6 import QtCore
from PySide6.QtCore import QLibraryInfo, qVersion
import PySide6

library_enum = getattr(QtCore, "LibraryLocation", None)
if library_enum is None:
    library_enum = QLibraryInfo.LibraryPath

def _member(*names: str):
    for name in names:
        if hasattr(library_enum, name):
            return getattr(library_enum, name)
    raise AttributeError(f"Library enum missing candidates: {', '.join(names)}")

def _path(location) -> str:
    try:
        candidate = QLibraryInfo.path(location)
    except Exception:  # pragma: no cover - PySide6 handles fallbacks
        candidate = ""
    return candidate or ""

env = {
    "QT_QPA_PLATFORM": os.environ.get("QT_QPA_PLATFORM", "offscreen"),
    "QT_QUICK_BACKEND": os.environ.get("QT_QUICK_BACKEND", "software"),
    "QT_QUICK_CONTROLS_STYLE": os.environ.get("QT_QUICK_CONTROLS_STYLE", "Basic"),
    "QT_PLUGIN_PATH": _path(_member("PluginsPath", "Plugins")),
    "QML2_IMPORT_PATH": _path(_member("QmlImportsPath", "ImportsPath", "QmlImports")),
    "QT_TRANSLATIONS_PATH": _path(_member("TranslationsPath", "Translations")),
}
metadata = {
    "qt_version": qVersion(),
    "pyside6_version": PySide6.__version__,
}
print(json.dumps({"env": env, "metadata": metadata}, ensure_ascii=False))
""".strip()


def _probe_via_uv() -> EnvironmentSnapshot:
    uv_executable = shutil.which("uv")
    if not uv_executable:
        raise RuntimeError("uv executable not found; cannot probe environment via uv")

    command = [
        uv_executable,
        "run",
        "--",
        "python",
        "-c",
        _UV_PROBE_SCRIPT,
    ]
    result = _run_command(command)
    if result.returncode != 0:
        raise RuntimeError("uv run failed to import PySide6\n" + result.stdout)
    output = result.stdout.strip().splitlines()
    payload = json.loads(output[-1])
    metadata = QtMetadata(
        qt_version=payload["metadata"]["qt_version"],
        pyside6_version=payload["metadata"]["pyside6_version"],
    )
    env_vars = dict(DEFAULTS)
    env_vars.update(payload["env"])
    return EnvironmentSnapshot(env_vars=env_vars, metadata=metadata)


def gather_environment(probe_mode: str = "auto") -> EnvironmentSnapshot:
    """Collect the Qt environment information using the requested strategy."""

    mode = probe_mode.lower()
    if mode not in {"auto", "uv", "python"}:
        raise ValueError("probe_mode must be one of: auto, uv, python")

    if mode == "python":
        return _probe_via_python()

    if mode == "uv":
        return _probe_via_uv()

    try:
        return _probe_via_uv()
    except RuntimeError:
        return _probe_via_python()


def _quote_powershell(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _quote_cmd(value: str) -> str:
    escaped = value.replace("^", "^^").replace("%", "%%").replace("\n", "^\n")
    escaped = escaped.replace('"', '\\"')
    return escaped


def render_shell_exports(env_vars: Mapping[str, str], shell: str = "posix") -> str:
    """Return a shell snippet exporting the supplied variables."""

    shell_key = shell.lower()
    if shell_key not in {"posix", "powershell", "cmd"}:
        raise ValueError("shell must be one of: posix, powershell, cmd")

    lines: list[str]
    if shell_key == "posix":
        lines = [
            "# Qt/PySide6 environment for Copilot GPT",
            "# Source this file before launching assistants or tooling",
        ]
        formatter = lambda key, value: f"export {key}={shlex.quote(value)}"
    elif shell_key == "powershell":
        lines = [
            "# Qt/PySide6 environment for Copilot GPT",
            "# Dot-source this script in PowerShell to update the current session",
        ]
        formatter = lambda key, value: f"$Env:{key} = {_quote_powershell(value)}"
    else:  # cmd
        lines = [
            "@echo off",
            "REM Qt/PySide6 environment for Copilot GPT",
            "REM Run using 'call' to persist changes in the caller session",
        ]
        formatter = lambda key, value: f'set "{key}={_quote_cmd(value)}"'

    for key in ORDERED_KEYS:
        if key in env_vars:
            value = env_vars[key]
            lines.append(formatter(key, value))
    for key in sorted(set(env_vars) - set(ORDERED_KEYS)):
        value = env_vars[key]
        lines.append(formatter(key, value))
    lines.append("")
    return "\n".join(lines)


def write_env_file(path: Path, env_vars: Mapping[str, str], *, shell: str) -> None:
    content = render_shell_exports(env_vars, shell=shell)
    path.write_text(content, encoding="utf-8")


def write_report(
    path: Path,
    snapshot: EnvironmentSnapshot,
    *,
    uv_sync: bool,
    probe_mode: str,
    shell: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "uv_sync_performed": uv_sync,
        "probe_mode": probe_mode,
        "shell_format": shell,
        **snapshot.to_dict(),
    }
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare Qt environment for Copilot GPT"
    )
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_REPORT_FILE)
    parser.add_argument(
        "--skip-uv-sync",
        action="store_true",
        help="Do not run 'uv sync' (useful when already executed inside uv run)",
    )
    parser.add_argument(
        "--probe-mode",
        choices=["auto", "uv", "python"],
        default="auto",
        help="Strategy for gathering environment information",
    )
    parser.add_argument(
        "--shell-format",
        choices=["posix", "powershell", "cmd"],
        default="posix",
        help="Shell syntax to use when writing the environment file",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    uv_sync_performed = False
    if not args.skip_uv_sync:
        try:
            uv_sync_performed = run_uv_sync()
        except RuntimeError as exc:
            print(f"[cipilot-env] WARNING: {exc}")
            print("[cipilot-env] Continuing without uv sync")

    try:
        snapshot = gather_environment(args.probe_mode)
    except RuntimeError as exc:
        print(f"[cipilot-env] ERROR: {exc}")
        return 1

    write_env_file(args.env_file, snapshot.env_vars, shell=args.shell_format)
    write_report(
        args.json_report,
        snapshot,
        uv_sync=uv_sync_performed,
        probe_mode=args.probe_mode,
        shell=args.shell_format,
    )

    try:
        env_display = args.env_file.relative_to(PROJECT_ROOT)
    except ValueError:
        env_display = args.env_file
    try:
        report_display = args.json_report.relative_to(PROJECT_ROOT)
    except ValueError:
        report_display = args.json_report

    env_display_str = str(env_display)
    report_display_str = str(report_display)

    instruction: str
    if args.shell_format == "posix":
        instruction = f"source {shlex.quote(env_display_str)}"
    elif args.shell_format == "powershell":
        instruction = f". {_quote_powershell(env_display_str)}"
    else:
        instruction = f'call "{env_display_str}"'

    print("[cipilot-env] Environment file written to", env_display_str)
    print("[cipilot-env] JSON report written to", report_display_str)
    print(
        "[cipilot-env] Apply the environment via '"
        f"{instruction}' before invoking Copilot GPT"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
