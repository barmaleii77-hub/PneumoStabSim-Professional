"""Reporting helpers shared between CLI utilities and tests."""

from .physics import evaluate_physics_case, summarise_assertions

__all__ = [
    "evaluate_physics_case",
    "summarise_assertions",
]
