"""Typed utilities maintained under strict quality gates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(slots=True)
class SampleVector:
    """Simple immutable vector used to validate tooling."""

    x: float
    y: float
    z: float

    def scaled(self, factor: float) -> "SampleVector":
        """Return a new vector scaled by ``factor``."""

        return SampleVector(self.x * factor, self.y * factor, self.z * factor)


def average_component(values: Iterable[SampleVector]) -> SampleVector:
    """Compute component-wise average for a sequence of :class:`SampleVector`."""

    total_x = 0.0
    total_y = 0.0
    total_z = 0.0
    count = 0

    for vector in values:
        total_x += vector.x
        total_y += vector.y
        total_z += vector.z
        count += 1

    if count == 0:
        raise ValueError("values must not be empty")

    inv = 1.0 / count
    return SampleVector(total_x * inv, total_y * inv, total_z * inv)
