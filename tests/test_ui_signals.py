"""UI signal validation tests using pytest and pytest-qt."""

from __future__ import annotations

import pytest
from PySide6.QtTest import QSignalSpy

from src.ui.widgets.knob import Knob
from src.ui.widgets.range_slider import RangeSlider
from src.ui.panels.panel_pneumo import PneumoPanel

pytestmark = pytest.mark.gui


@pytest.fixture
def ensure_no_windows(qapp, qtbot):
    """Ensure that no top-level windows remain visible after a test."""

    yield

    def _no_visible_windows() -> bool:
        return all(not widget.isVisible() for widget in qapp.topLevelWidgets())

    qtbot.waitUntil(_no_visible_windows, timeout=1000)


def test_knob_value_changed_signal(qtbot, ensure_no_windows):
    """Knob should emit valueChanged once when the value changes."""
    knob = Knob(minimum=0.0, maximum=100.0, value=50.0)
    qtbot.addWidget(knob)

    spy = QSignalSpy(knob.valueChanged)
    new_value = 75.0

    knob.setValue(new_value)

    assert len(spy) == 1, "Signal should be emitted once, got " f"{len(spy)} emissions"
    emitted_value = spy[0][0]
    assert emitted_value == pytest.approx(new_value)


def test_knob_multiple_changes(qtbot, ensure_no_windows):
    """Knob signal spy should track multiple value changes."""
    knob = Knob(minimum=0.0, maximum=100.0, value=0.0)
    qtbot.addWidget(knob)

    spy = QSignalSpy(knob.valueChanged)
    values = [25.0, 50.0, 75.0, 100.0]

    for value in values:
        knob.setValue(value)

    assert len(spy) == len(values)


def test_knob_bounds(qtbot, ensure_no_windows):
    """Knob should respect defined minimum and maximum bounds."""
    minimum = 10.0
    maximum = 90.0
    knob = Knob(minimum=minimum, maximum=maximum, value=50.0)
    qtbot.addWidget(knob)

    knob.setValue(5.0)
    assert knob.value() >= minimum

    knob.setValue(95.0)
    assert knob.value() <= maximum


def test_range_slider_min_changed(qtbot, ensure_no_windows):
    """RangeSlider should emit minValueChanged when the minimum changes."""
    slider = RangeSlider(minimum=0.0, maximum=100.0)
    qtbot.addWidget(slider)

    slider.setMinValue(20.0)
    slider.setMaxValue(80.0)

    spy = QSignalSpy(slider.minValueChanged)
    new_min = 30.0

    slider.setMinValue(new_min)

    assert len(spy) > 0


def test_range_slider_max_changed(qtbot, ensure_no_windows):
    """RangeSlider should emit maxValueChanged when the maximum changes."""
    slider = RangeSlider(minimum=0.0, maximum=100.0)
    qtbot.addWidget(slider)

    slider.setMinValue(20.0)
    slider.setMaxValue(80.0)

    spy = QSignalSpy(slider.maxValueChanged)
    new_max = 90.0

    slider.setMaxValue(new_max)

    assert len(spy) > 0


def test_range_slider_bounds_validation(qtbot, ensure_no_windows):
    """RangeSlider should keep minimum value less than or equal to maximum."""
    slider = RangeSlider(minimum=0.0, maximum=100.0)
    qtbot.addWidget(slider)

    slider.setMinValue(40.0)
    slider.setMaxValue(60.0)

    assert slider.minValue() <= slider.maxValue()


def test_pneumo_panel_creates(qtbot, ensure_no_windows):
    """PneumoPanel should be instantiated without errors."""
    panel = PneumoPanel()
    qtbot.addWidget(panel)

    assert panel is not None


def test_pneumo_panel_has_signals(qtbot, ensure_no_windows):
    """PneumoPanel should expose required signals."""
    panel = PneumoPanel()
    qtbot.addWidget(panel)

    assert hasattr(panel, "parameter_changed")
    assert hasattr(panel, "mode_changed")


def test_pneumo_panel_parameter_update(qtbot, ensure_no_windows):
    """PneumoPanel should expose parameters as a mutable mapping."""
    panel = PneumoPanel()
    qtbot.addWidget(panel)

    params = panel.get_parameters()

    assert isinstance(params, dict)
    assert "receiver_volume" in params or "tank_volume" in params


def test_signal_slot_basic(qtbot, ensure_no_windows):
    """Signal-slot connections should deliver emitted values."""
    knob = Knob(minimum=0.0, maximum=100.0)
    qtbot.addWidget(knob)

    received_values: list[float] = []

    def slot(value: float) -> None:
        received_values.append(value)

    knob.valueChanged.connect(slot)

    knob.setValue(25.0)
    knob.setValue(75.0)

    assert received_values == [25.0, 75.0]


def test_signal_disconnect(qtbot, ensure_no_windows):
    """Disconnecting a signal should stop the slot from receiving updates."""
    knob = Knob(minimum=0.0, maximum=100.0)
    qtbot.addWidget(knob)

    received_values: list[float] = []

    def slot(value: float) -> None:
        received_values.append(value)

    knob.valueChanged.connect(slot)
    knob.setValue(10.0)

    knob.valueChanged.disconnect(slot)
    knob.setValue(20.0)

    assert received_values == [10.0]


def test_knob_to_model_flow(qtbot, ensure_no_windows):
    """Knob updates should propagate to a connected model parameter."""
    knob = Knob(minimum=0.0, maximum=10.0, value=5.0)
    qtbot.addWidget(knob)

    model_param = {"value": 0.0}

    def update_model(value: float) -> None:
        model_param["value"] = value

    knob.valueChanged.connect(update_model)

    knob.setValue(7.5)

    assert model_param["value"] == pytest.approx(7.5)
