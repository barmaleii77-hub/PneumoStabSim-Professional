#!/usr/bin/env python3
"""
ИСПРАВЛЕНИЕ ДУБЛИРОВАНИЯ ГЕОМЕТРИИ И МУАРА В QML
================================================================
Проблемы:
1. Муар на цилиндрических поверхностях (дублирование геометрии)
2. Эффекты применяются к одной сцене, а выводится другая
3. HDR фон дергается при орбите
4. Сглаживание и эффекты не работают должным образом
"""

import os
import re


def check_cylinder_duplication():
    """Проверить дублирование цилиндров в main.qml"""

    main_qml_path = "assets/qml/main.qml"

    if not os.path.exists(main_qml_path):
        print("❌ main.qml не найден!")
        return False

    with open(main_qml_path, "r", encoding="utf-8") as f:
        content = f.read()

    print("🔍 АНАЛИЗ ДУБЛИРОВАНИЯ ЦИЛИНДРОВ:")
    print("=" * 50)

    # Ищем все цилиндры
    cylinder_pattern = r'Model\s*{[^}]*source:\s*(#Cylinder|"#Cylinder")[^}]*}'
    cylinder_matches = re.findall(cylinder_pattern, content, re.DOTALL)

    print(f"📊 Найдено цилиндров: {len(cylinder_matches)}")

    # Анализируем позиции цилиндров
    position_pattern = r"position:\s*Qt\.vector3d\(([^)]+)\)"
    positions = re.findall(position_pattern, content)

    print(f"📊 Найдено позиций: {len(positions)}")

    # Проверяем дублирование позиций
    position_dict = {}
    for pos in positions:
        if pos in position_dict:
            position_dict[pos] += 1
            print(
                f"⚠️ ДУБЛИРОВАНИЕ ПОЗИЦИИ: {pos} (встречается {position_dict[pos]} раз)"
            )
        else:
            position_dict[pos] = 1

    print("\n🔍 АНАЛИЗ КОМПОНЕНТОВ OptimizedSuspensionCorner:")
    print("=" * 50)

    # Ищем компоненты OptimizedSuspensionCorner
    corner_pattern = r"OptimizedSuspensionCorner\s*{[^}]*}"
    corner_matches = re.findall(corner_pattern, content, re.DOTALL)

    print(f"📊 Найдено OptimizedSuspensionCorner: {len(corner_matches)}")

    # Проверяем отдельные цилиндры вне компонентов
    lines = content.split("\n")
    in_suspension_corner = False
    standalone_cylinders = 0

    for i, line in enumerate(lines):
        if "OptimizedSuspensionCorner" in line and "{" in line:
            in_suspension_corner = True
        elif in_suspension_corner and line.strip() == "}":
            in_suspension_corner = False
        elif not in_suspension_corner and "#Cylinder" in line:
            standalone_cylinders += 1
            print(f"⚠️ ОТДЕЛЬНЫЙ ЦИЛИНДР вне компонента (строка {i+1}): {line.strip()}")

    print(f"📊 Отдельных цилиндров вне компонентов: {standalone_cylinders}")

    return True


def check_scene_environment_usage():
    """Проверить использование ExtendedSceneEnvironment"""

    main_qml_path = "assets/qml/main.qml"

    with open(main_qml_path, "r", encoding="utf-8") as f:
        content = f.read()

    print("\n🔍 АНАЛИЗ SCENE ENVIRONMENT:")
    print("=" * 50)

    # Ищем использование ExtendedSceneEnvironment
    if "ExtendedSceneEnvironment" in content:
        print("✅ ExtendedSceneEnvironment используется")

        # Проверяем привязку к View3D
        view3d_pattern = r"View3D\s*{[^}]*environment:\s*ExtendedSceneEnvironment"
        if re.search(view3d_pattern, content, re.DOTALL):
            print("✅ ExtendedSceneEnvironment правильно привязан к View3D")
        else:
            print("❌ ExtendedSceneEnvironment НЕ привязан к View3D!")
            return False
    else:
        print("❌ ExtendedSceneEnvironment НЕ используется!")
        return False

    # Проверяем настройки эффектов
    effect_props = [
        "bloomEnabled",
        "ssaoEnabled",
        "tonemapMode",
        "antialiasingMode",
        "shadowsEnabled",
    ]

    for prop in effect_props:
        if prop in content:
            print(f"✅ {prop} найден в QML")
        else:
            print(f"❌ {prop} НЕ найден в QML!")

    return True


