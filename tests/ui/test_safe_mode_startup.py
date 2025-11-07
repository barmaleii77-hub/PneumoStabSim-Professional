"""Regression tests for the CLI safe mode bootstrap behaviour."""

from __future__ import annotations

import argparse
import logging

import pytest
from pytestqt.qtbot import QtBot

from PySide6.QtCore import QTimer, Qt, qInstallMessageHandler
from PySide6.QtWidgets import QApplication

from src.app_runner import ApplicationRunner
from src.cli.arguments import parse_arguments


def test_parse_safe_alias_sets_test_mode() -> None:
    """``--safe`` should behave as a CLI alias for ``--test-mode``."""

    namespace = parse_arguments(["--safe"])

    assert namespace.test_mode is True
    assert namespace.safe_cli_mode is True
    assert namespace.safe is True


def test_parse_test_mode_does_not_mark_safe_alias() -> None:
    """``--test-mode`` should not masquerade as the ``--safe`` alias."""

    namespace = parse_arguments(["--test-mode"])

    assert namespace.test_mode is True
    assert namespace.safe_cli_mode is True
    assert namespace.safe is False


@pytest.mark.qt_no_exception_capture
def test_safe_mode_exits_without_loading_main_window(
    qtbot: QtBot, qapp: QApplication, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Safe mode must skip QML loading and exit the Qt event loop."""

    runner = ApplicationRunner(
        lambda _argv: qapp,  # type: ignore[arg-type]
        qInstallMessageHandler,
        Qt,
        QTimer,
    )

    monkeypatch.setattr(runner, "_print_header", lambda: None)
    monkeypatch.setattr(runner, "_log_startup_environment", lambda: None)
    monkeypatch.setattr(runner, "setup_high_dpi", lambda: None)
    monkeypatch.setattr(runner, "_validate_settings_file", lambda: None)

    created = {"called": False}

    def _record_window_creation() -> None:
        created["called"] = True

    monkeypatch.setattr(runner, "create_main_window", _record_window_creation)
    monkeypatch.setattr(runner, "setup_signals", lambda: None)
    monkeypatch.setattr(runner, "setup_test_mode", lambda _enabled: None)

    def _fake_setup_logging(*, verbose_console: bool = False) -> logging.Logger:
        logger = logging.getLogger("safe-mode-test")
        logger.setLevel(logging.INFO)
        if verbose_console:
            logger.info("Verbose console logging enabled in test stub")
        return logger

    monkeypatch.setattr(runner, "setup_logging", _fake_setup_logging)

    exit_calls: dict[str, int | None] = {"code": None}

    original_exit = qapp.exit

    def _record_exit(
        code: int = 0,
    ) -> None:  # pragma: no cover - exercised in Qt event loop
        exit_calls["code"] = code
        original_exit(code)

    monkeypatch.setattr(qapp, "exit", _record_exit)

    args = argparse.Namespace(
        diag=False,
        verbose=False,
        safe_mode=False,
        safe=True,
        safe_runtime=True,
        legacy=False,
        force_disable_qml_3d=True,
        force_disable_qml_3d_reasons=("safe-cli",),
        test_mode=True,
        safe_cli_mode=True,
    )

    exit_code = runner.run(args)

    assert exit_code == 0
    assert created["called"] is False
    assert runner.window_instance is None
    assert runner._safe_exit_timer is not None
    assert runner._surface_format_configured is False
    assert exit_calls["code"] == 0
