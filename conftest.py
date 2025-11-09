"""Root-level pytest configuration for platform guards."""

from __future__ import annotations

import pytest

from tests._qt_runtime import QT_SKIP_REASON, disable_pytestqt


def pytest_load_initial_conftests(
    early_config: pytest.Config, parser: pytest.Parser, args: list[str]
) -> None:
    """Disable pytest-qt before configuration when prerequisites are missing."""

    _ = parser, args
    if QT_SKIP_REASON is None:
        return

    disable_pytestqt(early_config.pluginmanager)


def pytest_plugin_registered(
    plugin: object, manager: pytest.PytestPluginManager
) -> None:
    """Ensure pytest-qt stays disabled even if auto-loaded by entry points."""

    if QT_SKIP_REASON is None:
        return

    name = getattr(plugin, "__name__", "")
    if name in {"pytestqt", "pytestqt.plugin"}:
        disable_pytestqt(manager)
