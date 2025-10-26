# -*- coding: utf-8 -*-
"""Environment diagnostics helpers used before importing Qt."""

from __future__ import annotations

import os
import platform
import sys
from ctypes import CDLL
from ctypes.util import find_library
from dataclasses import dataclass, field
from typing import Iterable, List, Literal

from src.bootstrap.dependency_config import (
    DependencyConfigError,
    DependencyVariant,
    match_dependency_error,
    resolve_dependency_variant,
)


STATUS_ICON: dict[str, str] = {"ok": "✅", "warning": "⚠️", "error": "❌"}
STATUS_LABEL: dict[str, str] = {"ok": "OK", "warning": "WARN", "error": "ERROR"}


@dataclass
class CheckResult:
    """Represents a single environment check outcome."""

    name: str
    status: Literal["ok", "warning", "error"]
    detail: str | None = None
    hint: str | None = None

    def _icon(self) -> str:
        return STATUS_ICON.get(self.status, "❔")

    def _label(self) -> str:
        return STATUS_LABEL.get(self.status, self.status.upper())

    def as_markdown(self) -> str:
        lines = [f"- {self._icon()} **{self.name}**"]
        if self.detail:
            lines.append(f"  - {self.detail}")
        if self.hint:
            lines.append(f"  - 💡 {self.hint}")
        return "\n".join(lines)


@dataclass
class EnvironmentReport:
    """Aggregated environment check results."""

    python_version: str
    platform: str
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def is_successful(self) -> bool:
        return all(check.status != "error" for check in self.checks)

    def to_markdown(self) -> str:
        lines = [
            "# PneumoStabSim Environment Setup Report",
            "",
            f"- Python: `{self.python_version}`",
            f"- Platform: `{self.platform}`",
            "",
            "## Checks",
            "",
        ]

        for check in self.checks:
            lines.append(check.as_markdown())
        lines.append("")

        summary = (
            "All mandatory checks passed." if self.is_successful else "Issues detected."
        )
        lines.append(f"**Summary:** {summary}")
        return "\n".join(lines)


def _check_python_version() -> CheckResult:
    current_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    minimum_version = (3, 11)
    if sys.version_info >= minimum_version:
        return CheckResult(
            name="Python version",
            status="ok",
            detail=f"Running on Python {current_version}",
        )

    required = ".".join(str(part) for part in minimum_version)
    return CheckResult(
        name="Python version",
        status="error",
        detail=f"Detected Python {current_version}",
        hint=f"Upgrade to Python {required} or newer.",
    )


def _opengl_missing_detail(variant: DependencyVariant) -> str:
    message = variant.missing_message
    if message:
        return message
    return f"System library '{variant.human_name}' not found."


def _is_headless_environment() -> bool:
    """Return ``True`` when running without a graphical display server."""

    platform_hint = os.environ.get("QT_QPA_PLATFORM", "").lower()
    if platform_hint in {"offscreen", "minimal", "minimalgl"}:
        return True

    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        return False

    return sys.platform.startswith(("linux", "freebsd", "openbsd"))


def _check_opengl_runtime() -> CheckResult:
    try:
        variant = resolve_dependency_variant("opengl_runtime")
    except DependencyConfigError as exc:
        return CheckResult(
            name="OpenGL runtime",
            status="error",
            detail=str(exc),
        )

    resolved = find_library(variant.library_name)
    if not resolved:
        severity: Literal["warning", "error"]
        severity = "warning" if _is_headless_environment() else "error"
        detail = _opengl_missing_detail(variant)
        if severity == "warning":
            detail = (
                f"{detail} Headless environment detected; skipping strict requirement."
            )
        hint = (
            variant.install_hint
            or "Install a system OpenGL runtime (e.g. 'apt-get install -y libgl1') when running with a display server."
        )
        return CheckResult(
            name="OpenGL runtime",
            status=severity,
            detail=detail,
            hint=hint,
        )

    try:
        CDLL(resolved)
    except OSError as exc:
        severity = "warning" if _is_headless_environment() else "error"
        detail = f"Failed to load '{resolved}': {exc}"
        if severity == "warning":
            detail += " (headless environment detected)"
        return CheckResult(
            name="OpenGL runtime",
            status=severity,
            detail=detail,
            hint=variant.install_hint,
        )

    return CheckResult(
        name="OpenGL runtime",
        status="ok",
        detail=f"Found '{resolved}'",
    )


def _check_pyside6() -> CheckResult:
    try:
        from PySide6 import __version__ as pyside_version  # type: ignore
        from PySide6.QtCore import qVersion  # noqa: F401  # ensure Qt is accessible

        return CheckResult(
            name="PySide6 import",
            status="ok",
            detail=f"PySide6 {pyside_version} available",
        )
    except ImportError as exc:
        message = str(exc)
        hint = None

        variant = match_dependency_error("opengl_runtime", message)
        if variant is not None:
            hint = variant.install_hint
        elif "libEGL" in message:
            hint = "Install system EGL runtime (e.g. 'apt-get install -y libegl1')."
        elif "PySide6" in message:
            hint = "Install dependencies via 'pip install -r requirements.txt'."

        return CheckResult(
            name="PySide6 import",
            status="error",
            detail=message,
            hint=hint,
        )


def generate_environment_report() -> EnvironmentReport:
    report = EnvironmentReport(
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        platform=platform.platform(),
    )

    checks: Iterable[CheckResult] = (
        _check_python_version(),
        _check_opengl_runtime(),
        _check_pyside6(),
    )

    report.checks.extend(checks)
    return report


def render_console_report(report: EnvironmentReport) -> str:
    lines = [
        "=" * 60,
        "PneumoStabSim Environment Diagnostics",
        "=" * 60,
        f"Python: {report.python_version}",
        f"Platform: {report.platform}",
        "",
    ]

    for check in report.checks:
        status = check._label()
        lines.append(f"[{status}] {check.name}")
        if check.detail:
            lines.append(f"    {check.detail}")
        if check.hint:
            lines.append(f"    Hint: {check.hint}")
        lines.append("")

    summary = "All checks passed." if report.is_successful else "Issues detected."
    lines.append(summary)
    return "\n".join(lines)
