# -*- coding: utf-8 -*-
"""
Graphics Panel - модульная реструктуризация
Модуль управления настройками графики и визуализации

СТРУКТУРА МОДУЛЯ:
- widgets.py: Переиспользуемые UI компоненты (ColorButton, LabeledSlider)
- lighting_tab.py: Вкладка освещения
- environment_tab.py: Вкладка окружения (фон, IBL, туман)
- quality_tab.py: Вкладка качества (тени, AA)
- camera_tab.py: Вкладка камеры (FOV, clipping)
- materials_tab.py: Вкладка материалов (PBR)
- effects_tab.py: Вкладка эффектов (Bloom, SSAO, DoF)
- state_manager.py: Управление состоянием
- panel_graphics_refactored.py: ✅ НОВЫЙ рефакторенный координатор v3.0 (SettingsManager)
- panel_graphics.py: ⚠️ LEGACY монолитная версия (~2600 строк)

MIGRATION STATUS: ✅ Рефакторинг завершён! v3.0 - SettingsManager integrated
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

# ✅ НОВОЕ: SettingsManager вместо defaults.py
from src.common.settings_manager import get_settings_manager

__all__ = [
    # ✅ Главный класс (REFACTORED v3.0!)
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
    'get_settings_manager',  # ✅ НОВОЕ: Экспорт SettingsManager
]

# Вывод статуса загрузки
import logging
_logger = logging.getLogger(__name__)
if _USING_REFACTORED:
    _logger.info("✅ GraphicsPanel: REFACTORED version v3.0 loaded (SettingsManager)")
else:
    _logger.warning("⚠️ GraphicsPanel: Using LEGACY version (~2600 lines) - migration incomplete")