def analyze_antialiasing_values():
    """Анализировать значения антиалиасинга"""

    main_qml_path = "assets/qml/main.qml"

    with open(main_qml_path, "r", encoding="utf-8") as f:
        content = f.read()

    print("\n🔍 АНАЛИЗ АНТИАЛИАСИНГА:")
    print("=" * 50)

    # Ищем настройки антиалиасинга
    aa_mode_match = re.search(r"property\s+int\s+antialiasingMode:\s*(\d+)", content)
    aa_quality_match = re.search(
        r"property\s+int\s+antialiasingQuality:\s*(\d+)", content
    )

    if aa_mode_match:
        aa_mode = int(aa_mode_match.group(1))
        print(f"📊 antialiasingMode: {aa_mode}")

        modes = {
            0: "NoAA (отключен)",
            1: "SSAA (суперсемплинг)",
            2: "MSAA (мультисемплинг)",
            3: "ProgressiveAA (прогрессивный)",
        }
        print(f"   Режим: {modes.get(aa_mode, 'Неизвестный')}")

    if aa_quality_match:
        aa_quality = int(aa_quality_match.group(1))
        print(f"📊 antialiasingQuality: {aa_quality}")

        qualities = {0: "Low (низкое)", 1: "Medium (среднее)", 2: "High (высокое)"}
        print(f"   Качество: {qualities.get(aa_quality, 'Неизвестное')}")

    # Проверяем привязку в ExtendedSceneEnvironment
    aa_binding_pattern = r"antialiasingMode:\s*([^,\n}]+)"
    aa_binding_match = re.search(aa_binding_pattern, content)

    if aa_binding_match:
        binding = aa_binding_match.group(1).strip()
        print(f"📊 Привязка antialiasingMode: {binding}")

        if "SceneEnvironment" in binding:
            print("✅ Правильная привязка к SceneEnvironment")
        else:
            print("❌ Неправильная привязка антиалиасинга!")


def check_hdr_background():
    """Проверить настройки HDR фона"""

    main_qml_path = "assets/qml/main.qml"

    with open(main_qml_path, "r", encoding="utf-8") as f:
        content = f.read()

    print("\n🔍 АНАЛИЗ HDR ФОНА:")
    print("=" * 50)

    # Ищем настройки фона
    bg_mode_pattern = r"backgroundMode:\s*([^,\n}]+)"
    bg_mode_match = re.search(bg_mode_pattern, content)

    if bg_mode_match:
        bg_mode = bg_mode_match.group(1).strip()
        print(f"📊 backgroundMode: {bg_mode}")

        if "SkyBox" in bg_mode and "iblReady" in bg_mode:
            print("✅ Условный SkyBox с проверкой IBL")
        elif "SkyBox" in bg_mode:
            print("⚠️ SkyBox без проверки IBL - может вызывать дерганье!")

    # Проверяем lightProbe
    light_probe_pattern = r"lightProbe:\s*([^,\n}]+)"
    light_probe_match = re.search(light_probe_pattern, content)

    if light_probe_match:
        light_probe = light_probe_match.group(1).strip()
        print(f"📊 lightProbe: {light_probe}")

        if "iblLoader.probe" in light_probe and "iblReady" in light_probe:
            print("✅ Условный lightProbe с проверкой IBL")
        elif "iblLoader.probe" in light_probe:
            print("⚠️ lightProbe без проверки готовности - может вызывать дерганье!")


def suggest_fixes():
    """Предложить исправления"""

    print("\n🔧 ПРЕДЛАГАЕМЫЕ ИСПРАВЛЕНИЯ:")
    print("=" * 50)

    print("1. ДУБЛИРОВАНИЕ ГЕОМЕТРИИ:")
    print(
        "   ❌ Убрать отдельные цилиндры, если они дублируют OptimizedSuspensionCorner"
    )
    print("   ✅ Использовать ТОЛЬКО OptimizedSuspensionCorner для всех цилиндров")
    print("   ✅ Проверить, что позиции не дублируются")

    print("\n2. МУАР НА ЦИЛИНДРАХ:")
    print("   ❌ Z-fighting из-за перекрывающихся цилиндров")
    print("   ✅ Убрать дублирующиеся Model с source: '#Cylinder'")
    print("   ✅ Использовать разные Z-позиции для слоев")

    print("\n3. HDR ФОН ДЕРГАЕТСЯ:")
    print("   ❌ backgroundMode переключается без проверки готовности IBL")
    print("   ✅ Добавить проверку iblReady в backgroundMode")
    print("   ✅ lightProbe должен быть null пока IBL не готов")

    print("\n4. ЭФФЕКТЫ НЕ РАБОТАЮТ:")
    print("   ❌ Возможно ExtendedSceneEnvironment не получает параметры")
    print("   ✅ Проверить привязки всех эффектов")
    print("   ✅ Убедиться что antialiasingMode правильно маппится")

    print("\n5. УВЕЛИЧЕНИЕ ЗНАЧЕНИЙ ЭФФЕКТОВ:")
    print("   ✅ ssaoStrength: увеличить до 100+ (сейчас ~50)")
    print("   ✅ bloomIntensity: увеличить до 1.5+ (сейчас ~0.8)")
    print("   ✅ shadowSoftness: увеличить до 1.0+ (сейчас ~0.5)")


def main():
    """Основная функция"""

    print("🔍 ДИАГНОСТИКА ДУБЛИРОВАНИЯ И МУАРА В QML")
    print("=" * 60)

    # Проверяем дублирование цилиндров
    check_cylinder_duplication()

    # Проверяем использование ExtendedSceneEnvironment
    check_scene_environment_usage()

    # Анализируем антиалиасинг
    analyze_antialiasing_values()

    # Проверяем HDR фон
    check_hdr_background()

    # Предлагаем исправления
    suggest_fixes()

    print("\n✅ ДИАГНОСТИКА ЗАВЕРШЕНА!")
    print("🔧 Используйте предложенные исправления для устранения проблем")


if __name__ == "__main__":
    main()
