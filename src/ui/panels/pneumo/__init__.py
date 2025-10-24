# -*- coding: utf-8 -*-
"""Pneumatic panel package with refactored implementation and legacy fallback."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_USING_REFACTORED = False

try:
    from .panel_pneumo_refactored import PneumoPanel

    _USING_REFACTORED = True
    logger.info("✅ PneumoPanel: using refactored modular implementation")
except Exception as exc:  # pragma: no cover - fallback path
    logger.warning(
        "⚠️ PneumoPanel: refactored import failed, falling back to legacy", exc_info=exc
    )
    from ..panel_pneumo_legacy import PneumoPanel  # type: ignore

    logger.info("📦 PneumoPanel: legacy monolithic version active")

__all__ = ["PneumoPanel", "get_version_info"]


def get_version_info() -> dict[str, object]:
    """Return diagnostics about the active implementation."""

    return {
        "module": "PneumoPanel",
        "refactored": _USING_REFACTORED,
        "version": "1.0.0" if _USING_REFACTORED else "legacy",
    }


if __name__ == "__main__":  # pragma: no cover - manual diagnostics
    info = get_version_info()
    print("=" * 60)
    print("PNEUMOPANEL MODULE INFO")
    print("=" * 60)
    for key, value in info.items():
        print(f"{key}: {value}")
    print("=" * 60)
