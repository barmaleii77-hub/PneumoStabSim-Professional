#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 ДИАГНОСТИКА ПРОБЛЕМЫ С ОСВЕЩЕНИЕМ
Детальная проверка почему освещение не меняется
"""

import sys
from pathlib import Path


def check_lighting_flow():
    """Проверяет весь поток обновления освещения"""
    print("🔍 ГЛУБОКАЯ ДИАГНОСТИКА ОСВЕЩЕНИЯ")
    print("=" * 60)

    # 1. Проверим panel_graphics.py
    print("\n📋 1. ПРОВЕРКА PANEL_GRAPHICS.PY")
    print("-" * 40)

    graphics_file = Path("src/ui/panels/panel_graphics.py")
    if not graphics_file.exists():
        print("❌ Файл не найден!")
        return False

    content = graphics_file.read_text(encoding="utf-8")

    # Найдем функцию emit_lighting_update
    if "def emit_lighting_update(self):" in content:
        print("✅ Функция emit_lighting_update найдена")

        # Найдем что она отправляет
        lines = content.split("\n")
        in_function = False
        for i, line in enumerate(lines):
            if "def emit_lighting_update(self):" in line:
                in_function = True
                continue
            if (
                in_function
                and line.strip().startswith("def ")
                and not line.strip().startswith("def emit_lighting_update")
            ):
                break
            if in_function and "'keyLightBrightness'" in line:
                print(f"  📤 Найдена отправка: {line.strip()}")
            if in_function and "'fillLightBrightness'" in line:
                print(f"  📤 Найдена отправка: {line.strip()}")
            if in_function and "'pointLightBrightness'" in line:
                print(f"  📤 Найдена отправка: {line.strip()}")
    else:
        print("❌ Функция emit_lighting_update НЕ найдена!")
        return False

    # 2. Проверим main_window.py
    print("\n📋 2. ПРОВЕРКА MAIN_WINDOW.PY")
    print("-" * 40)

    window_file = Path("src/ui/main_window.py")
    if not window_file.exists():
        print("❌ Файл не найден!")
        return False

    window_content = window_file.read_text(encoding="utf-8")

    if "lighting_changed.connect" in window_content:
        print("✅ Сигнал lighting_changed подключен")
    else:
        print("❌ Сигнал lighting_changed НЕ подключен!")
        return False

    if "_on_lighting_changed" in window_content:
        print("✅ Обработчик _on_lighting_changed найден")
    else:
        print("❌ Обработчик _on_lighting_changed НЕ найден!")
        return False

    # 3. Найдем какой QML файл РЕАЛЬНО загружается
    print("\n📋 3. КАКОЙ QML ФАЙЛ ЗАГРУЖАЕТСЯ?")
    print("-" * 40)

    if "main_optimized.qml" in window_content:
        qml_file_used = "main_optimized.qml"
        print("✅ Используется main_optimized.qml")
    elif "main.qml" in window_content:
        qml_file_used = "main.qml"
        print("✅ Используется main.qml")
    else:
        print("❌ Не могу определить какой QML используется!")
        return False

    # 4. Проверим этот QML файл
    print(f"\n📋 4. ПРОВЕРКА {qml_file_used.upper()}")
    print("-" * 40)

    qml_path = Path(f"assets/qml/{qml_file_used}")
    if not qml_path.exists():
        print(f"❌ Файл {qml_file_used} не найден!")
        return False

    qml_content = qml_path.read_text(encoding="utf-8")

    # Проверим свойства
    props_found = 0
    if "property real keyLightBrightness" in qml_content:
        print("✅ property real keyLightBrightness")
        props_found += 1
    else:
        print("❌ property real keyLightBrightness НЕ найдено!")

    if "property real fillLightBrightness" in qml_content:
        print("✅ property real fillLightBrightness")
        props_found += 1
    else:
        print("❌ property real fillLightBrightness НЕ найдено!")

    if "property real pointLightBrightness" in qml_content:
        print("✅ property real pointLightBrightness")
        props_found += 1
    else:
        print("❌ property real pointLightBrightness НЕ найдено!")

    # Проверим функцию applyLightingUpdates
    if "function applyLightingUpdates(" in qml_content:
        print("✅ Функция applyLightingUpdates найдена")

        # Проверим что она делает с keyLightBrightness
        if "keyLightBrightness" in qml_content and "DirectionalLight" in qml_content:
            print("✅ keyLightBrightness используется в DirectionalLight")
        else:
            print("❌ keyLightBrightness не используется в DirectionalLight!")

    else:
        print("❌ Функция applyLightingUpdates НЕ найдена!")
        return False

    # 5. Проверим есть ли обработчик от Python
    print(f"\n📋 5. ПРОВЕРКА ОБРАБОТЧИКА В {qml_file_used.upper()}")
    print("-" * 40)

    if "Connections" in qml_content and "target: rootWindow" in qml_content:
        print("✅ Connections к rootWindow найден")

        if "onLighting_changed" in qml_content:
            print("✅ onLighting_changed обработчик найден")
        else:
            print("❌ onLighting_changed обработчик НЕ найден!")
            return False
    else:
        print("❌ Connections к rootWindow НЕ найден!")
        return False

    return props_found >= 3


def main():
    print("🚨 КРИТИЧЕСКАЯ ДИАГНОСТИКА ОСВЕЩЕНИЯ")
    print("=" * 60)
    print("Проверяем почему освещение не меняется...")

    if check_lighting_flow():
        print("\n" + "=" * 60)
        print("✅ ВСЕ КОМПОНЕНТЫ НА МЕСТЕ")
        print("=" * 60)
        print("Проблема может быть в:")
        print("1. 🔧 Значения не доходят от слайдеров до emit_lighting_update")
        print("2. 🔧 Сигнал не доходит от Python до QML")
        print("3. 🔧 QML получает сигнал но не применяет к свету")
        print("4. 🔧 Свет есть но визуально не заметен")
        print()
        print("🎯 РЕКОМЕНДАЦИЯ: Добавить отладочные сообщения")
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ НАЙДЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
        print("=" * 60)
        print("Необходимо исправить структурные проблемы")
        return 1


if __name__ == "__main__":
    sys.exit(main())
