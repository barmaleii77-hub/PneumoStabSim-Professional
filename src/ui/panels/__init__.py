"""
UI panels for PneumoStabSim
"""

# ИСПРАВЛЕНО: Используем правильные пути к панелям  
from .panel_geometry import GeometryPanel
from .panel_pneumo import PneumoPanel
from .panel_modes import ModesPanel
from .panel_road import RoadPanel
from .panel_graphics import GraphicsPanel

__all__ = ['GeometryPanel', 'PneumoPanel', 'ModesPanel', 'RoadPanel', 'GraphicsPanel']
