"""Qt runtime helpers for cross-platform test execution."""

from __future__ import annotations

import importlib
import platform
import textwrap
from typing import Final

import pytest

from tests._qt_runtime import QT_SKIP_REASON

_REQUIRED_MODULES: Final[tuple[str, ...]] = (
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtQml",
)


def _format_dependency_message(header: str, details: list[str]) -> str:
    formatted = "\n".join(f"  - {line}" for line in details)
    if details:
        missing_section = f"\n\nMissing modules:\n{formatted}\n"
    else:
        missing_section = "\n"
    return (
        textwrap.dedent(
            """
    {header}{missing}
    Execute `python -m tools.cross_platform_test_prep --use-uv --run-tests` to
    install the required Python and system dependencies before retrying.
    """
        )
        .strip()
        .format(header=header, missing=missing_section)
    )


def _fail_missing_runtime(reason: str, missing: list[str]) -> None:
    instructions = _format_dependency_message(reason, missing)
    pytest.fail(instructions)


def ensure_qt_runtime() -> None:
    """Validate that Qt bindings and runtime prerequisites are present.

    The full test suite exercises QML and Qt Quick integration paths on both
    Linux and Windows. Missing bindings now result in a hard failure so that the
    cross-platform matrix can no longer silently skip Qt-dependent suites.
    """

    errors: list[str] = []

    for module_name in _REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - depends on host platform
            errors.append(f"{module_name}: {exc}")

    if errors:
        reason = QT_SKIP_REASON or "Qt runtime bindings are missing"
        _fail_missing_runtime(reason, errors)

    if QT_SKIP_REASON is not None:
        system = platform.system()
        header = (
            f"Qt runtime prerequisites are not satisfied for {system}. {QT_SKIP_REASON}"
        )
        _fail_missing_runtime(header, [])


def require_qt_modules(*module_names: str):
    """Import the requested Qt modules and fail with guidance if unavailable."""

    loaded = []
    errors: list[str] = []

    for module_name in module_names:
        try:
            loaded.append(importlib.import_module(module_name))
        except Exception as exc:  # pragma: no cover - platform dependent
            errors.append(f"{module_name}: {exc}")

    if errors:
        _fail_missing_runtime("Required Qt modules are missing", errors)

    return tuple(loaded)


def enforce_importorskip(module_name: str, *, reason: str | None = None):
    """Fail the test suite when a requested dependency is unavailable.

    This replaces ``pytest.importorskip`` semantics with a hard failure so that
    missing Qt bindings or plugins are surfaced immediately instead of being
    silently acknowledged as skips.
    """

    missing: list[str] = []

    spec = importlib.util.find_spec(module_name)
    if spec is None:
        missing.append(f"{module_name}: module not found")
    else:
        try:
            return importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - platform dependent
            missing.append(f"{module_name}: {exc}")

    header = reason or f"{module_name} is required for Qt-dependent tests"
    _fail_missing_runtime(header, missing)


def require_pytest_qt() -> None:
    """Ensure the pytest-qt plugin is importable before running Qt suites."""

    enforce_importorskip("pytestqt.plugin", reason="pytest-qt plugin is required")


__all__ = [
    "ensure_qt_runtime",
    "enforce_importorskip",
    "require_pytest_qt",
    "require_qt_modules",
]
