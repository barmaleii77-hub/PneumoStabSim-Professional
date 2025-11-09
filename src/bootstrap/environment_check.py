"""Runtime environment diagnostics for PneumoStabSim Professional."""

from __future__ import annotations

import os
import platform
import sys
from ctypes.util import find_library
from dataclasses import dataclass
from collections.abc import Iterable, Sequence

from src.bootstrap.dependency_config import (
    DependencyConfigError,
    DependencyVariant,
    resolve_dependency_variant,
)


@dataclass(slots=True)
class CheckResult:
    """Represents the outcome of a single environment probe."""

    name: str
    status: str
    detail: str | None = None

    @property
    def is_error(self) -> bool:
        return self.status.lower() == "error"

    @property
    def is_warning(self) -> bool:
        return self.status.lower() == "warning"


@dataclass(slots=True)
class EnvironmentReport:
    """Aggregated result of all runtime environment probes."""

    python_version: str
    platform: str
    qt_version: str | None = None
    checks: Sequence[CheckResult] = ()

    @property
    def is_successful(self) -> bool:
        return all(not check.is_error for check in self.checks)

    def to_markdown(self) -> str:
        """Render the report as a human-readable Markdown document."""

        lines = [
            "# PneumoStabSim Environment Report",
            "",
            f"- Python: `{self.python_version}`",
            f"- Platform: `{self.platform}`",
            f"- Qt: `{self.qt_version or 'unavailable'}`",
            "",
            "## Checks",
            "",
        ]

        if not self.checks:
            lines.append("- No checks were executed.")
        else:
            for check in self.checks:
                detail_suffix = f" — {check.detail}" if check.detail else ""
                lines.append(
                    f"- **{check.status.upper()}** {check.name}{detail_suffix}"
                )

        return "\n".join(lines)


def _python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _platform_label() -> str:
    return f"{platform.system()} {platform.release()}"


def _detect_qt_version() -> str | None:
    try:
        from PySide6.QtCore import qVersion  # type: ignore
    except Exception:
        return None

    try:
        return qVersion()
    except Exception:
        return None


def _candidate_names(variant: DependencyVariant) -> tuple[str, ...]:
    candidates: list[str] = []

    def _push(value: str | None) -> None:
        if not value:
            return
        if value not in candidates:
            candidates.append(value)

    _push(getattr(variant, "library_name", None))
    _push(getattr(variant, "human_name", None))
    for marker in getattr(variant, "error_markers", ()):
        _push(marker)

    library_name = getattr(variant, "library_name", "")
    if library_name and not library_name.startswith("lib"):
        _push(f"lib{library_name}.so.1")

    return tuple(candidates)


def _headless_environment() -> bool:
    platform_hint = os.environ.get("QT_QPA_PLATFORM", "").strip().lower()
    if platform_hint in {"offscreen", "minimal"}:
        return True
    display_present = bool(os.environ.get("DISPLAY")) or bool(
        os.environ.get("WAYLAND_DISPLAY")
    )
    return not display_present


def _missing_runtime_message(variant: DependencyVariant) -> str:
    if getattr(variant, "missing_message", None):
        return str(variant.missing_message)
    human_name = getattr(variant, "human_name", None) or getattr(
        variant, "library_name", "OpenGL runtime"
    )
    return f"Required OpenGL runtime ({human_name}) is missing."


def _install_hint(variant: DependencyVariant) -> str | None:
    hint = getattr(variant, "install_hint", None)
    if isinstance(hint, str) and hint.strip():
        return hint
    return None


def _check_opengl_runtime() -> CheckResult:
    name = "OpenGL runtime"

    try:
        variant = resolve_dependency_variant("opengl_runtime")
    except DependencyConfigError as exc:
        return CheckResult(
            name=name,
            status="warning",
            detail=f"Unable to resolve opengl_runtime dependency: {exc}",
        )

    candidates = _candidate_names(variant)
    for candidate in candidates:
        resolved = find_library(candidate)
        if resolved:
            return CheckResult(
                name=name,
                status="ok",
                detail=f"OpenGL runtime '{resolved}' is available.",
            )

    headless = _headless_environment()
    status = "warning" if headless else "error"

    parts: list[str] = [_missing_runtime_message(variant)]
    hint = _install_hint(variant)
    if hint:
        parts.append(hint)
    if headless:
        parts.append(
            "Headless environment detected; treating missing runtime as a warning."
        )

    return CheckResult(
        name=name,
        status=status,
        detail=" ".join(parts),
    )


def collect_env() -> EnvironmentReport:
    checks: Iterable[CheckResult] = (_check_opengl_runtime(),)
    return EnvironmentReport(
        python_version=_python_version(),
        platform=_platform_label(),
        qt_version=_detect_qt_version(),
        checks=tuple(checks),
    )


def generate_environment_report() -> EnvironmentReport:
    """Generate a full environment report for bootstrap checks."""

    return collect_env()


def render_console_report(report: EnvironmentReport) -> str:
    """Render a console-friendly string representation of the report."""

    lines = [
        "ENVIRONMENT CHECK",
        f"Python: {report.python_version}",
        f"Platform: {report.platform}",
        f"Qt: {report.qt_version or 'unavailable'}",
        "",
    ]

    for check in report.checks:
        detail_suffix = f": {check.detail}" if check.detail else ""
        lines.append(f"[{check.status.upper()}] {check.name}{detail_suffix}")

    return "\n".join(lines)


def main() -> int:
    report = generate_environment_report()
    print(render_console_report(report))
    return 0 if report.is_successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
