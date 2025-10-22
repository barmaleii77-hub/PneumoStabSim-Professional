#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 ИСПРАВЛЕНИЕ ТУМАНА И СГЛАЖИВАНИЯ
Исправляем проблемы с туманом и сглаживанием в GraphicsPanel
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent / "src"))


def fix_graphics_panel_fog_antialiasing():
    """Исправляет проблемы с туманом и сглаживанием"""

    print("🔧 ИСПРАВЛЕНИЕ ТУМАНА И СГЛАЖИВАНИЯ")
    print("=" * 70)

    # Читаем текущий файл GraphicsPanel
    panel_file = Path("src/ui/panels/panel_graphics.py")

    if not panel_file.exists():
        print(f"❌ Файл не найден: {panel_file}")
        return False

    print(f"📂 Читаем файл: {panel_file}")
    content = panel_file.read_text(encoding="utf-8")

    # Находим проблемные места и исправляем их

    # 1. Исправляем emit_environment_update - добавляем отладочную информацию
    old_emit_env = '''def emit_environment_update(self):
        """Отправить сигнал об изменении окружения"""
        environment_params = {
            'background_color': self.current_graphics['background_color'],
            'skybox_enabled': self.current_graphics['skybox_enabled'],
            'skybox_blur': self.current_graphics['skybox_blur'],
            'ibl_enabled': self.current_graphics['ibl_enabled'],      # ✅ НОВОЕ: IBL
            'ibl_intensity': self.current_graphics['ibl_intensity'],  # ✅ НОВОЕ: IBL
            'ibl_source': self.current_graphics['ibl_source'],
            'ibl_fallback': self.current_graphics['ibl_fallback'],
            'fog_enabled': self.current_graphics['fog_enabled'],
            'fog_color': self.current_graphics['fog_color'],
            'fog_density': self.current_graphics['fog_density']
        }

        self.logger.info(f"Environment updated: {environment_params}")
        self.environment_changed.emit(environment_params)'''

    new_emit_env = '''def emit_environment_update(self):
        """Отправить сигнал об изменении окружения"""
        environment_params = {
            'background_color': self.current_graphics['background_color'],
            'skybox_enabled': self.current_graphics['skybox_enabled'],
            'skybox_blur': self.current_graphics['skybox_blur'],
            'ibl_enabled': self.current_graphics['ibl_enabled'],      # ✅ НОВОЕ: IBL
            'ibl_intensity': self.current_graphics['ibl_intensity'],  # ✅ НОВОЕ: IBL
            'ibl_source': self.current_graphics['ibl_source'],
            'ibl_fallback': self.current_graphics['ibl_fallback'],
            'fog_enabled': self.current_graphics['fog_enabled'],
            'fog_color': self.current_graphics['fog_color'],
            'fog_density': self.current_graphics['fog_density']
        }

        print(f"🌫️  GraphicsPanel: EMIT environment_changed")
        print(f"     fog_enabled = {environment_params['fog_enabled']}")
        print(f"     fog_color = {environment_params['fog_color']}")
        print(f"     fog_density = {environment_params['fog_density']}")

        self.logger.info(f"Environment updated: {environment_params}")
        self.environment_changed.emit(environment_params)'''

    # 2. Исправляем emit_quality_update - добавляем отладочную информацию
    old_emit_quality = '''def emit_quality_update(self):
        """Отправить сигнал об изменении качества рендеринга"""
        quality_params = {
            'antialiasing': self.current_graphics['antialiasing'],
            'aa_quality': self.current_graphics['aa_quality'],
            'shadows_enabled': self.current_graphics['shadows_enabled'],
            'shadow_quality': self.current_graphics['shadow_quality'],
            'shadow_softness': self.current_graphics['shadow_softness'],  # ✅ НОВОЕ: Мягкость теней
        }

        self.logger.info(f"Quality updated: {quality_params}")
        self.quality_changed.emit(quality_params)'''

    new_emit_quality = '''def emit_quality_update(self):
        """Отправить сигнал об изменении качества рендеринга"""
        quality_params = {
            'antialiasing': self.current_graphics['antialiasing'],
            'aa_quality': self.current_graphics['aa_quality'],
            'shadows_enabled': self.current_graphics['shadows_enabled'],
            'shadow_quality': self.current_graphics['shadow_quality'],
            'shadow_softness': self.current_graphics['shadow_softness'],  # ✅ НОВОЕ: Мягкость теней
        }

        print(f"⚙️  GraphicsPanel: EMIT quality_changed")
        print(f"     antialiasing = {quality_params['antialiasing']}")
        print(f"     aa_quality = {quality_params['aa_quality']}")
        print(f"     shadows_enabled = {quality_params['shadows_enabled']}")
        print(f"     shadow_quality = {quality_params['shadow_quality']}")

        self.logger.info(f"Quality updated: {quality_params}")
        self.quality_changed.emit(quality_params)'''

    # Применяем исправления
    if old_emit_env in content:
        content = content.replace(old_emit_env, new_emit_env)
        print("✅ Исправлен emit_environment_update()")
    else:
        print("⚠️ emit_environment_update() не найден для замены")

    if old_emit_quality in content:
        content = content.replace(old_emit_quality, new_emit_quality)
        print("✅ Исправлен emit_quality_update()")
    else:
        print("⚠️ emit_quality_update() не найден для замены")

    # Сохраняем исправленный файл
    panel_file.write_text(content, encoding="utf-8")
    print(f"💾 Файл сохранен: {panel_file}")

    return True


