#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 ИСПРАВЛЕНИЕ КРИТИЧЕСКИХ ПРОБЛЕМ
❌ ПРОБЛЕМА 1: "Рывок при первом клике мыши" - нет инициализации камеры
❌ ПРОБЛЕМА 2: "Параметры освещения не работают" - несоответствие имен

Исправления:
✅ 1. Добавляет инициализацию камеры в QML
✅ 2. Исправляет имена параметров в панели графики
✅ 3. Проверяет результат
"""

import sys
from pathlib import Path
import re


def main():
    print("🔧 ИСПРАВЛЕНИЕ КРИТИЧЕСКИХ ПРОБЛЕМ ПЕРВОГО КЛИКА И ОСВЕЩЕНИЯ")
    print("=" * 60)

    # Пути к файлам
    qml_file = Path("assets/qml/main_optimized.qml")
    graphics_panel_file = Path("src/ui/panels/panel_graphics.py")

    if not qml_file.exists():
        print(f"❌ Файл QML не найден: {qml_file}")
        return 1

    if not graphics_panel_file.exists():
        print(f"❌ Файл панели графики не найден: {graphics_panel_file}")
        return 1

    print(f"📂 QML файл: {qml_file}")
    print(f"📂 Панель графики: {graphics_panel_file}")
    print()

    # ============================================
    # ПРОБЛЕМА 1: Рывок при первом клике
    # ============================================

    print("🎯 ПРОБЛЕМА 1: Исправление рывка при первом клике")
    print("-" * 40)

    # Читаем QML файл
    qml_content = qml_file.read_text(encoding="utf-8")

    # Проверяем есть ли уже инициализация камеры
    if (
        "cameraInitialized" in qml_content
        and "Timer" in qml_content
        and "cameraInitTimer" in qml_content
    ):
        print("✅ Инициализация камеры уже присутствует в QML")
    else:
        print("❌ Инициализация камеры отсутствует - добавляем...")

        # Добавляем флаг инициализации камеры
        camera_flag_pattern = (
            r"(property bool autoRotate: false\s*property real autoRotateSpeed: 0\.5)"
        )
        camera_flag_replacement = r"\1\n\n    // ✅ ИСПРАВЛЕНИЕ: Флаг инициализации камеры для избежания рывка\n    property bool cameraInitialized: false"

        if re.search(camera_flag_pattern, qml_content):
            qml_content = re.sub(
                camera_flag_pattern, camera_flag_replacement, qml_content
            )
            print("  ✅ Добавлен флаг cameraInitialized")
        else:
            print("  ⚠️ Не найден паттерн для добавления флага")

        # Добавляем таймер инициализации камеры
        timer_pattern = r"(Timer \{\s*running: autoRotate.*?\n    \})"
        timer_replacement = r"""\1

    // ✅ ИСПРАВЛЕНИЕ: Таймер инициализации камеры (устраняет рывок при первом клике)
    Timer {
        id: cameraInitTimer
        interval: 100  // 100мс после загрузки
        running: true
        repeat: false
        onTriggered: {
            console.log("📷 Camera initialization timer triggered")
            root.cameraInitialized = true
            console.log("✅ Camera behaviors enabled - no more first-click jerk!")
        }
    }"""

        if re.search(timer_pattern, qml_content, re.DOTALL):
            qml_content = re.sub(
                timer_pattern, timer_replacement, qml_content, flags=re.DOTALL
            )
            print("  ✅ Добавлен таймер инициализации камеры")
        else:
            print("  ⚠️ Не найден паттерн для добавления таймера")

        # Обновляем Behavior для yawDeg
        behavior_pattern = r"(Behavior on yawDeg\s*\{[^}]*\})"
        behavior_replacement = r"""Behavior on yawDeg {
        enabled: root.cameraInitialized  // ✅ ИСПРАВЛЕНО: включается только после инициализации
        NumberAnimation { duration: 90; easing.type: Easing.OutCubic }
    }"""

        if re.search(behavior_pattern, qml_content, re.DOTALL):
            qml_content = re.sub(
                behavior_pattern, behavior_replacement, qml_content, flags=re.DOTALL
            )
            print("  ✅ Обновлен Behavior для yawDeg")
        else:
            print("  ⚠️ Не найден Behavior для yawDeg")

        # Обновляем Behavior для pitchDeg
        pitch_behavior_pattern = r"(Behavior on pitchDeg\s*\{[^}]*\})"
        pitch_behavior_replacement = r"""Behavior on pitchDeg {
        enabled: root.cameraInitialized  // ✅ ИСПРАВЛЕНО: включается только после инициализации
        NumberAnimation { duration: 90; easing.type: Easing.OutCubic }
    }"""

        if re.search(pitch_behavior_pattern, qml_content, re.DOTALL):
            qml_content = re.sub(
                pitch_behavior_pattern,
                pitch_behavior_replacement,
                qml_content,
                flags=re.DOTALL,
            )
            print("  ✅ Обновлен Behavior для pitchDeg")
        else:
            print("  ⚠️ Не найден Behavior для pitchDeg")

    # ============================================
    # ПРОБЛЕМА 2: Параметры освещения не работают
    # ============================================

    print("\n🎯 ПРОБЛЕМА 2: Исправление параметров освещения")
    print("-" * 40)

    # Читаем файл панели графики
    graphics_content = graphics_panel_file.read_text(encoding="utf-8")

    # Проверяем текущие имена параметров
    current_names = []
    if "'key_brightness'" in graphics_content:
        current_names.append("key_brightness")
    if "'fill_brightness'" in graphics_content:
        current_names.append("fill_brightness")
    if "'point_brightness'" in graphics_content:
        current_names.append("point_brightness")

    print(f"🔍 Найдены текущие имена: {current_names}")

    # QML ожидает эти имена:
    expected_qml_names = [
        "keyLightBrightness",
        "fillLightBrightness",
        "pointLightBrightness",
        "keyLightColor",
        "fillLightColor",
        "pointLightColor",
    ]

    print(f"🎯 QML ожидает: {expected_qml_names[:3]} (яркость)")

    # Исправляем соответствие имен параметров
    name_mappings = {
        # Параметры освещения
        "'key_brightness'": "'keyLightBrightness'",
        "'key_color'": "'keyLightColor'",
        "'key_angle_x'": "'keyLightAngleX'",
        "'key_angle_y'": "'keyLightAngleY'",
        "'fill_brightness'": "'fillLightBrightness'",
        "'fill_color'": "'fillLightColor'",
        "'point_brightness'": "'pointLightBrightness'",
        "'point_color'": "'pointLightColor'",
        "'point_y'": "'pointLightY'",
        "'point_fade'": "'pointFade'",
        # Дополнительные параметры если найдены
        "'rim_brightness'": "'rimBrightness'",
        "'rim_color'": "'rimColor'",
    }

    changes_made = 0
    for old_name, new_name in name_mappings.items():
        if old_name in graphics_content:
            graphics_content = graphics_content.replace(old_name, new_name)
            changes_made += 1
            print(f"  ✅ {old_name} → {new_name}")

    if changes_made == 0:
        print("  ✅ Все имена параметров уже корректные")
    else:
        print(f"  🔧 Исправлено {changes_made} имен параметров")

    # ============================================
    # ДОПОЛНИТЕЛЬНО: Улучшаем обработчики сигналов
    # ============================================

    print("\n🎯 ДОПОЛНИТЕЛЬНО: Проверка обработчиков сигналов")
    print("-" * 40)

    # Проверяем что emit_lighting_update() вызывается правильно
    if "self.emit_lighting_update()" in graphics_content:
        print("  ✅ emit_lighting_update() найден")
    else:
        print("  ⚠️ emit_lighting_update() не найден")

    # Проверяем инициализацию графики
    if "Отправляем начальные настройки СРАЗУ без задержки" in graphics_content:
        print("  ✅ Инициализация графики без задержки найдена")
    else:
        print("  ⚠️ Инициализация графики требует улучшения")

    # ============================================
    # СОХРАНЕНИЕ ИЗМЕНЕНИЙ
    # ============================================

    print("\n💾 СОХРАНЕНИЕ ИЗМЕНЕНИЙ")
    print("-" * 40)

    try:
        # Сохраняем QML файл
        qml_file.write_text(qml_content, encoding="utf-8")
        print(f"✅ QML файл сохранен: {qml_file}")

        # Сохраняем файл панели графики
        graphics_panel_file.write_text(graphics_content, encoding="utf-8")
        print(f"✅ Панель графики сохранена: {graphics_panel_file}")

    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return 1

    # ============================================
    # ПРОВЕРКА РЕЗУЛЬТАТОВ
    # ============================================

    print("\n🔍 ПРОВЕРКА РЕЗУЛЬТАТОВ")
    print("-" * 40)

    # Перечитываем файлы для проверки
    qml_check = qml_file.read_text(encoding="utf-8")
    graphics_check = graphics_panel_file.read_text(encoding="utf-8")

    # Проверка 1: Инициализация камеры
    camera_check = (
        "cameraInitialized: false" in qml_check
        and "cameraInitTimer" in qml_check
        and "enabled: root.cameraInitialized" in qml_check
    )

    if camera_check:
        print("✅ ПРОБЛЕМА 1 ИСПРАВЛЕНА: Инициализация камеры добавлена")
    else:
        print("❌ ПРОБЛЕМА 1 НЕ ИСПРАВЛЕНА: Инициализация камеры неполная")

    # Проверка 2: Имена параметров освещения
    lighting_check = (
        "'keyLightBrightness'" in graphics_check
        and "'fillLightBrightness'" in graphics_check
        and "'pointLightBrightness'" in graphics_check
    )

    if lighting_check:
        print("✅ ПРОБЛЕМА 2 ИСПРАВЛЕНА: Имена параметров освещения корректные")
    else:
        print("❌ ПРОБЛЕМА 2 НЕ ИСПРАВЛЕНА: Имена параметров требуют доработки")

    # ============================================
    # ИТОГОВЫЙ ОТЧЕТ
    # ============================================

    print("\n" + "=" * 60)
    print("🎯 ИТОГОВЫЙ ОТЧЕТ ИСПРАВЛЕНИЙ")
    print("=" * 60)

    if camera_check and lighting_check:
        print("🎉 ВСЕ ПРОБЛЕМЫ ИСПРАВЛЕНЫ УСПЕШНО!")
        print()
        print("✅ ПРОБЛЕМА 1: Рывок при первом клике устранен")
        print("   🔧 Добавлена инициализация камеры с таймером")
        print("   🔧 Behavior включается только после инициализации")
        print()
        print("✅ ПРОБЛЕМА 2: Параметры освещения теперь работают")
        print("   🔧 Исправлены имена параметров Python ↔ QML")
        print("   🔧 keyLightBrightness, fillLightBrightness, pointLightBrightness")
        print()
        print("🚀 ТЕСТИРОВАНИЕ:")
        print("   1. Запустите: python app.py")
        print("   2. Попробуйте первый клик мыши (должен быть плавным)")
        print("   3. Измените параметры освещения в панели 'Графика'")
        print("   4. Проверьте что изменения применяются мгновенно")
        print()
        return 0
    else:
        print("⚠️ НЕКОТОРЫЕ ПРОБЛЕМЫ ОСТАЛИСЬ")
        if not camera_check:
            print("❌ Инициализация камеры неполная")
        if not lighting_check:
            print("❌ Имена параметров освещения неправильные")
        print()
        print("🔧 Требуется ручная доработка файлов")
        return 1


if __name__ == "__main__":
    sys.exit(main())
