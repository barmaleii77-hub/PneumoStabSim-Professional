# -*- coding: utf-8 -*-
"""
Unified Settings Manager
Единый менеджер настроек для всего приложения

ТРЕБОВАНИЯ:
- Один файл настроек для ВСЕГО приложения
- Никаких дефолтов в коде
- Сквозная прослеживаемость параметров
- Дефолты = текущие настройки (обновляются по кнопке "Сохранить как дефолт")
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import copy


class SettingsManager:
    """
    Централизованный менеджер настроек приложения
    
    Архитектура:
    1. Загрузка из config/app_settings.json (единый источник истины)
    2. Изменения только через UI
    3. Автосохранение при каждом изменении
    4. "Сброс" = загрузка snapshot дефолтов из того же файла
    5. "Сохранить как дефолт" = обновление snapshot в файле
    
    Структура файла:
    {
        "current": { ... текущие настройки ... },
        "defaults_snapshot": { ... сохраненные дефолты ... },
        "metadata": { "version", "last_modified", ... }
    }
    """
    
    def __init__(self, settings_file: str | Path = "config/app_settings.json"):
        self.logger = logging.getLogger(__name__)
        self.settings_file = Path(settings_file)
        
        # Внутреннее состояние
        self._current: Dict[str, Any] = {}
        self._defaults_snapshot: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        
        # Загрузка настроек
        self.load()
    
    def load(self) -> bool:
        """
        Загрузить настройки из JSON файла
        
        Returns:
            bool: True если успешно
        """
        if not self.settings_file.exists():
            self.logger.warning(f"Settings file not found: {self.settings_file}")
            self.logger.info("Creating default settings file...")
            self._create_default_file()
            return False
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Новая структура с разделением current/defaults
            if "current" in data:
                self._current = data["current"]
                self._defaults_snapshot = data.get("defaults_snapshot", copy.deepcopy(self._current))
                self._metadata = data.get("metadata", {})
            else:
                # Старая структура - мигрируем
                self._current = data
                self._defaults_snapshot = copy.deepcopy(data)
                self._metadata = {
                    "version": data.get("version", "4.9.5"),
                    "last_modified": datetime.now().isoformat()
                }
                # Сохраняем в новом формате
                self.save()
            
            self.logger.info(f"Settings loaded from {self.settings_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            return False
    
    def save(self) -> bool:
        """
        Сохранить текущие настройки в JSON файл
        
        Returns:
            bool: True если успешно
        """
        try:
            # Обновляем metadata
            self._metadata["last_modified"] = datetime.now().isoformat()
            
            # Структура файла
            data = {
                "current": self._current,
                "defaults_snapshot": self._defaults_snapshot,
                "metadata": self._metadata
            }
            
            # Сохраняем с отступами для читаемости
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Settings saved to {self.settings_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            return False
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Получить значение по пути (dot-notation)
        
        Args:
            path: Путь к параметру, например "graphics.lighting.key.brightness"
            default: Значение по умолчанию если параметр не найден
        
        Returns:
            Значение параметра или default
        
        Example:
            >>> manager.get("graphics.effects.bloom_intensity")
            0.5
        """
        keys = path.split('.')
        value = self._current
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, path: str, value: Any, auto_save: bool = True) -> bool:
        """
        Установить значение по пути
        
        Args:
            path: Путь к параметру
            value: Новое значение
            auto_save: Автоматически сохранить в файл
        
        Returns:
            bool: True если успешно
        
        Example:
            >>> manager.set("graphics.effects.bloom_intensity", 0.8)
            True
        """
        keys = path.split('.')
        current = self._current
        
        # Создаем промежуточные словари если нужно
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        # Устанавливаем значение
        current[keys[-1]] = value
        
        # Автосохранение
        if auto_save:
            return self.save()
        
        return True
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """
        Получить всю категорию настроек
        
        Args:
            category: Название категории ("graphics", "geometry", и т.д.)
        
        Returns:
            Словарь с настройками категории
        """
        return self._current.get(category, {})
    
    def set_category(self, category: str, data: Dict[str, Any], auto_save: bool = True) -> bool:
        """
        Установить всю категорию настроек
        
        Args:
            category: Название категории
            data: Словарь с настройками
            auto_save: Автоматически сохранить
        
        Returns:
            bool: True если успешно
        """
        self._current[category] = data
        
        if auto_save:
            return self.save()
        
        return True
    
    def reset_to_defaults(self, category: Optional[str] = None) -> bool:
        """
        Сбросить настройки к сохраненным дефолтам
        
        Args:
            category: Категория для сброса (None = сброс всего)
        
        Returns:
            bool: True если успешно
        """
        if category is None:
            # Сброс всех настроек
            self._current = copy.deepcopy(self._defaults_snapshot)
        else:
            # Сброс конкретной категории
            if category in self._defaults_snapshot:
                self._current[category] = copy.deepcopy(self._defaults_snapshot[category])
        
        return self.save()
    
    def save_current_as_defaults(self, category: Optional[str] = None) -> bool:
        """
        Сохранить текущие настройки как новые дефолты
        (кнопка "Сохранить как дефолт" в UI)
        
        Args:
            category: Категория для сохранения (None = сохранить все)
        
        Returns:
            bool: True если успешно
        """
        if category is None:
            # Сохраняем все текущие настройки как дефолты
            self._defaults_snapshot = copy.deepcopy(self._current)
        else:
            # Сохраняем конкретную категорию
            if category in self._current:
                self._defaults_snapshot[category] = copy.deepcopy(self._current[category])
        
        self.logger.info(f"Current settings saved as defaults (category={category or 'all'})")
        return self.save()
    
    def get_all_current(self) -> Dict[str, Any]:
        """
        Получить ВСЕ текущие настройки
        
        Returns:
            Словарь с полными настройками
        """
        return copy.deepcopy(self._current)
    
    def get_all_defaults(self) -> Dict[str, Any]:
        """
        Получить сохраненные дефолты
        
        Returns:
            Словарь с дефолтами
        """
        return copy.deepcopy(self._defaults_snapshot)
    
    def _create_default_file(self):
        """Создать файл настроек с базовыми дефолтами"""
        # Минимальная структура настроек
        self._current = {
            "graphics": {
                "lighting": {},
                "environment": {},
                "quality": {},
                "camera": {},
                "effects": {},
                "materials": {}
            },
            "geometry": {},
            "simulation": {},
            "ui": {}
        }
        
        self._defaults_snapshot = copy.deepcopy(self._current)
        self._metadata = {
            "version": "4.9.5",
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat()
        }
        
        # Создаем директорию если нужно
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем
        self.save()


# Singleton instance
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """
    Получить singleton instance SettingsManager
    
    Returns:
        SettingsManager: Единственный экземпляр менеджера
    """
    global _settings_manager
    
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    
    return _settings_manager
