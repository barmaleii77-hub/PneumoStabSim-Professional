"""Compatibility shim exposing geometry helpers expected by tests.

Historically tests imported from `src.mechanics.geometry`. The implementation
was refactored into `linkage_geometry.py`. This module re-exports the
expected symbols and provides a lightweight `LinkagePoint` alias used by
legacy tests.
"""
from __future__ import annotations

from typing import Tuple

from .linkage_geometry import SuspensionLinkage

LinkagePoint = Tuple[float, float]

__all__ = ["SuspensionLinkage", "LinkagePoint"]
