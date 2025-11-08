"""Behavioural tests for :class:`FileCyclerWidget`."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for FileCyclerWidget tests",
    exc_type=ImportError,
)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from src.ui.panels.graphics.widgets import FileCyclerWidget


@pytest.mark.gui
def test_file_cycler_missing_path_shows_indicator_and_warning(
    qapp,
    qtbot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog,
) -> None:
    widget = FileCyclerWidget()
    qtbot.addWidget(widget)
    widget.set_resolution_roots([tmp_path])
    widget.set_items([])

    warnings: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "PySide6.QtWidgets.QMessageBox.warning",
        lambda parent, title, text: warnings.append((title, text)),
    )

    caplog.set_level(logging.WARNING, logger="FileCyclerWidget")

    received: list[str] = []
    widget.currentChanged.connect(received.append)

    widget.show()
    qapp.processEvents()

    widget.set_current_data("missing_texture.png", emit=False)
    qapp.processEvents()

    assert widget.current_path() == "missing_texture.png"
    assert not received, "Programmatic load must not trigger change signal"
    assert widget.is_missing()

    indicator = widget.findChild(QLabel, "fileCyclerMissingIndicator")
    assert indicator is not None and indicator.isVisible()
    assert indicator.toolTip() == "missing_texture.png"

    assert warnings, "Expected warning dialog to be requested"
    assert "missing_texture.png" in warnings[0][1]
    assert any("missing_texture.png" in record.message for record in caplog.records)


@pytest.mark.gui
def test_file_cycler_keeps_missing_selection_when_items_refresh(
    qapp,
    qtbot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    widget = FileCyclerWidget()
    qtbot.addWidget(widget)

    monkeypatch.setattr(
        "PySide6.QtWidgets.QMessageBox.warning",
        lambda *args, **kwargs: None,
    )

    widget.set_items([("First", "first.png")])
    widget.set_current_data("missing.png", emit=False)
    widget.set_items([("First", "first.png"), ("Second", "second.png")])

    widget.show()
    qapp.processEvents()

    assert widget.current_path() == "missing.png"
    assert widget.is_missing()
    indicator = widget.findChild(QLabel, "fileCyclerMissingIndicator")
    assert indicator is not None and indicator.isVisible()


@pytest.mark.gui
def test_file_cycler_user_confirms_new_path_clears_warning(
    qapp,
    qtbot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    present = tmp_path / "present.png"
    present.write_bytes(b"fake")

    widget = FileCyclerWidget()
    qtbot.addWidget(widget)
    widget.set_resolution_roots([tmp_path])
    widget.set_items([("Present", "present.png")])

    monkeypatch.setattr(
        "PySide6.QtWidgets.QMessageBox.warning",
        lambda *args, **kwargs: None,
    )

    widget.show()
    qapp.processEvents()

    widget.set_current_data("missing.png", emit=False)
    qapp.processEvents()
    assert widget.is_missing()

    emitted: list[str] = []
    widget.currentChanged.connect(emitted.append)

    qtbot.mouseClick(widget._next_btn, Qt.LeftButton)  # type: ignore[attr-defined]
    qapp.processEvents()

    assert emitted == ["present.png"]
    assert widget.current_path() == "present.png"
    assert not widget.is_missing()
    indicator = widget.findChild(QLabel, "fileCyclerMissingIndicator")
    assert indicator is not None and not indicator.isVisible()


@pytest.mark.gui
def test_file_cycler_warning_resets_when_file_reappears(
    qapp,
    qtbot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog,
) -> None:
    target = tmp_path / "texture.png"

    widget = FileCyclerWidget()
    qtbot.addWidget(widget)
    widget.set_resolution_roots([tmp_path])
    widget.set_items([("Texture", "texture.png")])

    warnings: list[str] = []

    def fake_warning(parent, title, text):  # noqa: ANN001 - Qt slot signature
        warnings.append(text)

    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.warning", fake_warning)

    caplog.set_level(logging.WARNING, logger="FileCyclerWidget")

    widget.show()
    qapp.processEvents()

    widget.set_current_data("texture.png", emit=False)
    qapp.processEvents()

    assert widget.is_missing()
    assert warnings and "texture.png" in warnings[-1]

    target.write_bytes(b"stub")
    widget.set_current_data("texture.png", emit=False)
    qapp.processEvents()

    indicator = widget.findChild(QLabel, "fileCyclerMissingIndicator")
    assert indicator is not None and not indicator.isVisible()
    assert not widget.is_missing()
    assert not widget.missing_path()
    assert warnings == warnings[:1]

    target.unlink()
    widget.set_current_data("texture.png", emit=False)
    qapp.processEvents()

    assert widget.is_missing()
    assert len(warnings) == 2
    assert sum("texture.png" in record.message for record in caplog.records) >= 2
