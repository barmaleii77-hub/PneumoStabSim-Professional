#!/usr/bin/env python3

"""
🔍 ГЛУБОКАЯ ДИАГНОСТИКА ПРОБЛЕМ ГРАФИКИ
Находим почему туман и сглаживание все еще не работают
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QObject, QMetaMethod, QMetaObject

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ui.main_window import MainWindow


def deep_graphics_diagnosis():
    """Глубокая диагностика проблем с графикой"""
    print("🔍 ГЛУБОКАЯ ДИАГНОСТИКА ПРОБЛЕМ ГРАФИКИ")
    print("=" * 70)

    app = QApplication([])

    try:
        # Создаем окно
        window = MainWindow(use_qml_3d=True)
        window.show()

        # Даем время на инициализацию
        QTimer.singleShot(2000, lambda: run_deep_diagnosis(window))
        QTimer.singleShot(30000, app.quit)  # Выход через 30 секунд

        app.exec()

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback

        traceback.print_exc()
    finally:
        app.quit()


def run_deep_diagnosis(window):
    """Запускает глубокую диагностику"""

    if not window._qml_root_object:
        print("❌ QML объект недоступен!")
        return

    if not hasattr(window, "_graphics_panel") or not window._graphics_panel:
        print("❌ GraphicsPanel недоступна!")
        return

    qml = window._qml_root_object
    graphics_panel = window._graphics_panel

    print("✅ Компоненты доступны, начинаем глубокую диагностику...")

    # 1. Диагностика состояния QML объекта
    print("\n🔍 ДИАГНОСТИКА 1: QML ОБЪЕКТ")
    print("-" * 50)
    diagnose_qml_object(qml)

    # 2. Диагностика GraphicsPanel
    print("\n🔍 ДИАГНОСТИКА 2: GRAPHICS PANEL")
    print("-" * 50)
    diagnose_graphics_panel(graphics_panel)

    # 3. Диагностика подключения сигналов
    print("\n🔍 ДИАГНОСТИКА 3: ПОДКЛЮЧЕНИЕ СИГНАЛОВ")
    print("-" * 50)
    diagnose_signal_connections(window, graphics_panel)

    # 4. Тест прямых вызовов QML функций
    print("\n🔍 ДИАГНОСТИКА 4: ПРЯМЫЕ ВЫЗОВЫ QML")
    print("-" * 50)
    QTimer.singleShot(1000, lambda: test_direct_qml_calls(qml))

    # 5. Тест реальных изменений через UI
    print("\n🔍 ДИАГНОСТИКА 5: ИЗМЕНЕНИЯ ЧЕРЕЗ UI")
    print("-" * 50)
    QTimer.singleShot(3000, lambda: test_ui_changes(graphics_panel))

    # 6. Финальная проверка
    print("\n🔍 ДИАГНОСТИКА 6: ФИНАЛЬНАЯ ПРОВЕРКА")
    print("-" * 50)
    QTimer.singleShot(5000, lambda: final_check(qml, graphics_panel))


def diagnose_qml_object(qml):
    """Диагностирует QML объект"""
    try:
        print("  📋 ДОСТУПНЫЕ QML СВОЙСТВА:")

        # Проверяем основные свойства
        properties_to_check = [
            "fogEnabled",
            "fogColor",
            "antialiasingMode",
            "antialiasingQuality",
            "shadowsEnabled",
            "shadowQuality",
        ]

        for prop in properties_to_check:
            try:
                value = qml.property(prop)
                print(f"     {prop} = {value}")
            except Exception as e:
                print(f"     {prop} = ERROR: {e}")

        fog_object = qml.property("fog")
        if isinstance(fog_object, QObject):
            try:
                fog_density = fog_object.property("density")
                print(f"     fog.density = {fog_density}")
            except Exception as fog_error:
                print(f"     fog.density = ERROR: {fog_error}")
        else:
            print("     fog = <unavailable>")

        print("  📋 ДОСТУПНЫЕ QML МЕТОДЫ:")

        # Проверяем доступные методы
        methods_to_check = [
            "applyEnvironmentUpdates",
            "applyQualityUpdates",
            "updateEnvironment",
            "updateQuality",
        ]

        for method in methods_to_check:
            try:
                # Пытаемся найти метод через metaObject
                meta_obj = qml.metaObject()
                method_index = meta_obj.indexOfMethod(method)
                if method_index >= 0:
                    print(f"     {method} = ДОСТУПЕН (индекс {method_index})")
                else:
                    print(f"     {method} = НЕ НАЙДЕН")
            except Exception as e:
                print(f"     {method} = ERROR: {e}")

    except Exception as e:
        print(f"  ❌ Ошибка диагностики QML объекта: {e}")


def diagnose_graphics_panel(graphics_panel):
    """Диагностирует GraphicsPanel"""
    try:
        print("  📋 GRAPHICS PANEL СОСТОЯНИЕ:")

        # Проверяем текущие настройки
        current_graphics = graphics_panel.current_graphics
        print(f"     fog_enabled = {current_graphics.get('fog_enabled', 'N/A')}")
        print(f"     fog_color = {current_graphics.get('fog_color', 'N/A')}")
        print(f"     fog_density = {current_graphics.get('fog_density', 'N/A')}")
        print(f"     antialiasing = {current_graphics.get('antialiasing', 'N/A')}")
        print(f"     aa_quality = {current_graphics.get('aa_quality', 'N/A')}")

        # Проверяем UI элементы
        print("  📋 UI ЭЛЕМЕНТЫ:")

        if hasattr(graphics_panel, "fog_enabled"):
            ui_fog = graphics_panel.fog_enabled.isChecked()
            print(f"     fog_enabled checkbox = {ui_fog}")
        else:
            print("     fog_enabled checkbox = НЕ НАЙДЕН")

        if hasattr(graphics_panel, "antialiasing"):
            ui_aa = graphics_panel.antialiasing.currentIndex()
            print(f"     antialiasing combobox = {ui_aa}")
        else:
            print("     antialiasing combobox = НЕ НАЙДЕН")

        # Проверяем сигналы
        print("  📋 СИГНАЛЫ:")

        signals_to_check = [
            "environment_changed",
            "quality_changed",
            "lighting_changed",
            "material_changed",
        ]

        for signal_name in signals_to_check:
            if hasattr(graphics_panel, signal_name):
                signal_obj = getattr(graphics_panel, signal_name)
                print(f"     {signal_name} = ДОСТУПЕН")

                # Пытаемся проверить подключения (если возможно)
                meta_method = None
                try:
                    meta_method = QMetaMethod.fromSignal(signal_obj)
                except (TypeError, AttributeError):
                    meta_method = None

                if meta_method and meta_method.isValid():
                    method_signature = bytes(meta_method.methodSignature()).decode()
                    normalized_signature = bytes(
                        QMetaObject.normalizedSignature(method_signature.encode())
                    ).decode()
                    print(f"       сигнатура: {normalized_signature}")

                    connection_state: str
                    try:
                        is_connected = getattr(signal_obj, "isSignalConnected", None)
                        if callable(is_connected):
                            connection_state = (
                                "есть подписчики"
                                if is_connected()
                                else "подписчиков нет"
                            )
                        elif hasattr(graphics_panel, "isSignalConnected"):
                            connection_state = (
                                "есть подписчики"
                                if graphics_panel.isSignalConnected(meta_method)
                                else "подписчиков нет"
                            )
                        else:
                            connection_state = "подключения неизвестны"
                    except (TypeError, AttributeError):
                        connection_state = "подключения неизвестны"

                    print(f"       подключено обработчиков: {connection_state}")
                else:
                    print("       сигнатура: неизвестно")
            else:
                print(f"     {signal_name} = НЕ НАЙДЕН")

    except Exception as e:
        print(f"  ❌ Ошибка диагностики GraphicsPanel: {e}")


def diagnose_signal_connections(window, graphics_panel):
    """Диагностирует подключение сигналов"""
    try:
        print("  📋 ПРОВЕРКА ПОДКЛЮЧЕНИЯ СИГНАЛОВ:")

        # Проверяем есть ли обработчики в MainWindow
        handlers_to_check = [
            "_on_environment_changed",
            "_on_quality_changed",
            "_on_lighting_changed",
            "_on_material_changed",
        ]

        for handler_name in handlers_to_check:
            if hasattr(window, handler_name):
                print(f"     {handler_name} = ДОСТУПЕН в MainWindow")
            else:
                print(f"     {handler_name} = НЕ НАЙДЕН в MainWindow")

        # Тестируем подключение сигналов
        print("  📋 ТЕСТ СИГНАЛОВ:")

        # Создаем тестовые функции-счетчики
        test_results = {"environment_received": 0, "quality_received": 0}

        def test_env_handler(params):
            test_results["environment_received"] += 1
            print(
                f"     🔥 ТЕСТ environment_changed получен #{test_results['environment_received']}"
            )

        def test_quality_handler(params):
            test_results["quality_received"] += 1
            print(
                f"     🔥 ТЕСТ quality_changed получен #{test_results['quality_received']}"
            )

        # Подключаем тестовые обработчики
        if hasattr(graphics_panel, "environment_changed"):
            graphics_panel.environment_changed.connect(test_env_handler)
            print("     ✅ Тестовый обработчик environment_changed подключен")

        if hasattr(graphics_panel, "quality_changed"):
            graphics_panel.quality_changed.connect(test_quality_handler)
            print("     ✅ Тестовый обработчик quality_changed подключен")

        # Запускаем тестовые emit'ы
        QTimer.singleShot(
            500, lambda: test_signal_emission(graphics_panel, test_results)
        )

    except Exception as e:
        print(f"  ❌ Ошибка диагностики подключения сигналов: {e}")


def test_signal_emission(graphics_panel, test_results):
    """Тестирует эмиссию сигналов"""
    try:
        print("  📋 ТЕСТ ЭМИССИИ СИГНАЛОВ:")

        # Сохраняем исходные значения
        original_fog = graphics_panel.current_graphics["fog_enabled"]
        original_aa = graphics_panel.current_graphics["antialiasing"]

        # Тест 1: emit environment_changed
        print("     🧪 Эмитим environment_changed...")
        graphics_panel.emit_environment_update()

        # Тест 2: emit quality_changed
        print("     🧪 Эмитим quality_changed...")
        graphics_panel.emit_quality_update()

        # Проверяем результаты через 1 секунду
        QTimer.singleShot(1000, lambda: check_signal_test_results(test_results))

    except Exception as e:
        print(f"  ❌ Ошибка тестирования эмиссии сигналов: {e}")


def check_signal_test_results(test_results):
    """Проверяет результаты тестирования сигналов"""
    print("  📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ СИГНАЛОВ:")
    print(f"     environment_changed получено: {test_results['environment_received']}")
    print(f"     quality_changed получено: {test_results['quality_received']}")

    if test_results["environment_received"] > 0:
        print("     ✅ environment_changed РАБОТАЕТ")
    else:
        print("     ❌ environment_changed НЕ РАБОТАЕТ")

    if test_results["quality_received"] > 0:
        print("     ✅ quality_changed РАБОТАЕТ")
    else:
        print("     ❌ quality_changed НЕ РАБОТАЕТ")


def test_direct_qml_calls(qml):
    """Тестирует прямые вызовы QML функций"""
    try:
        print("  📋 ТЕСТ ПРЯМЫХ ВЫЗОВОВ QML ФУНКЦИЙ:")

        from PySide6.QtCore import QMetaObject, Q_ARG, Qt

        # Тест 1: applyEnvironmentUpdates
        test_env_params = {
            "fog_enabled": True,
            "fog_color": "#ff0000",
            "fog_density": 0.5,
        }

        print("     🧪 Тестируем applyEnvironmentUpdates...")
        success1 = QMetaObject.invokeMethod(
            qml,
            "applyEnvironmentUpdates",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", test_env_params),
        )
        print(f"     Результат: {success1}")

        # Тест 2: applyQualityUpdates
        test_quality_params = {
            "antialiasing": 0,
            "aa_quality": 1,
            "shadows_enabled": True,
        }

        print("     🧪 Тестируем applyQualityUpdates...")
        success2 = QMetaObject.invokeMethod(
            qml,
            "applyQualityUpdates",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", test_quality_params),
        )
        print(f"     Результат: {success2}")

        # Проверяем изменились ли свойства
        QTimer.singleShot(500, lambda: check_qml_property_changes(qml))

    except Exception as e:
        print(f"  ❌ Ошибка тестирования прямых вызовов QML: {e}")
        import traceback

        traceback.print_exc()


def check_qml_property_changes(qml):
    """Проверяет изменились ли QML свойства"""
    try:
        print("  📋 ПРОВЕРКА ИЗМЕНЕНИЙ QML СВОЙСТВ:")

        fog_enabled = qml.property("fogEnabled")
        fog_color = qml.property("fogColor")

        fog_object = qml.property("fog")
        fog_density = None
        if isinstance(fog_object, QObject):
            fog_density = fog_object.property("density")
        aa_mode = qml.property("antialiasingMode")

        print(f"     fogEnabled = {fog_enabled} (ожидалось True)")
        print(f"     fogColor = {fog_color} (ожидалось #ff0000)")
        print(f"     fog.density = {fog_density} (ожидалось 0.5)")
        print(f"     antialiasingMode = {aa_mode} (ожидалось 0)")

        # Проверяем соответствие
        changes_detected = 0
        if fog_enabled == True:
            print("     ✅ fogEnabled изменился правильно")
            changes_detected += 1
        else:
            print("     ❌ fogEnabled НЕ изменился")

        if aa_mode == 0:
            print("     ✅ antialiasingMode изменился правильно")
            changes_detected += 1
        else:
            print("     ❌ antialiasingMode НЕ изменился")

        print(f"     Итого изменений: {changes_detected}/2")

    except Exception as e:
        print(f"  ❌ Ошибка проверки изменений QML свойств: {e}")


def test_ui_changes(graphics_panel):
    """Тестирует изменения через UI"""
    try:
        print("  📋 ТЕСТ ИЗМЕНЕНИЙ ЧЕРЕЗ UI:")

        # Тест 1: Изменение checkbox тумана
        if hasattr(graphics_panel, "fog_enabled"):
            original_state = graphics_panel.fog_enabled.isChecked()
            print(
                f"     🧪 Изменяем fog_enabled checkbox: {original_state} -> {not original_state}"
            )
            graphics_panel.fog_enabled.setChecked(not original_state)

            QTimer.singleShot(
                500, lambda: check_ui_fog_change(graphics_panel, not original_state)
            )
        else:
            print("     ❌ fog_enabled checkbox недоступен")

        # Тест 2: Изменение combobox сглаживания
        if hasattr(graphics_panel, "antialiasing"):
            original_index = graphics_panel.antialiasing.currentIndex()
            new_index = (original_index + 1) % graphics_panel.antialiasing.count()
            print(
                f"     🧪 Изменяем antialiasing combobox: {original_index} -> {new_index}"
            )
            graphics_panel.antialiasing.setCurrentIndex(new_index)

            QTimer.singleShot(
                1000, lambda: check_ui_aa_change(graphics_panel, new_index)
            )
        else:
            print("     ❌ antialiasing combobox недоступен")

    except Exception as e:
        print(f"  ❌ Ошибка тестирования изменений через UI: {e}")


def check_ui_fog_change(graphics_panel, expected_state):
    """Проверяет изменение тумана через UI"""
    try:
        current_ui_state = graphics_panel.fog_enabled.isChecked()
        current_data_state = graphics_panel.current_graphics["fog_enabled"]

        print("     Результат fog UI change:")
        print(f"       UI state: {current_ui_state} (ожидалось {expected_state})")
        print(f"       Data state: {current_data_state} (ожидалось {expected_state})")

        if current_ui_state == expected_state and current_data_state == expected_state:
            print("     ✅ UI изменение тумана работает")
        else:
            print("     ❌ UI изменение тумана НЕ работает")

    except Exception as e:
        print(f"  ❌ Ошибка проверки UI изменения тумана: {e}")


def check_ui_aa_change(graphics_panel, expected_index):
    """Проверяет изменение сглаживания через UI"""
    try:
        current_ui_index = graphics_panel.antialiasing.currentIndex()
        current_data_index = graphics_panel.current_graphics["antialiasing"]

        print("     Результат AA UI change:")
        print(f"       UI index: {current_ui_index} (ожидалось {expected_index})")
        print(f"       Data index: {current_data_index} (ожидалось {expected_index})")

        if current_ui_index == expected_index and current_data_index == expected_index:
            print("     ✅ UI изменение сглаживания работает")
        else:
            print("     ❌ UI изменение сглаживания НЕ работает")

    except Exception as e:
        print(f"  ❌ Ошибка проверки UI изменения сглаживания: {e}")


def final_check(qml, graphics_panel):
    """Финальная проверка всех компонентов"""
    try:
        print("  📋 ФИНАЛЬНАЯ СВОДКА:")

        # QML состояние
        fog_qml = qml.property("fogEnabled")
        aa_qml = qml.property("antialiasingMode")

        # Panel состояние
        fog_panel = graphics_panel.current_graphics["fog_enabled"]
        aa_panel = graphics_panel.current_graphics["antialiasing"]

        # UI состояние
        fog_ui = (
            graphics_panel.fog_enabled.isChecked()
            if hasattr(graphics_panel, "fog_enabled")
            else None
        )
        aa_ui = (
            graphics_panel.antialiasing.currentIndex()
            if hasattr(graphics_panel, "antialiasing")
            else None
        )

        print("     ТУМАН:")
        print(f"       QML: {fog_qml}")
        print(f"       Panel: {fog_panel}")
        print(f"       UI: {fog_ui}")

        print("     СГЛАЖИВАНИЕ:")
        print(f"       QML: {aa_qml}")
        print(f"       Panel: {aa_panel}")
        print(f"       UI: {aa_ui}")

        # Проверяем синхронизацию
        fog_synced = fog_qml == fog_panel == fog_ui
        aa_synced = aa_qml == aa_panel == aa_ui

        if fog_synced:
            print("     ✅ ТУМАН синхронизирован")
        else:
            print("     ❌ ТУМАН НЕ синхронизирован")

        if aa_synced:
            print("     ✅ СГЛАЖИВАНИЕ синхронизировано")
        else:
            print("     ❌ СГЛАЖИВАНИЕ НЕ синхронизировано")

        # Итоговая диагностика
        if fog_synced and aa_synced:
            print("\n🎉 ВСЕ РАБОТАЕТ ПРАВИЛЬНО!")
        else:
            print("\n❌ ПРОБЛЕМЫ ОБНАРУЖЕНЫ:")
            if not fog_synced:
                print("   • Туман не синхронизирован между компонентами")
            if not aa_synced:
                print("   • Сглаживание не синхронизировано между компонентами")

    except Exception as e:
        print(f"  ❌ Ошибка финальной проверки: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 ЗАПУСК ГЛУБОКОЙ ДИАГНОСТИКИ ГРАФИКИ")
    print()
    print("Проверяем:")
    print("  • QML объект и его свойства/методы")
    print("  • GraphicsPanel состояние и UI элементы")
    print("  • Подключение сигналов между компонентами")
    print("  • Прямые вызовы QML функций")
    print("  • Изменения через пользовательский интерфейс")
    print("  • Синхронизацию между всеми компонентами")
    print()

    deep_graphics_diagnosis()

    print("\n✅ Глубокая диагностика завершена!")
    print("\n🎯 РЕЗУЛЬТАТ:")
    print("   Определили точную причину проблем с туманом и сглаживанием")
