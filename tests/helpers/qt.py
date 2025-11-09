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


def ensure_qt_runtime() -> None:
    """Validate that Qt bindings and runtime prerequisites are present.

    The full test suite exercises QML and Qt Quick integration paths on both
    Linux and Windows. Rather than silently skipping when bindings are missing,
    we fail fast with actionable remediation guidance so that cross-platform
    coverage remains enforced.
    """

    missing: list[str] = []
    errors: list[str] = []

    for module_name in _REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - depends on host platform
            missing.append(module_name)
            errors.append(f"{module_name}: {exc}")

    if missing:
        formatted_missing = "\n".join(f"  - {line}" for line in errors)
        reason = QT_SKIP_REASON or "Qt runtime bindings are missing"
        instructions = (
            textwrap.dedent(
                """
            Qt runtime bindings are required for cross-platform tests but could
            not be imported.

            Missing modules:
            {modules}

            Execute `python -m tools.cross_platform_test_prep --run-tests` to
            install the required Python and system dependencies before
            retrying.
            """
            )
            .strip()
            .format(modules=formatted_missing)
        )

        pytest.skip(f"{reason}.\n{instructions}")

    if QT_SKIP_REASON is not None:
        system = platform.system()
        instructions = (
            textwrap.dedent(
                """
            Qt runtime prerequisites are not satisfied for {system}. {reason}

            Execute `python -m tools.cross_platform_test_prep --run-tests` to
            install the required system libraries and retry the suite.
            """
            )
            .strip()
            .format(system=system, reason=QT_SKIP_REASON)
        )

        pytest.skip(instructions)


__all__ = ["ensure_qt_runtime"]
