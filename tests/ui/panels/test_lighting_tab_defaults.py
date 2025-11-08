from __future__ import annotations

import pytest

pytest.importorskip(
    "PySide6.QtWidgets",
    reason="PySide6 is required for LightingTab tests",
    exc_type=ImportError,
)

from src.ui.panels.graphics.lighting_tab import LightingTab


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

    assert constant_slider.value() == pytest.approx(1.0)
    assert linear_slider.value() == pytest.approx(0.01, rel=1e-6)
    assert quadratic_slider.value() == pytest.approx(1.0)

    # Regression coverage: set_state must backfill defaults when they are missing
    # or explicitly null in the payload to avoid resetting sliders to 0.0.
    tab.set_state({"point": {"constant_fade": None}})

    assert constant_slider.value() == pytest.approx(1.0)
    assert linear_slider.value() == pytest.approx(0.01, rel=1e-6)
    assert quadratic_slider.value() == pytest.approx(1.0)

    state = tab.get_state()["point"]
    assert state["constant_fade"] == pytest.approx(1.0)
    assert state["linear_fade"] == pytest.approx(0.01, rel=1e-6)
    assert state["quadratic_fade"] == pytest.approx(1.0)
