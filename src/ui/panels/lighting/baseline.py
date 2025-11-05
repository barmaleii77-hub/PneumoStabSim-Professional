"""Compatibility shim re-exporting lighting baseline helpers."""

from __future__ import annotations

from src.graphics.materials.baseline import *  # noqa: F401,F403

__all__ = [name for name in globals().keys() if not name.startswith("_")]
