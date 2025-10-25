#!/usr/bin/env python3
"""Bootstrap VS Code configuration for PneumoStabSim Professional."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parent
VSCODE_DIR = PROJECT_ROOT / ".vscode"
RECOMMENDED_EXTENSIONS = [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.debugpy",
    "charliermarsh.ruff",
    "ms-toolsai.jupyter",
    "ms-vscode.cpptools",
    "ms-vscode.cmake-tools",
    "ms-vscode.powershell",
    "qt.io.qt-vscode",
    "tamasfe.even-better-toml",
    "github.copilot",
    "github.copilot-chat",
]
REQUIRED_JSON = [
    PROJECT_ROOT / "PneumoStabSim.code-workspace",
    VSCODE_DIR / "settings.json",
    VSCODE_DIR / "launch.json",
    VSCODE_DIR / "tasks.json",
    VSCODE_DIR / "extensions.json",
]
OBSOLETE_PATTERNS = ("*.bak", "*.old", "*~")
PYTHON_EXTRA_PATHS = [
    "${workspaceFolder}/src",
    "${workspaceFolder}/tests",
    "${workspaceFolder}/tools",
]


@dataclass
class BootstrapReport:
    """Accumulates status information for the bootstrap process."""

    success: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def ok(self) -> bool:
        return not self.errors

    def log_success(self, message: str) -> None:
        print(f"✅ {message}")
        self.success.append(message)

    def log_warning(self, message: str) -> None:
        print(f"⚠️  {message}")
        self.warnings.append(message)

    def log_error(self, message: str) -> None:
        print(f"❌ {message}")
        self.errors.append(message)

    def summary(self) -> None:
        print("\n===== VS Code bootstrap summary =====")
        print(f"Success: {len(self.success)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Errors: {len(self.errors)}")
        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f" • {warning}")
        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f" • {error}")


class VSCodeBootstrap:
    """Orchestrates validation and lightweight setup for VS Code."""

    def __init__(self) -> None:
        self.report = BootstrapReport()

    # ------------------------------------------------------------------
    # Filesystem helpers
    # ------------------------------------------------------------------
    def ensure_vscode_directory(self) -> None:
        VSCODE_DIR.mkdir(exist_ok=True)
        self.report.log_success(".vscode directory is ready")

    def clean_obsolete_files(self) -> None:
        removed: list[Path] = []
        for pattern in OBSOLETE_PATTERNS:
            for candidate in VSCODE_DIR.glob(pattern):
                try:
                    candidate.unlink()
                    removed.append(candidate)
                except OSError as exc:
                    self.report.log_warning(f"Cannot remove obsolete file {candidate.name}: {exc}")
        if removed:
            self.report.log_success(
                "Removed obsolete files: " + ", ".join(item.name for item in removed)
            )

    # ------------------------------------------------------------------
    # uv helpers
    # ------------------------------------------------------------------
    def ensure_uv_available(self) -> str | None:
        uv_path = shutil.which("uv")
        if not uv_path:
            self.report.log_warning(
                "uv executable not found. Install it via 'python -m pip install uv' or run "
                "python scripts/bootstrap_uv.py"
            )
            return None
        self.report.log_success(f"uv detected at {uv_path}")
        return uv_path

    def run_uv_sync(self, uv_path: str | None) -> None:
        if not uv_path:
            return
        try:
            subprocess.run([uv_path, "sync"], check=True, cwd=PROJECT_ROOT)
            self.report.log_success("uv sync completed successfully")
        except subprocess.CalledProcessError as exc:
            self.report.log_error(f"uv sync failed with exit code {exc.returncode}")
        except OSError as exc:
            self.report.log_error(f"Failed to execute uv sync: {exc}")

    # ------------------------------------------------------------------
    # Configuration verification
    # ------------------------------------------------------------------
    def validate_json_files(self, paths: Iterable[Path]) -> None:
        for path in paths:
            if not path.exists():
                self.report.log_error(f"Required configuration file is missing: {path.relative_to(PROJECT_ROOT)}")
                continue
            try:
                json.loads(path.read_text(encoding="utf-8"))
                self.report.log_success(f"Validated JSON file: {path.relative_to(PROJECT_ROOT)}")
            except json.JSONDecodeError as exc:
                self.report.log_error(
                    f"Invalid JSON in {path.relative_to(PROJECT_ROOT)} (line {exc.lineno}, col {exc.colno})"
                )

    def ensure_extension_recommendations(self) -> None:
        extensions_file = VSCODE_DIR / "extensions.json"
        existing: dict[str, object] = {}
        if extensions_file.exists():
            try:
                existing = json.loads(extensions_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = {}
        recommendations = sorted(set(RECOMMENDED_EXTENSIONS))
        if existing.get("recommendations") != recommendations:
            extensions_file.write_text(
                json.dumps({"recommendations": recommendations}, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            self.report.log_success("Updated VS Code extension recommendations")
        else:
            self.report.log_success("VS Code extension recommendations already up to date")

    def ensure_python_import_hints(self) -> None:
        """Keep VS Code aware of the src/tests/tools package roots."""

        self._update_settings_file(VSCODE_DIR / "settings.json")
        self._update_settings_file(
            PROJECT_ROOT / "PneumoStabSim.code-workspace", nested_key="settings"
        )

    def _update_settings_file(self, path: Path, *, nested_key: str | None = None) -> None:
        if not path.exists():
            self.report.log_warning(
                f"Cannot update Python paths; file missing: {path.relative_to(PROJECT_ROOT)}"
            )
            return

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.report.log_error(
                f"Cannot update {path.relative_to(PROJECT_ROOT)} due to invalid JSON (line {exc.lineno}, col {exc.colno})"
            )
            return

        target: dict[str, object]
        if nested_key is None:
            if not isinstance(data, dict):
                self.report.log_error(
                    f"Expected object at root of {path.relative_to(PROJECT_ROOT)} to update Python paths"
                )
                return
            target = data
        else:
            if not isinstance(data, dict):
                self.report.log_error(
                    f"Expected object at root of {path.relative_to(PROJECT_ROOT)} to access '{nested_key}'"
                )
                return
            nested = data.setdefault(nested_key, {})
            if not isinstance(nested, dict):
                self.report.log_error(
                    f"Expected '{nested_key}' to be an object in {path.relative_to(PROJECT_ROOT)}"
                )
                return
            target = nested

        changed = self._ensure_python_paths(target)
        if changed:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            self.report.log_success(
                f"Updated Python import paths in {path.relative_to(PROJECT_ROOT)}"
            )
        else:
            self.report.log_success(
                f"Python import paths already set in {path.relative_to(PROJECT_ROOT)}"
            )

    def _ensure_python_paths(self, container: dict[str, object]) -> bool:
        changed = False
        for key in ("python.analysis.extraPaths", "python.autoComplete.extraPaths"):
            existing = container.get(key)
            if isinstance(existing, list):
                merged = list(existing)
                for candidate in PYTHON_EXTRA_PATHS:
                    if candidate not in merged:
                        merged.append(candidate)
            else:
                merged = list(PYTHON_EXTRA_PATHS)
            if existing != merged:
                container[key] = merged
                changed = True
        return changed

    # ------------------------------------------------------------------
    def run(self) -> None:
        print("===== PneumoStabSim Professional :: VS Code bootstrap =====")
        self.ensure_vscode_directory()
        self.clean_obsolete_files()
        uv_path = self.ensure_uv_available()
        self.run_uv_sync(uv_path)
        self.validate_json_files(REQUIRED_JSON)
        self.ensure_extension_recommendations()
        self.ensure_python_import_hints()
        self.report.summary()
        if not self.report.ok():
            sys.exit(1)


def main() -> None:
    try:
        VSCodeBootstrap().run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
