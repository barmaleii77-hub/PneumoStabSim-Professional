"""
UI panels for PneumoStabSim
"""

# ✅ ИСПРАВЛЕНО: Импортируем РЕФАКТОРЕННУЮ версию из подпакета graphics!
from .panel_geometry import GeometryPanel
from .panel_pneumo import PneumoPanel
from .panel_modes import ModesPanel
from .panel_road import RoadPanel
from .graphics.panel_graphics_refactored import GraphicsPanel  # ✅ РЕФАКТОРЕННАЯ ВЕРСИЯ!

__all__ = ["GeometryPanel", "PneumoPanel", "ModesPanel", "RoadPanel", "GraphicsPanel"]
