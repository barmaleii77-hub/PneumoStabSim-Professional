# -*- coding: utf-8 -*-
"""Environment diagnostics helpers used before importing Qt."""

from __future__ import annotations

import platform
import sys
from ctypes import CDLL
from ctypes.util import find_library
from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass
class CheckResult:
    """Represents a single environment check outcome."""

    name: str
    status: str
    detail: str | None = None
    hint: str | None = None

    def as_markdown(self) -> str:
        icon = "✅" if self.status == "ok" else "❌"
        lines = [f"- {icon} **{self.name}**"]
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
        return all(check.status == "ok" for check in self.checks)

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


def _check_opengl_runtime() -> CheckResult:
    if sys.platform.startswith("win"):
        library_name = "opengl32"
        human_name = "opengl32.dll"
    elif sys.platform == "darwin":
        library_name = "OpenGL"
        human_name = "OpenGL.framework"
    else:
        library_name = "GL"
        human_name = "libGL.so.1"

    resolved = find_library(library_name)
    if not resolved:
        return CheckResult(
            name="OpenGL runtime",
            status="error",
            detail=f"System library '{human_name}' not found.",
            hint=_opengl_hint(),
        )

    try:
        CDLL(resolved)
    except OSError as exc:
        return CheckResult(
            name="OpenGL runtime",
            status="error",
            detail=f"Failed to load '{resolved}': {exc}",
            hint=_opengl_hint(),
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
        hint = None
        message = str(exc)
        if "libGL.so.1" in message or "opengl32" in message.lower():
            hint = _opengl_hint()
        elif "libEGL" in message:
            hint = "Install system EGL runtime (e.g. 'apt-get install -y libegl1')."
        elif "PySide6" in message:
            hint = "Install dependencies via 'pip install -r requirements.txt'."

        return CheckResult(
            name="PySide6 import",
            status="error",
            detail=f"{message}",
            hint=hint,
        )


def _opengl_hint() -> str:
    if sys.platform.startswith("win"):
        return (
            "Install the latest GPU drivers or enable OpenGL compatibility components."
        )
    if sys.platform == "darwin":
        return "Ensure the Xcode command line tools are installed for OpenGL support."
    return "Install a Mesa/OpenGL package, e.g. 'apt-get install -y libgl1'."


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
        status = "OK" if check.status == "ok" else "ERROR"
        lines.append(f"[{status}] {check.name}")
        if check.detail:
            lines.append(f"    {check.detail}")
        if check.hint:
            lines.append(f"    Hint: {check.hint}")
        lines.append("")

    summary = "All checks passed." if report.is_successful else "Issues detected."
    lines.append(summary)
    return "\n".join(lines)
