#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт рефакторинга панелей на использование SettingsManager
Автоматическое обновление всех панелей для централизованного управления настройками

ЦЕЛЬ:
✅ Заменить жестко закодированные defaults на загрузку из SettingsManager
✅ Добавить автосохранение при изменениях
✅ Унифицировать методы reset_to_defaults() и load_settings()
✅ Сделать сброс настроек безопасным (загрузка из JSON defaults_snapshot)
"""

import re
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class PanelRefactorer:
    """Рефакторинг панели для использования SettingsManager"""

    def __init__(self, panel_file: Path):
        self.panel_file = panel_file
        self.panel_name = panel_file.stem
        self.content: str = ""
        self.modified = False

    def load(self) -> bool:
        """Загрузить содержимое панели"""
        try:
            with open(self.panel_file, "r", encoding="utf-8") as f:
                self.content = f.read()
            return True
        except Exception as e:
            logger.error(f"Failed to load {self.panel_file}: {e}")
            return False

    def save(self) -> bool:
        """Сохранить модифицированное содержимое"""
        if not self.modified:
            logger.info(f"{self.panel_name}: No changes needed")
            return True

        try:
            # Бэкап оригинала
            backup = self.panel_file.with_suffix(".py.backup")
            with open(backup, "w", encoding="utf-8") as f:
                # Читаем оригинал заново для бэкапа
                with open(self.panel_file, "r", encoding="utf-8") as orig:
                    f.write(orig.read())

            # Сохраняем модифицированный файл
            with open(self.panel_file, "w", encoding="utf-8") as f:
                f.write(self.content)

            logger.info(
                f"✅ {self.panel_name}: Refactored successfully (backup: {backup.name})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to save {self.panel_file}: {e}")
            return False

    def add_settings_manager_import(self) -> bool:
        """Добавить импорт SettingsManager если его нет"""
        if "from src.common.settings_manager import SettingsManager" in self.content:
            return False  # Уже есть

        # Ищем блок импортов
        import_pattern = r"(from\s+PySide6\.QtWidgets\s+import.*?\n)"

        match = re.search(import_pattern, self.content, re.MULTILINE)
        if match:
            insert_pos = match.end()
            import_line = "from src.common.settings_manager import SettingsManager\n"
            self.content = (
                self.content[:insert_pos] + import_line + self.content[insert_pos:]
            )
            self.modified = True
            return True

        return False

    def replace_init_defaults(self) -> bool:
        """Заменить _set_default_values() на _load_defaults_from_settings()"""
        # Ищем метод _set_default_values
        pattern = r"(\s+)def\s+_set_default_values\(self\):.*?\n\s+self\.parameters\.update\(defaults\)"

        if not re.search(pattern, self.content, re.DOTALL):
            return False

        # Заменяем на новый метод
        replacement = r"""\1def _load_defaults_from_settings(self):
\1    \"\"\"Загрузить defaults из SettingsManager\"\"\"
\1    category = self._get_category_name()
\1    defaults = self._settings_manager.get(category, self._get_fallback_defaults())
\1    self.parameters.update(defaults)
\1    self.logger.info(f"✅ {category.title()} defaults loaded from SettingsManager")"""

        self.content = re.sub(pattern, replacement, self.content, flags=re.DOTALL)
        self.modified = True
        return True

    def add_settings_manager_init(self) -> bool:
        """Добавить инициализацию _settings_manager в __init__"""
        init_pattern = r"(def\s+__init__\(self,\s*parent=None\):.*?\n\s+)(super\(\)\.__init__\(parent\))"

        match = re.search(init_pattern, self.content, re.DOTALL)
        if not match:
            return False

        # Проверяем, нет ли уже _settings_manager
        if "self._settings_manager = SettingsManager()" in self.content:
            return False

        # Добавляем после super().__init__()
        insert_text = f"{match.group(1)}{match.group(2)}\n        \n        # ✅ НОВОЕ: Используем SettingsManager\n        self._settings_manager = SettingsManager()\n        "

        self.content = self.content.replace(match.group(0), insert_text)
        self.modified = True
        return True

    def update_reset_method(self) -> bool:
        """Обновить метод _reset_to_defaults для использования SettingsManager"""
        reset_pattern = r"(\s+)@Slot\(\)\s+def\s+_reset_to_defaults\(self\):.*?self\.parameters\.update\(defaults\)"

        if not re.search(reset_pattern, self.content, re.DOTALL):
            return False

        category_name = self._guess_category_name()

        replacement = rf"""\1@Slot()
