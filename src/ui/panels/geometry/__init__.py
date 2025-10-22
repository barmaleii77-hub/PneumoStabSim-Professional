# -*- coding: utf-8 -*-
"""
Geometry Panel Module
Модуль панели геометрии с fallback на старую версию
"""

import logging

logger = logging.getLogger(__name__)

# =============================================================================
# TRY REFACTORED VERSION FIRST
# =============================================================================

_USING_REFACTORED = False

try:
    from .panel_geometry_refactored import GeometryPanel

    _USING_REFACTORED = True
    logger.info("✅ GeometryPanel: Using REFACTORED modular version")

except ImportError as e:
    logger.warning(f"⚠️ GeometryPanel: Cannot import refactored version: {e}")
    logger.info("📦 GeometryPanel: Falling back to legacy version...")

    # ==========================================================================
    # FALLBACK TO LEGACY VERSION
    # ==========================================================================

    try:
        from ..panel_geometry import GeometryPanel

        logger.info("✅ GeometryPanel: Using LEGACY monolithic version")

    except ImportError as e2:
        logger.error(f"❌ GeometryPanel: Cannot import legacy version: {e2}")
        raise ImportError(
            "GeometryPanel: Neither refactored nor legacy version available!"
        ) from e2


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ["GeometryPanel"]


# =============================================================================
# VERSION INFO
# =============================================================================


def get_version_info() -> dict:
    """Get version information

    Returns:
        Dictionary with version info
    """
    return {
        "module": "GeometryPanel",
        "refactored": _USING_REFACTORED,
        "version": "1.0.0" if _USING_REFACTORED else "legacy",
        "coordinator_lines": 250 if _USING_REFACTORED else 850,
        "total_modules": 8 if _USING_REFACTORED else 1,
    }


# =============================================================================
# MODULE DIAGNOSTICS
# =============================================================================

if __name__ == "__main__":
    # Print version info when module is run directly
    info = get_version_info()

    print("=" * 60)
    print("GEOMETRYPANEL MODULE INFO")
    print("=" * 60)
    print(f"Module: {info['module']}")
    print(f"Using Refactored: {info['refactored']}")
    print(f"Version: {info['version']}")
    print(f"Coordinator Lines: {info['coordinator_lines']}")
    print(f"Total Modules: {info['total_modules']}")
    print("=" * 60)

    if info["refactored"]:
        print("✅ Modular structure active!")
        print("   - frame_tab.py")
        print("   - suspension_tab.py")
        print("   - cylinder_tab.py")
        print("   - options_tab.py")
        print("   - state_manager.py")
        print("   - defaults.py")
    else:
        print("⚠️ Using legacy monolithic version")
