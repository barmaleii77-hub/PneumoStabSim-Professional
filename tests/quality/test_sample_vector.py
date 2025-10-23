from __future__ import annotations

import pytest

from pneumostabsim_typing import SampleVector, average_component


def test_average_component() -> None:
    vectors = [
        SampleVector(1.0, 2.0, 3.0),
        SampleVector(-1.0, 0.0, 1.0),
        SampleVector(0.0, 4.0, -2.0),
    ]

    avg = average_component(vectors)

    assert pytest.approx(avg.x) == 0.0
    assert pytest.approx(avg.y) == 2.0
    assert pytest.approx(avg.z) == 0.6666666667


def test_average_component_empty() -> None:
    with pytest.raises(ValueError):
        average_component([])