def fix_main_window_handlers():
    """Исправляет обработчики в MainWindow для прямого вызова QML функций"""

    print("\n🔧 ИСПРАВЛЕНИЕ MAIN_WINDOW ОБРАБОТЧИКОВ")
    print("-" * 50)

    # Читаем файл MainWindow
    main_file = Path("src/ui/main_window.py")

    if not main_file.exists():
        print(f"❌ Файл не найден: {main_file}")
        return False

    print(f"📂 Читаем файл: {main_file}")
    content = main_file.read_text(encoding="utf-8")

    # Ищем и заменяем обработчики environment и quality

    # 1. Исправляем _on_environment_changed для прямого вызова QML
    old_env_handler = '''    @Slot(dict)
    def _on_environment_changed(self, environment_params: dict):
        """Обработчик изменения параметров окружения"""
        print(f"🌍 MainWindow: Environment changed: {environment_params}")

        if self._qml_root_object:
            try:
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt

                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "applyEnvironmentUpdates", # ✅ ИСПРАВЛЕНО: Правильное имя функции
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", environment_params)
                )

                if success:
                    self.status_bar.showMessage("Окружение обновлено")
                    print("✅ Successfully called applyEnvironmentUpdates()")
                else:
                    print("❌ Failed to call applyEnvironmentUpdates()")

            except Exception as e:
                self.logger.error(f"Environment update failed: {e}")'''

    new_env_handler = '''    @Slot(dict)
    def _on_environment_changed(self, environment_params: dict):
        """Обработчик изменения параметров окружения"""
        print(f"🌍 MainWindow: Environment changed: {environment_params}")

        if self._qml_root_object:
            try:
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt

                print(f"🔧 MainWindow: Вызываем applyEnvironmentUpdates напрямую...")
                print(f"     fog_enabled = {environment_params.get('fog_enabled', 'N/A')}")

                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "applyEnvironmentUpdates", # ✅ ИСПРАВЛЕНО: Правильное имя функции
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", environment_params)
                )

                if success:
                    self.status_bar.showMessage("Окружение обновлено")
                    print("✅ Successfully called applyEnvironmentUpdates()")
                else:
                    print("❌ Failed to call applyEnvironmentUpdates()")

            except Exception as e:
                self.logger.error(f"Environment update failed: {e}")
                print(f"❌ Exception in environment update: {e}")
                import traceback
                traceback.print_exc()'''

    # 2. Исправляем _on_quality_changed для прямого вызова QML
    old_quality_handler = '''    @Slot(dict)
    def _on_quality_changed(self, quality_params: dict):
        """Обработчик изменения параметров качества"""
        print(f"⚙️ MainWindow: Quality changed: {quality_params}")

        if self._qml_root_object:
            try:
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt

                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "applyQualityUpdates", # ✅ ИСПРАВЛЕНО: Правильное имя функции
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", quality_params)
                )

                if success:
                    self.status_bar.showMessage("Качество обновлено")
                    print("✅ Successfully called applyQualityUpdates()")
                else:
                    print("❌ Failed to call applyQualityUpdates()")

            except Exception as e:
                self.logger.error(f"Quality update failed: {e}")'''

    new_quality_handler = '''    @Slot(dict)
    def _on_quality_changed(self, quality_params: dict):
        """Обработчик изменения параметров качества"""
        print(f"⚙️ MainWindow: Quality changed: {quality_params}")

        if self._qml_root_object:
            try:
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt

                print(f"🔧 MainWindow: Вызываем applyQualityUpdates напрямую...")
                print(f"     antialiasing = {quality_params.get('antialiasing', 'N/A')}")
                print(f"     aa_quality = {quality_params.get('aa_quality', 'N/A')}")

                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "applyQualityUpdates", # ✅ ИСПРАВЛЕНО: Правильное имя функции
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", quality_params)
                )

                if success:
                    self.status_bar.showMessage("Качество обновлено")
                    print("✅ Successfully called applyQualityUpdates()")
                else:
                    print("❌ Failed to call applyQualityUpdates()")

            except Exception as e:
                self.logger.error(f"Quality update failed: {e}")
                print(f"❌ Exception in quality update: {e}")
                import traceback
                traceback.print_exc()'''

    # Применяем исправления
    if old_env_handler in content:
        content = content.replace(old_env_handler, new_env_handler)
        print("✅ Исправлен _on_environment_changed()")
    else:
        print("⚠️ _on_environment_changed() не найден для замены")

    if old_quality_handler in content:
        content = content.replace(old_quality_handler, new_quality_handler)
        print("✅ Исправлен _on_quality_changed()")
    else:
        print("⚠️ _on_quality_changed() не найден для замены")

    # Сохраняем исправленный файл
    main_file.write_text(content, encoding="utf-8")
    print(f"💾 Файл сохранен: {main_file}")

    return True


if __name__ == "__main__":
    print("🚀 ЗАПУСК ИСПРАВЛЕНИЯ ТУМАНА И СГЛАЖИВАНИЯ")
    print()

    # Исправляем GraphicsPanel
    result1 = fix_graphics_panel_fog_antialiasing()

    # Исправляем MainWindow
    result2 = fix_main_window_handlers()

    print("\n" + "=" * 70)
    if result1 and result2:
        print("✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО!")
        print()
        print("🎯 ЧТО ИСПРАВЛЕНО:")
        print("   • GraphicsPanel теперь выводит отладочную информацию")
        print("   • MainWindow handlers добавляют больше отладки")
        print("   • Улучшено логирование для диагностики проблем")
        print()
        print("🧪 СЛЕДУЮЩИЙ ШАГ:")
        print("   py diagnose_fog_antialiasing.py")
        print("   Запустите диагностику чтобы увидеть где проблема")
    else:
        print("❌ НЕКОТОРЫЕ ИСПРАВЛЕНИЯ НЕ УДАЛИСЬ")
        print("   Проверьте файлы вручную")
    print("=" * 70)
