from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import logging
import pytest

from PySide6.QtCore import QCoreApplication

from src.runtime.sim_loop import PhysicsWorker, SimulationManager


@pytest.mark.usefixtures("qapp")
def test_physics_worker_emits_error_on_step_failure(qtbot, caplog):
    """PhysicsWorker should emit ``error_occurred`` and stop when a step fails."""

    worker = PhysicsWorker()
    qtbot.addCleanup(worker.deleteLater)
    caplog.set_level(logging.ERROR, logger="runtime.physics")

    worker.is_running = True
    worker.timing_accumulator.update = lambda: 1  # type: ignore[assignment]
    worker._execute_physics_step = Mock(side_effect=RuntimeError("boom"))
    worker._create_state_snapshot = lambda: SimpleNamespace(  # type: ignore[assignment]
        validate=lambda: True
    )

    with qtbot.waitSignal(worker.error_occurred, timeout=1000) as signal:
        worker._physics_step()

    assert not worker.is_running
    assert signal.args[0].startswith("Physics step error")
    error_logs = [record.message for record in caplog.records]
    assert any("ERROR: physics step failed" in message for message in error_logs)


@pytest.mark.usefixtures("qapp")
def test_simulation_manager_logs_and_exits_on_physics_error(qtbot, capfd, monkeypatch):
    """SimulationManager should log to stderr and exit the application on errors."""

    manager = SimulationManager()
    qtbot.addCleanup(manager.deleteLater)

    app = QCoreApplication.instance()
    assert app is not None

    exit_called: dict[str, int] = {}

    def _fake_exit(code: int) -> None:
        exit_called["code"] = code

    monkeypatch.setattr(app, "exit", _fake_exit)

    manager._on_physics_error("integration blow-up")

    assert exit_called.get("code") == 1
    stderr_output = capfd.readouterr().err
    assert "ERROR: physics error" in stderr_output
