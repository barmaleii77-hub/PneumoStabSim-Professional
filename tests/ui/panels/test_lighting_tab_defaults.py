from __future__ import annotations

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for LightingTab tests",
    exc_type=ImportError,
)

from src.ui.panels.graphics.lighting_tab import LightingTab


def _quantize(
    value: float, *, step: float = 0.01, minimum: float = 0.0, maximum: float = 10.0
) -> float:
    clamped = max(minimum, min(maximum, value))
    steps = round((clamped - minimum) / step)
    return round(minimum + steps * step, 6)


@pytest.mark.gui
def test_point_light_attenuation_defaults_are_applied(
    qtbot: pytestqt.qtbot.QtBot,
) -> None:
    """LightingTab should surface engine attenuation defaults on startup."""

    tab = LightingTab()
    qtbot.addWidget(tab)

    controls = tab.get_controls()

    constant_slider = controls["point.constant_fade"]
    linear_slider = controls["point.linear_fade"]
    quadratic_slider = controls["point.quadratic_fade"]

    # Regression coverage: set_state must backfill defaults when they are missing
    # or explicitly null in the payload to avoid resetting sliders to 0.0.
    tab.set_state(
        {"point": {"constant_fade": None, "linear_fade": None, "quadratic_fade": None}}
    )

    point_state = tab.get_state()["point"]
    range_value = point_state["range"]
    expected_linear = _quantize(2.0 / range_value)

    assert constant_slider.value() == pytest.approx(1.0)
    assert linear_slider.value() == pytest.approx(expected_linear, rel=1e-6)
    assert quadratic_slider.value() == pytest.approx(1.0)

    assert point_state["constant_fade"] == pytest.approx(1.0)
    assert point_state["linear_fade"] == pytest.approx(expected_linear, rel=1e-6)
    assert point_state["quadratic_fade"] == pytest.approx(1.0)

    # Invalid or out-of-range inputs fall back to engine defaults.
    tab.set_state(
        {"point": {"constant_fade": -5.0, "linear_fade": 0.0, "quadratic_fade": "oops"}}
    )
    point_state = tab.get_state()["point"]

    assert constant_slider.value() == pytest.approx(1.0)
    assert linear_slider.value() == pytest.approx(expected_linear, rel=1e-6)
    assert quadratic_slider.value() == pytest.approx(1.0)

    assert point_state["constant_fade"] == pytest.approx(1.0)
    assert point_state["linear_fade"] == pytest.approx(expected_linear, rel=1e-6)
    assert point_state["quadratic_fade"] == pytest.approx(1.0)

    # Values above the slider range clamp to the UI limits.
    tab.set_state(
        {"point": {"constant_fade": 15.0, "linear_fade": 20.0, "quadratic_fade": 12.5}}
    )
    point_state = tab.get_state()["point"]

    assert constant_slider.value() == pytest.approx(10.0)
    assert linear_slider.value() == pytest.approx(10.0)
    assert quadratic_slider.value() == pytest.approx(10.0)

    assert point_state["constant_fade"] == pytest.approx(10.0)
    assert point_state["linear_fade"] == pytest.approx(10.0)
    assert point_state["quadratic_fade"] == pytest.approx(10.0)

    # Custom values inside the allowed range should remain intact.
    tab.set_state(
        {"point": {"constant_fade": 0.8, "linear_fade": 0.42, "quadratic_fade": 0.5}}
    )
    point_state = tab.get_state()["point"]

    assert constant_slider.value() == pytest.approx(0.8)
    assert linear_slider.value() == pytest.approx(0.42)
    assert quadratic_slider.value() == pytest.approx(0.5)

    assert point_state["constant_fade"] == pytest.approx(0.8)
    assert point_state["linear_fade"] == pytest.approx(0.42)
    assert point_state["quadratic_fade"] == pytest.approx(0.5)
