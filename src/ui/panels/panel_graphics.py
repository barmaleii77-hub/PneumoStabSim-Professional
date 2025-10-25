"""Compatibility shim exposing the refactored graphics panel under the legacy path."""

from __future__ import annotations

from .graphics.panel_graphics_refactored import GraphicsPanel

__all__ = ["GraphicsPanel"]
