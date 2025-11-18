"""Integration coverage for geometry panel UI interactions and validation flows."""

from __future__ import annotations

from typing import Any

import os

import pytest

from src.ui.panels.geometry.defaults import DEFAULT_GEOMETRY

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 widgets require OpenGL libraries that are unavailable",
    exc_type=ImportError,
)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.ui.panels.geometry.options_tab import OptionsTab
from src.ui.panels.geometry.state_manager import GeometryStateManager


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_options_tab_validation_displays_dialogs(monkeypatch) -> None:
    """Validate button should surface errors and emit the control signal."""

    state_manager = GeometryStateManager()

    errors: list[str] = ["geometric overlap", "hydraulic violation"]
    warnings: list[str] = []

    monkeypatch.setattr(state_manager, "validate_geometry", lambda: list(errors))
    monkeypatch.setattr(state_manager, "get_warnings", lambda: list(warnings))

    calls: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        "src.ui.panels.geometry.options_tab.message_critical",
        lambda _parent, title, text: calls.append(("critical", title, text)),
    )
    monkeypatch.setattr(
        "src.ui.panels.geometry.options_tab.message_warning",
        lambda _parent, title, text: calls.append(("warning", title, text)),
    )
    monkeypatch.setattr(
        "src.ui.panels.geometry.options_tab.message_info",
        lambda _parent, title, text: calls.append(("info", title, text)),
    )

    tab = OptionsTab(state_manager)
    emitted: list[str] = []
    tab.validate_requested.connect(lambda: emitted.append("validate"))

    tab.validate_button.click()

    assert calls and calls[0][0] == "critical", "Expected critical dialog for errors"
    assert "geometric overlap" in calls[0][2]
    assert emitted == ["validate"]


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_interference_toggle_runs_validation(monkeypatch) -> None:
    """Enabling interference check should trigger validation feedback and option change."""

    state_manager = GeometryStateManager()
    state_manager.set_parameter("interference_check", False)

    validation_calls: list[str] = []
    monkeypatch.setattr(
        state_manager,
        "validate_geometry",
        lambda: validation_calls.append("validate") or [],
    )
    monkeypatch.setattr(
        state_manager,
        "get_warnings",
        lambda: ["rod diameter is close to the limit"],
    )

    calls: list[tuple[str, str, str]] = []
    for name in ("message_critical", "message_warning", "message_info"):
        monkeypatch.setattr(
            f"src.ui.panels.geometry.options_tab.{name}",
            lambda _parent, title, text, _name=name: calls.append((_name, title, text)),
        )

    tab = OptionsTab(state_manager)
    option_updates: list[tuple[str, Any]] = []
    tab.option_changed.connect(lambda name, value: option_updates.append((name, value)))

    tab.interference_check.setChecked(True)

    assert ("interference_check", True) in option_updates
    assert any(kind == "message_info" for kind, *_ in calls)
    assert any(kind == "message_warning" for kind, *_ in calls)
    assert validation_calls == ["validate"], (
        "Validation should run when enabling interference checks"
    )


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_validation_success_and_warning_paths(monkeypatch) -> None:
    """Validation button should surface warnings and success confirmations."""

    state_manager = GeometryStateManager()

    sequences = [
        {"errors": [], "warnings": ["rod diameter near limit"]},
        {"errors": [], "warnings": []},
    ]

    calls: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        "src.ui.panels.geometry.options_tab.message_warning",
        lambda _parent, title, text: calls.append(("warning", title, text)),
    )
    monkeypatch.setattr(
        "src.ui.panels.geometry.options_tab.message_info",
        lambda _parent, title, text: calls.append(("info", title, text)),
    )
    monkeypatch.setattr(
        state_manager, "validate_geometry", lambda: sequences[0]["errors"]
    )
    monkeypatch.setattr(state_manager, "get_warnings", lambda: sequences[0]["warnings"])

    tab = OptionsTab(state_manager)
    emits: list[str] = []
    tab.validate_requested.connect(lambda: emits.append("validate"))

    tab.validate_button.click()

    monkeypatch.setattr(
        state_manager, "validate_geometry", lambda: sequences[1]["errors"]
    )
    monkeypatch.setattr(state_manager, "get_warnings", lambda: sequences[1]["warnings"])

    tab.validate_button.click()

    assert (
        "warning",
        "Предупреждения геометрии",
    ) in [(kind, title) for kind, title, _ in calls]
    assert any(kind == "info" and "корректны" in message for kind, _, message in calls)
    assert emits == ["validate", "validate"]


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_reset_button_resets_options_and_emits(monkeypatch) -> None:
    """Reset button should confirm, restore defaults, and emit reset event."""

    state_manager = GeometryStateManager()
    state_manager.set_parameter("interference_check", False)
    state_manager.set_parameter("link_rod_diameters", True)

    prompts: list[tuple[str, str, bool]] = []
    monkeypatch.setattr(
        "src.ui.panels.geometry.options_tab.dialogs_allowed", lambda: True
    )
    monkeypatch.setattr(
        "src.ui.panels.geometry.options_tab.message_question",
        lambda _parent, title, text, default_yes=False: prompts.append(
            (title, text, default_yes)
        )
        or True,
    )

    tab = OptionsTab(state_manager)
    reset_events: list[bool] = []
    tab.reset_requested.connect(lambda: reset_events.append(True))

    tab.reset_button.click()

    assert (
        state_manager.get_all_parameters()["interference_check"]
        is DEFAULT_GEOMETRY["interference_check"]
    )
    assert (
        state_manager.get_all_parameters()["link_rod_diameters"]
        is DEFAULT_GEOMETRY["link_rod_diameters"]
    )
    assert tab.interference_check.isChecked() is True
    assert tab.link_rod_diameters.isChecked() is False
    assert reset_events == [True]
    assert prompts and prompts[0][2] is False
