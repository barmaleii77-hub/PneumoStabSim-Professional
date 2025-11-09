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
        message = textwrap.dedent(
            """
            Qt runtime bindings are required for cross-platform tests but could
            not be imported.

            Missing modules:
            {modules}

            Ensure the development dependencies are installed with one of the
            following commands (run from the repository root):

              • `uv sync --extra dev`
              • `python -m pip install -r requirements-dev.txt`

            After installing the dependencies rerun
            `python -m tools.cross_platform_test_prep --run-tests` to verify the
            environment.
            """
        ).strip().format(modules="\n".join(f"  - {line}" for line in errors))

        pytest.fail(message)

    if QT_SKIP_REASON is not None:
        system = platform.system()
        instructions = textwrap.dedent(
            """
            Qt runtime prerequisites are not satisfied for {system}. {reason}

            Execute `python -m tools.cross_platform_test_prep --run-tests` to
            install the required system libraries and retry the suite.
            """
        ).strip().format(system=system, reason=QT_SKIP_REASON)

        pytest.fail(instructions)


__all__ = ["ensure_qt_runtime"]
