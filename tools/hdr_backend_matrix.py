"""HDR backend verification matrix for cross-platform testing.

This module codifies the expected rendering backend configuration for
Windows, Linux, and macOS so that QA can reproduce HDR/dithering test runs.
It is intentionally lightweight and does not launch the Qt application;
instead it validates the repository state (assets, configuration, Qt
version) and prints a checklist describing how to execute the manual smoke
passes on each platform.

The script is designed to run inside automation as well as on developer
workstations.  When executed with ``--check`` it will exit with a non-zero
status if required assets are missing or the Qt version does not satisfy the
minimum requirements.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

import structlog

LOGGER = structlog.get_logger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
# Базовый «эталонный» HDR-файл. В некоторых окружениях его может не быть,
# но допустимо наличие альтернатив (EXR / другие HDR). Поэтому ниже реализована
# мягкая проверка с fallback.
HDR_PRIMARY = REPO_ROOT / "assets" / "hdr" / "studio.hdr"
HDR_ASSETS: tuple[Path, ...] = (
    HDR_PRIMARY,
    REPO_ROOT / "assets" / "hdr" / "README.md",
)
SETTINGS_FILE = REPO_ROOT / "config" / "baseline" / "app_settings.json"
QUALITY_TAB = REPO_ROOT / "src" / "ui" / "panels" / "graphics" / "quality_tab.py"

DITHERING_SENTINELS: tuple[str, ...] = (
    "dithering_check = LoggingCheckBox",
    '"Dithering (Qt 6.10+)"',
    '"dithering.enabled"',
)


@dataclass(frozen=True)
class BackendPlan:
    """Describe how HDR tests should run on a specific platform."""

    platform: str
    primary_backend: str
    description: str
    env: Mapping[str, str] = field(default_factory=dict)
    optional_env: Mapping[str, str] = field(default_factory=dict)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def render(self) -> str:
        lines = [f"Platform: {self.platform}"]
        lines.append(f"  Primary backend: {self.primary_backend}")
        lines.append(f"  Summary: {self.description}")
        if self.env:
            lines.append("  Environment variables:")
            for key, value in self.env.items():
                lines.append(f"    - {key}={value}")
        if self.optional_env:
            lines.append("  Optional environment:")
            for key, value in self.optional_env.items():
                lines.append(f"    - {key}={value}")
        if self.notes:
            lines.append("  Notes:")
            for note in self.notes:
                lines.append(f"    • {note}")
        return "\n".join(lines)


def _detect_platform(value: str | None) -> str:
    if value and value != "auto":
        normalized = value.lower()
        if normalized in {"windows", "win", "nt"}:
            return "windows"
        if normalized in {"linux", "posix"}:
            return "linux"
        if normalized in {"mac", "macos", "darwin"}:
            return "macos"
        raise ValueError(f"Unknown platform override: {value}")
    current = platform.system().lower()
    if current.startswith("win"):
        return "windows"
    if current == "darwin":
        return "macos"
    return "linux"


def _qt_version() -> tuple[int, int, int] | None:
    try:
        from PySide6 import QtCore
    except Exception:  # pragma: no cover - import probe only
        LOGGER.warning("PySide6 unavailable; Qt version cannot be determined")
        return None
    version_str = QtCore.qVersion()
    try:
        parts = tuple(int(part) for part in version_str.split("."))
    except ValueError:  # pragma: no cover - defensive guard
        LOGGER.warning("Unexpected Qt version string", version=version_str)
        return None
    if len(parts) == 2:
        parts = parts + (0,)
    return parts[:3]


def _supports_dithering(version: tuple[int, int, int] | None) -> bool:
    if version is None:
        return False
    major, minor, _ = version
    return major > 6 or (major == 6 and minor >= 10)


def compute_backend_plan(target: str | None = None) -> BackendPlan:
    platform_key = _detect_platform(target)
    if platform_key == "windows":
        return BackendPlan(
            platform="Windows",
            primary_backend="Direct3D 11",
            description="RHI defaults to Direct3D; force D3D11 for HDR validation",
            env={"QSG_RHI_BACKEND": "d3d11"},
            notes=(
                "Launch via PowerShell profile (run_app.ps1) after executing "
                "scripts/setup_environment.ps1",
                "Toggle Graphics → Quality → 'Dithering (Qt 6.10+)' to validate UI binding",
            ),
        )
    if platform_key == "macos":
        return BackendPlan(
            platform="macOS",
            primary_backend="Metal",
            description="Metal RHI validates shader compilation and HDR tonemapping",
            env={"QSG_RHI_BACKEND": "metal"},
            notes=(
                "Use the universal_f5.py launcher to ensure Metal surfaces are initialised",
                "Observe console for shader compilation warnings; expect none",
            ),
        )
    return BackendPlan(
        platform="Linux",
        primary_backend="OpenGL 4.5 Core",
        description="Force OpenGL core profile with HDR textures and dithering toggles",
        env={
            "QSG_RHI_BACKEND": "opengl",
            "QSG_OPENGL_VERSION": "4.5",
            "QT_OPENGL_PROFILE": "core",
        },
        optional_env={"QSG_OPENGL_VERSION_FALLBACK": "3.3"},
        notes=(
            "Set fallback variable only when testing legacy GPUs that lack GL 4.5",
            "Invoke make cross-platform-test after exporting the environment",
        ),
    )


def _check_hdr_assets(files: Iterable[Path]) -> list[Path]:
    """Return missing mandatory assets.

    Допускаем отсутствие основного HDR-файла, если в каталоге присутствует
    хотя бы один *.hdr или *.exr файл (т.е. есть валидные альтернативы).
    """
    missing: list[Path] = []
    for candidate in files:
        if not candidate.exists():
            missing.append(candidate)

    # Смягчённая логика: если отсутствует именно HDR_PRIMARY, но в папке есть другие HDR/EXR — не считаем критичной ошибкой.
    if HDR_PRIMARY in missing:
        hdr_dir = HDR_PRIMARY.parent
        if hdr_dir.exists():
            alternatives = list(hdr_dir.glob("*.hdr")) + list(hdr_dir.glob("*.exr"))
            if alternatives:
                LOGGER.info(
                    "Primary HDR missing; acceptable alternatives detected",
                    primary=str(HDR_PRIMARY),
                    count=len(alternatives),
                )
                # Удаляем primary из списка критичных пропусков
                missing = [m for m in missing if m != HDR_PRIMARY]
    return missing


def _check_dithering_control(path: Path) -> list[str]:
    if not path.exists():
        return [f"Missing graphics quality panel source: {path}"]
    text = path.read_text(encoding="utf-8")
    missing_tokens = [token for token in DITHERING_SENTINELS if token not in text]
    return [f"Dithering marker not found: {token}" for token in missing_tokens]


def _load_settings() -> dict[str, object] | None:
    if not SETTINGS_FILE.exists():
        LOGGER.error("Settings baseline missing", file=str(SETTINGS_FILE))
        return None
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        LOGGER.error("Failed to parse baseline settings", error=str(exc))
        return None


def _check_settings_for_dithering(payload: dict[str, object] | None) -> list[str]:
    if payload is None:
        return ["Settings payload unavailable"]
    issues: list[str] = []
    try:
        quality = payload["current"]["graphics"]["quality"]  # type: ignore[index]
    except (KeyError, TypeError):
        issues.append("graphics.quality section missing from baseline settings")
    else:
        if not isinstance(quality, dict) or "dithering" not in quality:
            issues.append("graphics.quality.dithering missing from baseline settings")

    try:
        environment = payload["current"]["graphics"]["environment"]  # type: ignore[index]
    except (KeyError, TypeError):
        issues.append("graphics.environment section missing from baseline settings")
    else:
        if not isinstance(environment, dict) or "ao_dither" not in environment:
            issues.append(
                "graphics.environment.ao_dither missing from baseline settings"
            )
    return issues


def run_checks(target: str | None, fail_on_error: bool) -> int:
    plan = compute_backend_plan(target)
    LOGGER.info(
        "Selected backend plan", platform=plan.platform, backend=plan.primary_backend
    )

    missing_assets = _check_hdr_assets(HDR_ASSETS)
    if missing_assets:
        for path in missing_assets:
            LOGGER.error("HDR asset missing", path=str(path))
    else:
        LOGGER.info("HDR assets OK (or acceptable alternatives detected)")

    issues: list[str] = []
    issues.extend(_check_dithering_control(QUALITY_TAB))

    settings_payload = _load_settings()
    settings_issues = _check_settings_for_dithering(settings_payload)
    if settings_issues:
        issues.extend(settings_issues)
    else:
        LOGGER.info("Baseline settings expose dithering toggles")

    qt_version = _qt_version()
    if qt_version:
        LOGGER.info(
            "Detected Qt version", version=".".join(str(part) for part in qt_version)
        )
    else:
        issues.append("Unable to detect Qt version; ensure PySide6 is installed")

    if qt_version and not _supports_dithering(qt_version):
        issues.append("Qt version does not support ditheringEnabled (requires >= 6.10)")

    for note in issues:
        LOGGER.warning("Validation issue", detail=note)

    print(plan.render())

    if fail_on_error and (missing_assets or issues):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--platform",
        default="auto",
        help="Override detected platform (windows, linux, macOS, auto)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with non-zero status when validation issues are detected",
    )
    args = parser.parse_args(argv)
    return run_checks(args.platform, args.check)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    sys.exit(main())
