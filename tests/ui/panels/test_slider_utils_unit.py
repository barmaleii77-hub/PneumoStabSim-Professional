from __future__ import annotations

import math

import pytest

from ._slider_utils import resolve_slider_step


class _DummySpinbox:
    def __init__(self, step: float | None) -> None:
        self._step = step

    def singleStep(self) -> float | None:  # pragma: no cover - exercised indirectly
        return self._step


class _DummySlider:
    def __init__(
        self,
        *,
        step: float | None = None,
        private_step: float | None = None,
        spinbox_step: float | None = None,
    ) -> None:
        if step is not None:
            self.step = step  # type: ignore[assignment]
        if private_step is not None:
            self._step = private_step
        if spinbox_step is not None:
            self.value_spinbox = _DummySpinbox(spinbox_step)


@pytest.mark.parametrize(
    "slider_kwargs, delta, expected",
    [
        ({"step": 0.2}, 0.5, 0.2),
        ({"step": 0.25}, -0.1, -0.25),
        ({"private_step": 0.05}, 0.1, 0.05),
        ({"spinbox_step": 0.75}, 0.1, 0.75),
        ({}, 0.6, 0.6),
    ],
)
def test_resolve_slider_step_fallbacks(slider_kwargs, delta, expected):
    slider = _DummySlider(**slider_kwargs)
    resolved = resolve_slider_step(slider, delta)
    assert math.isclose(resolved, expected, rel_tol=1e-9, abs_tol=1e-9)


def test_resolve_slider_step_zero_delta_without_step():
    slider = _DummySlider(spinbox_step=0.5)
    assert resolve_slider_step(slider, 0.0) == pytest.approx(0.5)


def test_resolve_slider_step_zero_delta_no_metadata():
    slider = _DummySlider()
    assert resolve_slider_step(slider, 0.0) == pytest.approx(1.0)
