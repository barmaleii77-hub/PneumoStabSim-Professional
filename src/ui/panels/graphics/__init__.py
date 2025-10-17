# -*- coding: utf-8 -*-
"""
Graphics Panel - модульная реструктуризация
Модуль управления настройками графики и визуализации

СТРУКТУРА МОДУЛЯ:
- widgets.py: Переиспользуемые UI компоненты (ColorButton, LabeledSlider)
- defaults.py: Дефолтные настройки и пресеты
- lighting_tab.py: Вкладка освещения
- environment_tab.py: Вкладка окружения (фон, IBL, туман)
- quality_tab.py: Вкладка качества (тени, AA)
- camera_tab.py: Вкладка камеры (FOV, clipping)
- materials_tab.py: Вкладка материалов (PBR)
- effects_tab.py: Вкладка эффектов (Bloom, SSAO, DoF)
- state_manager.py: Управление состоянием (QSettings)
- panel_graphics_refactored.py: ✅ НОВЫЙ рефакторенный координатор (~300 строк)
- panel_graphics.py: ⚠️ LEGACY монолитная версия (~2600 строк)

MIGRATION STATUS: ✅ Рефакторинг завершён!
"""

# ✅ REFACTORED VERSION: Используем новый модульный координатор
try:
    from .panel_graphics_refactored import GraphicsPanel
    _USING_REFACTORED = True
except ImportError as e:
    # Fallback к старой монолитной версии (если что-то сломалось)
    import logging
    logging.getLogger(__name__).warning(f"Failed to load refactored version: {e}, falling back to legacy")
    from ..panel_graphics import GraphicsPanel
    _USING_REFACTORED = False

# Экспорт вкладок (для прямого импорта если нужно)
from .lighting_tab import LightingTab
from .environment_tab import EnvironmentTab
from .quality_tab import QualityTab
from .camera_tab import CameraTab
from .materials_tab import MaterialsTab
from .effects_tab import EffectsTab

# Экспорт вспомогательных модулей
from .widgets import ColorButton, LabeledSlider
from .state_manager import GraphicsStateManager
from .defaults import build_defaults, build_quality_presets

__all__ = [
    # ✅ Главный класс (REFACTORED!)
    'GraphicsPanel',
    
    # Вкладки
    'LightingTab',
    'EnvironmentTab',
    'QualityTab',
    'CameraTab',
    'MaterialsTab',
    'EffectsTab',
    
    # Виджеты
    'ColorButton',
    'LabeledSlider',
    
    # Утилиты
    'GraphicsStateManager',
    'build_defaults',
    'build_quality_presets'
]

# Вывод статуса загрузки
import logging
_logger = logging.getLogger(__name__)
if _USING_REFACTORED:
    _logger.info("✅ GraphicsPanel: REFACTORED version loaded (~300 lines)")
else:
    _logger.warning("⚠️ GraphicsPanel: Using LEGACY version (~2600 lines) - migration incomplete")
