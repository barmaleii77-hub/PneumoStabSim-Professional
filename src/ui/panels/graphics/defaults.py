# -*- coding: utf-8 -*-
"""
Graphics defaults access helpers.

Этот модуль теперь делегирует получение значений по умолчанию
к классу `SettingsManager`, чтобы все настройки приходили из
`config/app_settings.json`.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from src.common.settings_manager import get_settings_manager


def _load_graphics_defaults() -> Dict[str, Any]:
    """Загрузить дефолты графики из консолидационного файла настроек."""
    manager = get_settings_manager()
    defaults = manager.get_all_defaults().get("graphics")
    if not defaults:
        defaults = manager.get("graphics") or {}
    return deepcopy(defaults)


def build_defaults() -> Dict[str, Any]:
    """Вернуть снапшот дефолтных настроек графики из SettingsManager."""
    return _load_graphics_defaults()


GRAPHICS_DEFAULTS = build_defaults()
