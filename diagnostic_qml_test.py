#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностический тест QML - проверяем какой файл загружается и работают ли эффекты
"""
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl


def test_qml_loading():
    """Тестируем загрузку QML файлов и проверяем доступность свойств"""

    app = QApplication([])

    print("🔍 ДИАГНОСТИКА QML ФАЙЛОВ")
    print("=" * 50)

    qml_files = [
        ("main_optimized.qml", "assets/qml/main_optimized.qml"),
        ("main.qml", "assets/qml/main.qml"),
    ]

    for name, path in qml_files:
        print(f"\n📁 Тестируем: {name}")
        print("-" * 30)

        qml_path = Path(path)
        if not qml_path.exists():
            print(f"❌ Файл не найден: {qml_path}")
            continue

        try:
            # Создаем QQuickWidget
            widget = QQuickWidget()
            widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)

            # Загружаем QML
            qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
            widget.setSource(qml_url)

            # Проверяем статус загрузки
            if widget.status() == QQuickWidget.Status.Error:
                errors = widget.errors()
                print("❌ Ошибки загрузки QML:")
                for error in errors:
                    print(f"   {error}")
                continue

            # Получаем root object
            root = widget.rootObject()
            if not root:
                print("❌ Не удалось получить root object")
                continue

            print("✅ QML загружен успешно")

            # Проверяем ключевые свойства для эффектов
            test_properties = {
                "glassIOR": "Коэффициент преломления стекла",
                "userFrameLength": "Длина рамы",
                "userTrackWidth": "Колея",
                "userRodPosition": "Положение штока",
                "bloomEnabled": "Bloom эффект",
                "ssaoEnabled": "SSAO эффект",
                "metalRoughness": "Шероховатость металла",
                "glassOpacity": "Прозрачность стекла",
            }

            print("\n🔧 Проверка свойств:")
            available_props = []
            missing_props = []

            for prop, desc in test_properties.items():
                if root.property(prop) is not None:
                    value = root.property(prop)
                    available_props.append(f"   ✅ {prop}: {value} ({desc})")
                else:
                    missing_props.append(f"   ❌ {prop}: НЕТ ({desc})")

            for prop in available_props:
                print(prop)
            for prop in missing_props:
                print(prop)

            # Проверяем функции обновления
            print("\n🔧 Проверка функций обновления:")
            update_functions = [
                "updateGeometry",
                "updateMaterials",
                "updateLighting",
                "updateEffects",
                "updateEnvironment",
                "updateQuality",
            ]

            for func_name in update_functions:
                if hasattr(root, func_name):
                    print(f"   ✅ {func_name}() доступна")
                else:
                    print(f"   ❌ {func_name}() НЕ НАЙДЕНА")

            # Тестируем изменение критических свойств
            print("\n🧪 Тестирование изменения свойств:")

            # Тест 1: Размеры рамы
            if root.property("userFrameLength") is not None:
                old_frame = root.property("userFrameLength")
                root.setProperty("userFrameLength", 4000.0)  # Увеличиваем
                new_frame = root.property("userFrameLength")
                print(
                    f"   🔧 Длина рамы: {old_frame} → {new_frame} {'✅ РАБОТАЕТ' if abs(new_frame - 4000.0) < 1 else '❌ НЕ РАБОТАЕТ'}"
                )

            # Тест 2: Коэффициент преломления
            if root.property("glassIOR") is not None:
                old_ior = root.property("glassIOR")
                root.setProperty("glassIOR", 1.8)  # Увеличиваем преломление
                new_ior = root.property("glassIOR")
                print(
                    f"   🔍 IOR стекла: {old_ior} → {new_ior} {'✅ РАБОТАЕТ' if abs(new_ior - 1.8) < 0.01 else '❌ НЕ РАБОТАЕТ'}"
                )

            # Тест 3: Bloom эффект
            if root.property("bloomEnabled") is not None:
                root.setProperty("bloomEnabled", True)
                bloom_state = root.property("bloomEnabled")
                print(
                    f"   ✨ Bloom: {bloom_state} {'✅ РАБОТАЕТ' if bloom_state else '❌ НЕ РАБОТАЕТ'}"
                )

            print(f"\n📊 ЗАКЛЮЧЕНИЕ ДЛЯ {name}:")
            print(f"   Свойства: {len(available_props)}/{len(test_properties)}")
            print(
                f"   Функции: {sum(1 for f in update_functions if hasattr(root, f))}/{len(update_functions)}"
            )

            widget.deleteLater()

        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 50)
    print("🏁 ДИАГНОСТИКА ЗАВЕРШЕНА")

    app.quit()


if __name__ == "__main__":
    test_qml_loading()
