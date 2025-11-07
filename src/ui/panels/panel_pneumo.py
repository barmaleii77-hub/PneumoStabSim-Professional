"""Compatibility wrapper for the pneumatic panel."""

from __future__ import annotations

from .pneumo import PneumoPanel, get_version_info  # re-export refactored entry point

__all__ = ["PneumoPanel", "get_version_info"]
