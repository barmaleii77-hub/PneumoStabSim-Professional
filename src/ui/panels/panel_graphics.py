"""Compatibility shim exposing the modular graphics panel under the legacy path."""

from __future__ import annotations

from .graphics.panel_graphics import GraphicsPanel

__all__ = ["GraphicsPanel"]
