from __future__ import annotations

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for Knob widget tests",
    exc_type=ImportError,
)

from src.ui.widgets.knob import Knob


def test_set_units_updates_existing_label(qtbot):
    knob = Knob(units="м³")
    qtbot.addWidget(knob)

    assert knob.units_label.text() == "м³"

    knob.setUnits("бар")

    assert knob.units_label.text() == "бар"
    assert knob.units_label.isVisible()


def test_set_units_creates_label_when_missing(qtbot):
    knob = Knob()
    qtbot.addWidget(knob)

    assert knob.units_label is None

    knob.setUnits("мм")

    assert knob.units_label is not None
    assert knob.units_label.text() == "мм"
    assert knob.units_label.isVisible()

    knob.setUnits("")

    assert knob.units_label.text() == ""
    assert not knob.units_label.isVisible()
