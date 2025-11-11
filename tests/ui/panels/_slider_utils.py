from __future__ import annotations

import math
from typing import Any


def _call_getter(obj: Any, name: str) -> Any:
    attr = getattr(obj, name, None)
    if callable(attr):  # pragma: no branch - tiny helper
        try:
            return attr()
        except TypeError:
            return attr
    return attr


def _call_setter(obj: Any, name: str, value: float) -> bool:
    attr = getattr(obj, name, None)
    if callable(attr):
        attr(float(value))
        return True
    return False


def get_slider_value(slider: Any) -> float:
    """Return the current value exposed by the slider or its spinbox."""

    value = _call_getter(slider, "value")
    if value is None and hasattr(slider, "value_spinbox"):
        value = _call_getter(slider.value_spinbox, "value")
    if value is None:
        return 0.0
    return float(value)


def resolve_slider_step(slider: Any, delta: float) -> float:
    """Determine the appropriate step delta for ``slider``.

    Community builds of PySide6 occasionally omit the ``step`` property on
    derived widgets.  Tests use this helper to gracefully fall back to the
    requested ``delta`` when the property is unavailable.
    """

    raw_step = _call_getter(slider, "step")
    try:
        numeric_step = float(raw_step)
    except (TypeError, ValueError):
        return float(delta)

    if math.isclose(numeric_step, 0.0, abs_tol=1e-12):
        return float(delta)

    if math.isclose(delta, 0.0, abs_tol=1e-12):
        return abs(numeric_step)

    sign = 1.0 if delta >= 0 else -1.0
    return abs(numeric_step) * sign


def clamp_slider_value(slider: Any, candidate: float) -> float:
    """Clamp ``candidate`` to the slider's configured range."""

    minimum = _call_getter(slider, "minimum")
    maximum = _call_getter(slider, "maximum")
    if minimum is None:
        minimum = getattr(slider, "_minimum", getattr(slider, "_min", candidate))
    if maximum is None:
        maximum = getattr(slider, "_maximum", getattr(slider, "_max", candidate))

    minimum_f = float(minimum)
    maximum_f = float(maximum)
    if minimum_f > maximum_f:  # pragma: no cover - defensive guard
        minimum_f, maximum_f = maximum_f, minimum_f

    return max(minimum_f, min(maximum_f, float(candidate)))


def apply_slider_value(slider: Any, target: float) -> float:
    """Set ``slider`` to ``target`` using the most reliable pathway.

    ``RangeSlider`` instances expose ``setValue`` but older or community Qt
    builds may require writing through the companion spin box instead.  The
    helper attempts both approaches and returns the value reported after the
    update.
    """

    clamped = clamp_slider_value(slider, target)
    _call_setter(slider, "setValue", clamped)

    current = _call_getter(slider, "value")
    if current is None or not math.isclose(
        float(current), clamped, rel_tol=1e-9, abs_tol=1e-9
    ):
        spinbox = getattr(slider, "value_spinbox", None)
        if spinbox is not None:
            _call_setter(spinbox, "setValue", clamped)
            current = _call_getter(slider, "value")

    if current is None:
        current = clamped
    return float(current)


def nudge_slider(slider: Any, delta: float) -> float:
    """Adjust ``slider`` by one logical step respecting missing APIs."""

    current = get_slider_value(slider)
    step_delta = resolve_slider_step(slider, delta)
    return apply_slider_value(slider, current + step_delta)


__all__ = [
    "apply_slider_value",
    "clamp_slider_value",
    "get_slider_value",
    "nudge_slider",
    "resolve_slider_step",
]
