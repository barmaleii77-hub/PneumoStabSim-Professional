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

        if hasattr(slider, "step"):
            slider.step = 0.25
            assert slider.step_size == pytest.approx(0.25)
        else:
            # PySide6 community builds may not expose ``step``; fall back to
            # validating that changing the canonical ``step_size`` attribute
            # still reconfigures the slider correctly and emits updates.
            captured: list[float] = []

            def _capture(value: float) -> None:
                captured.append(value)

            slider.valueChanged.connect(_capture)

            slider.step_size = 0.25
            slider.set_value(2.75)
            assert slider.step_size == pytest.approx(0.25)
            assert captured, "Expected valueChanged to fire after adjusting step"

    def test_clamps_to_extreme_values(self, qtbot):
        slider = LabeledSlider("Exposure", -5.0, 5.0, 0.1)
        qtbot.addWidget(slider)

        slider.set_value(4.5)
        slider._spin.setValue(500.0)  # type: ignore[attr-defined]
        assert slider.value() == pytest.approx(5.0)

        slider._spin.setValue(-500.0)  # type: ignore[attr-defined]
        assert slider.value() == pytest.approx(-5.0)
