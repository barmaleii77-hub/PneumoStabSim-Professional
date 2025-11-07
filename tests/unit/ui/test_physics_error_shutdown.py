from __future__ import annotations

import logging

import pytest
from PySide6.QtCore import QCoreApplication

from src.ui.main_window_pkg.signals_router import SignalsRouter


class _DummyStatusBar:
    def __init__(self) -> None:
        self.messages: list[tuple[str, int]] = []

    def showMessage(self, message: str, timeout: int) -> None:  # pragma: no cover - qt
        self.messages.append((message, timeout))


class _DummyWindow:
    def __init__(self) -> None:
        self.status_bar = _DummyStatusBar()
        self.logger = logging.getLogger("dummy-window")


@pytest.mark.usefixtures("qapp")
def test_signals_router_requests_exit_on_physics_error(capfd, monkeypatch):
    window = _DummyWindow()
    app = QCoreApplication.instance()
    assert app is not None

    exit_args: dict[str, int] = {}

    def _fake_exit(code: int) -> None:
        exit_args["code"] = code

    monkeypatch.setattr(app, "exit", _fake_exit)

    SignalsRouter.handle_physics_error(window, "integration failure")

    assert exit_args.get("code") == 1
    assert window.status_bar.messages[0][0] == "Physics error: integration failure"
    stderr_output = capfd.readouterr().err
    assert "ERROR: physics engine error: integration failure" in stderr_output