\1def _reset_to_defaults(self):
\1    \"\"\"Сбросить все параметры к значениям по умолчанию из JSON\"\"\"
\1    self.logger.info("🔄 Resetting {category_name} to defaults from SettingsManager")
\1
\1    # ✅ НОВОЕ: Сброс через SettingsManager
\1    self._settings_manager.reset_to_defaults(category="{category_name}")
\1    self.parameters = self._settings_manager.get("{category_name}")"""

        self.content = re.sub(reset_pattern, replacement, self.content, flags=re.DOTALL)
        self.modified = True
        return True

    def update_set_parameters(self) -> bool:
        """Обновить set_parameters для сохранения через SettingsManager"""
        pattern = r"(def\s+set_parameters\(self,\s*params:\s*dict\):.*?)(self\.parameters\.update\(params\))"

        match = re.search(pattern, self.content, re.DOTALL)
        if not match:
            return False

        # Проверяем, нет ли уже сохранения через SettingsManager
        if "_settings_manager.set" in match.group(0):
            return False

        category_name = self._guess_category_name()

        replacement = f'{match.group(1)}{match.group(2)}\n        \n        # ✅ НОВОЕ: Сохраняем через SettingsManager\n        self._settings_manager.set("{category_name}", self.parameters, auto_save=True)\n        '

        self.content = self.content.replace(match.group(0), replacement)
        self.modified = True
        return True

    def _guess_category_name(self) -> str:
        """Определить имя категории по имени файла"""
        name = self.panel_name.replace("panel_", "").replace("_panel", "")
        if name == "graphics":
            return "graphics"
        elif name == "geometry":
            return "geometry"
        elif name == "pneumo":
            return "pneumatic"
        elif name == "modes":
            return "modes"
        else:
            return name

    def refactor(self) -> bool:
        """Выполнить полный рефакторинг панели"""
        if not self.load():
            return False

        logger.info(f"📝 Refactoring {self.panel_name}...")

        # Применяем рефакторинг
        changes = []

        if self.add_settings_manager_import():
            changes.append("Added SettingsManager import")

        if self.add_settings_manager_init():
            changes.append("Added _settings_manager initialization")

        if self.replace_init_defaults():
            changes.append(
                "Replaced _set_default_values with _load_defaults_from_settings"
            )

        if self.update_reset_method():
            changes.append("Updated _reset_to_defaults method")

        if self.update_set_parameters():
            changes.append("Updated set_parameters method")

        if changes:
            logger.info(f"  Changes: {', '.join(changes)}")

        return self.save()


def main():
    """Основная функция рефакторинга"""
    logger.info("🔧 Starting panel refactoring to SettingsManager...")
    logger.info("=" * 60)

    # Панели для рефакторинга
    panels_dir = Path("src/ui/panels")
    panel_files = [
        panels_dir / "panel_geometry.py",
        panels_dir / "panel_pneumo.py",
        panels_dir / "panel_modes.py",
        panels_dir / "panel_graphics.py",
    ]

    results = []

    for panel_file in panel_files:
        if not panel_file.exists():
            logger.warning(f"⚠️ Panel not found: {panel_file}")
            continue

        refactorer = PanelRefactorer(panel_file)
        success = refactorer.refactor()

        results.append((panel_file.stem, success))

    # Итоговая статистика
    logger.info("=" * 60)
    logger.info("📊 REFACTORING SUMMARY")
    logger.info("=" * 60)

    successful = sum(1 for _, success in results if success)
    total = len(results)

    for panel_name, success in results:
        status = "✅" if success else "❌"
        logger.info(f"  {status} {panel_name}")

    logger.info("=" * 60)
    logger.info(f"✅ Успешно: {successful}/{total}")
    logger.info("=" * 60)

    if successful == total:
        logger.info("🎉 ВСЕ ПАНЕЛИ УСПЕШНО РЕФАКТОРИРОВАНЫ!")
        logger.info("\nСледующие шаги:")
        logger.info("1. Проверить компиляцию: python -m compileall src/ui/panels/")
        logger.info("2. Запустить тесты: pytest tests/")
        logger.info("3. Запустить приложение: python app.py")
        logger.info("4. Проверить работу кнопки 'Сброс' в каждой панели")
    else:
        logger.warning("⚠️ Некоторые панели не удалось рефакторировать")
        logger.info("Проверьте логи выше для деталей")


if __name__ == "__main__":
    main()
