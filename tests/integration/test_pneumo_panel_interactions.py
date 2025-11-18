"""Integration coverage for pneumatic panel validation UI flows."""

from __future__ import annotations

import os

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 widgets require OpenGL libraries that are unavailable",
    exc_type=ImportError,
)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QMessageBox  # type: ignore  # noqa: E402

from src.ui.panels.pneumo.panel_pneumo_refactored import PneumoPanel  # noqa: E402


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_pneumo_panel_validate_button_prioritizes_errors(monkeypatch) -> None:
    """Critical dialogs should take precedence over warnings and info messages."""

    panel = PneumoPanel()

    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        panel.state_manager,
        "validate_pneumatic",
        lambda: (["receiver volume invalid"], ["minor drift"]),
    )

    def _capture(name: str, *args, **kwargs):  # noqa: ANN001, D401
        payload = "".join(str(arg) for arg in args[1:])
        calls.append((name, payload))
        return None

    for method in ("critical", "warning", "information"):
        monkeypatch.setattr(QMessageBox, method, lambda *args, _m=method, **kwargs: _capture(_m, *args, **kwargs))

    panel.validate_button.click()

    assert calls, "Validation click did not trigger any dialog"
    first_type, message = calls[0]
    assert first_type == "critical"
    assert "receiver volume invalid" in message
    assert not any(kind == "warning" for kind, _ in calls[:1])


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_pneumo_panel_validation_handles_out_of_range_limits(monkeypatch) -> None:
    """Manual volume validation should surface configuration errors to the user."""

    panel = PneumoPanel()
    panel.state_manager.set_volume_mode("MANUAL")
    panel.state_manager._state["receiver_volume_limits"] = {"min_m3": -1.0, "max_m3": -0.5}
    panel.state_manager._state["receiver_volume"] = -0.3

    captured: list[str] = []
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda *args, **kwargs: captured.append(str(args[2])),
    )
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: captured.append("warning"))
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: captured.append("info"))

    panel.validate_button.click()

    assert captured, "Validation should raise user-facing diagnostics"
    assert any("объём ресивера" in msg.lower() or "объем ресивера" in msg.lower() for msg in captured)
    assert any("максимальный объём" in msg.lower() or "максимальный объем" in msg.lower() for msg in captured)
    assert all(msg != "info" for msg in captured), "Informational dialogs are not expected when errors exist"
