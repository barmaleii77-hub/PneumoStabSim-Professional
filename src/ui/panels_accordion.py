"""Legacy import shim for accordion panels.

This module preserves backward compatibility with older imports by
re-exporting the refactored panel classes from :mod:`src.ui.panels.accordion`.
"""

from src.ui.panels.accordion import (
    AdvancedPanelAccordion,
    GeometryPanelAccordion,
    PneumoPanelAccordion,
    RoadPanelAccordion,
    SimulationPanelAccordion,
)

__all__ = [
    "GeometryPanelAccordion",
    "PneumoPanelAccordion",
    "SimulationPanelAccordion",
    "RoadPanelAccordion",
    "AdvancedPanelAccordion",
]
