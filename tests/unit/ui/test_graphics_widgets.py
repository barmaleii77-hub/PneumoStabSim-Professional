"""Unit tests for lightweight graphics panel widgets."""

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 QtWidgets module is required for LabeledSlider tests",
)

from src.ui.panels.graphics.widgets import LabeledSlider


@pytest.mark.usefixtures("qtbot")
class TestLabeledSlider:
    """Behavioural tests for :class:`LabeledSlider`."""

    def test_step_size_updates_controls(self, qtbot):
        slider = LabeledSlider("Test", 0.0, 10.0, 0.5)
        qtbot.addWidget(slider)

        slider.set_value(2.5)
        assert slider.step_size == pytest.approx(0.5)

        slider.step_size = 1.0
        assert slider.step_size == pytest.approx(1.0)
        spin_step = slider._spin.singleStep()  # type: ignore[attr-defined]
        assert spin_step == pytest.approx(1.0)

        slider_range = slider._slider.maximum()  # type: ignore[attr-defined]
        expected_range = int(round((slider._max - slider._min) / slider.step_size))  # type: ignore[attr-defined]
        assert slider_range == expected_range

        assert slider.value() == pytest.approx(2.5)

        slider.step = 0.25
        assert slider.step_size == pytest.approx(0.25)
