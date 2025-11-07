#!/usr/bin/env python3
"""
Анализ дублирования геометрии и проблем с эффектами в QML файлах
Проверяет муар, дублирование цилиндров, HDR проблемы, эффекты
"""

import re
from pathlib import Path


def analyze_qml_geometry_duplication():
    """Анализирует дублирование геометрии в QML файлах"""

    print("=" * 80)
    print("🔍 АНАЛИЗ ДУБЛИРОВАНИЯ ГЕОМЕТРИИ И ЭФФЕКТОВ")
    print("=" * 80)

    main_qml = Path("assets/qml/main.qml")

    if not main_qml.exists():
        print("❌ main.qml не найден!")
        return

    with open(main_qml, encoding="utf-8") as f:
        content = f.read()

    print("\n🎯 АНАЛИЗ ГЕОМЕТРИИ:")
    print("-" * 50)

    # Ищем все Model компоненты
    models = re.findall(r'Model\s*{[^}]+source:\s*"[^"]*"[^}]*}', content, re.DOTALL)
    print(f"📊 Всего Model компонентов: {len(models)}")

    # Анализ источников геометрии
    sources = {}
    for model in models:
        source_match = re.search(r'source:\s*"([^"]*)"', model)
        if source_match:
            source = source_match.group(1)
            sources[source] = sources.get(source, 0) + 1

    print("\n📋 Источники геометрии:")
    for source, count in sources.items():
        if count > 1:
            print(
                f"  ⚠️  {source}: {count} использований {'(ВОЗМОЖНОЕ ДУБЛИРОВАНИЕ!)' if count > 7 else ''}"
            )
        else:
            print(f"  ✅ {source}: {count} использование")

    # Проверяем цилиндры
    cylinder_count = sources.get("#Cylinder", 0)
    print("\n🛢️ АНАЛИЗ ЦИЛИНДРОВ:")
    print(f"   Всего цилиндров: {cylinder_count}")

    expected_cylinders = 7 * 4  # 7 цилиндров на каждый из 4 углов
    print(f"   Ожидается: {expected_cylinders} цилиндров (7 на угол × 4 угла)")

    if cylinder_count > expected_cylinders:
        print(
            f"   ❌ ДУБЛИРОВАНИЕ! Лишних цилиндров: {cylinder_count - expected_cylinders}"
        )
        print("   🚨 Это может вызывать муар эффект!")
    elif cylinder_count == expected_cylinders:
        print("   ✅ Количество цилиндров правильное")
    else:
        print(
            f"   ⚠️ Цилиндров меньше ожидаемого: {expected_cylinders - cylinder_count}"
        )

    # Анализ OptimizedSuspensionCorner
    print("\n🔧 АНАЛИЗ OptimizedSuspensionCorner:")
    corner_components = re.findall(
        r"OptimizedSuspensionCorner\s*{[^}]*}", content, re.DOTALL
    )
    print(f"   Компонентов углов: {len(corner_components)}")

    if len(corner_components) != 4:
        print(f"   ❌ Ожидается 4 угла, найдено: {len(corner_components)}")
    else:
        print("   ✅ Правильное количество углов")

    # Проверяем отдельные цилиндры вне OptimizedSuspensionCorner
    print("\n🔍 ПРОВЕРКА ОТДЕЛЬНЫХ ЦИЛИНДРОВ:")

    # Ищем цилиндры, которые НЕ внутри OptimizedSuspensionCorner
    outside_cylinders = []
    lines = content.split("\n")
    in_component = False
    component_depth = 0

    for i, line in enumerate(lines):
        if "OptimizedSuspensionCorner" in line and "{" in line:
            in_component = True
            component_depth = line.count("{") - line.count("}")
            continue

        if in_component:
            component_depth += line.count("{") - line.count("}")
            if component_depth <= 0:
                in_component = False
                continue

        if not in_component and 'source: "#Cylinder"' in line:
            outside_cylinders.append(f"   Строка {i + 1}: {line.strip()}")

    if outside_cylinders:
        print("   ⚠️ Найдены цилиндры ВНЕ OptimizedSuspensionCorner:")
        for cyl in outside_cylinders[:10]:  # Показываем первые 10
            print(cyl)
        if len(outside_cylinders) > 10:
            print(f"   ... и еще {len(outside_cylinders) - 10}")
        print("   🚨 Это может быть причиной дублирования!")
    else:
        print("   ✅ Все цилиндры внутри OptimizedSuspensionCorner")

    print("\n🎨 АНАЛИЗ ЭФФЕКТОВ:")
    print("-" * 50)

    # Анализ SceneEnvironment и ExtendedSceneEnvironment
    if "ExtendedSceneEnvironment" in content:
        print("   ✅ Использует ExtendedSceneEnvironment")
    else:
        print("   ❌ Не использует ExtendedSceneEnvironment")

    # Проверяем привязку эффектов
    effects_check = {
        "tonemapMode": r"tonemapMode:\s*[^{]*{[^}]*}",
        "antialiasingMode": r"antialiasingMode:\s*[^,\n]+",
        "bloomEnabled": r"bloomEnabled:\s*[^,\n]+",
        "ssaoEnabled": r"ssaoEnabled:\s*[^,\n]+",
        "shadowSoftness": r"shadowSoftness[^,\n]*",
        "glassIOR": r"indexOfRefraction:\s*[^,\n]+",
        "lightProbe": r"lightProbe:\s*[^,\n]+",
    }

    for effect, pattern in effects_check.items():
        if re.search(pattern, content):
            print(f"   ✅ {effect}: реализован")
        else:
            print(f"   ❌ {effect}: НЕ НАЙДЕН")

    # Проверяем IBL
    print("\n🌟 АНАЛИЗ IBL:")
    if "IblProbeLoader" in content:
        print("   ✅ IblProbeLoader присутствует")
    else:
        print("   ❌ IblProbeLoader отсутствует")

    if "lightProbe:" in content:
        print("   ✅ lightProbe привязан")
    else:
        print("   ❌ lightProbe НЕ привязан")

    # Проверяем HDR файлы
    hdr_files = ["studio.hdr", "studio_small_09_2k.hdr"]
    print("\n📁 ПРОВЕРКА HDR ФАЙЛОВ:")
    for hdr_file in hdr_files:
        hdr_path = Path(f"assets/hdr/{hdr_file}")
        if hdr_path.exists():
            size_mb = hdr_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ {hdr_file}: {size_mb:.1f} MB")
        else:
            print(f"   ❌ {hdr_file}: НЕ НАЙДЕН")

    # Анализ привязки эффектов к View3D
    print("\n🎭 АНАЛИЗ ПРИВЯЗКИ ЭФФЕКТОВ К СЦЕНЕ:")
    view3d_match = re.search(
        r"View3D\s*{[^}]*environment:\s*([^{]*){[^}]*}", content, re.DOTALL
    )
    if view3d_match:
        env_content = view3d_match.group(0)
        print("   ✅ View3D имеет environment")

        # Проверяем, что эффекты привязаны к правильному environment
        if "ExtendedSceneEnvironment" in env_content:
            print("   ✅ Эффекты применяются к правильной сцене")
        else:
            print("   ❌ Эффекты могут применяться не к той сцене!")
    else:
        print("   ❌ View3D environment не найден")

    # Рекомендации
    print("\n💡 РЕКОМЕНДАЦИИ:")
    print("-" * 50)

    if cylinder_count > expected_cylinders:
        print("1. 🚨 КРИТИЧНО: Удалить дублированные цилиндры!")
        print("   - Причина муара на цилиндрических поверхностях")
        print("   - Оставить только цилиндры внутри OptimizedSuspensionCorner")

    if "lightProbe:" not in content:
        print("2. 🌟 Исправить IBL lightProbe привязку")
        print("   - HDR фон может дергаться при орбите")

    if re.search(r"shadowSoftness[^,\n]*", content) is None:
        print("3. 🌫️ Добавить мягкость теней (shadowSoftness)")
        print("   - Тени должны быть более реалистичными")

    effects_missing = []
    for effect, pattern in effects_check.items():
        if not re.search(pattern, content):
            effects_missing.append(effect)

    if effects_missing:
        print("4. ✨ Реализовать отсутствующие эффекты:")
        for effect in effects_missing:
            print(f"   - {effect}")

    print("\n" + "=" * 80)
    return {
        "total_models": len(models),
        "cylinder_count": cylinder_count,
        "expected_cylinders": expected_cylinders,
        "corner_components": len(corner_components),
        "outside_cylinders": len(outside_cylinders),
        "effects_missing": effects_missing,
    }


def analyze_specific_geometry_issues():
    """Специфический анализ проблем геометрии"""

    print("\n🔧 ДЕТАЛЬНЫЙ АНАЛИЗ ГЕОМЕТРИИ:")
    print("=" * 80)

    main_qml = Path("assets/qml/main.qml")

    with open(main_qml, encoding="utf-8") as f:
        content = f.read()

    # Проверяем определение OptimizedSuspensionCorner
    component_match = re.search(
        r"component\s+OptimizedSuspensionCorner:\s*Node\s*{([^}]*)(?:{[^}]*}[^}]*)*}",
        content,
        re.DOTALL,
    )

    if component_match:
        component_content = component_match.group(0)
        print("✅ Найден компонент OptimizedSuspensionCorner")

        # Считаем Model внутри компонента
        models_in_component = re.findall(r"Model\s*{", component_content)
        print(f"   Моделей внутри компонента: {len(models_in_component)}")

        # Ожидается: рычаг + хвостовой шток + цилиндр + поршень + шток поршня + 3 шарнира = 8 моделей
        expected_models = 8
        if len(models_in_component) == expected_models:
            print(f"   ✅ Правильное количество моделей на угол: {expected_models}")
        else:
            print(
                f"   ⚠️ Неожиданное количество моделей: {len(models_in_component)} (ожидалось {expected_models})"
            )

        # Проверяем типы геометрии в компоненте
        cylinders_in_component = len(
            re.findall(r'source:\s*"#Cylinder"', component_content)
        )
        cubes_in_component = len(re.findall(r'source:\s*"#Cube"', component_content))

        print(f"   Цилиндров в компоненте: {cylinders_in_component}")
        print(f"   Кубов в компоненте: {cubes_in_component}")

        # Ожидается: 5 цилиндров + 1 куб (рычаг) = 6
        expected_cyl = 5  # хвостовой шток + цилиндр + поршень + шток поршня + 3 шарнира = 7 цилиндров
        expected_cube = 1  # рычаг

        if cylinders_in_component != 7:
            print(
                f"   ⚠️ Неожиданное количество цилиндров в компоненте: {cylinders_in_component} (ожидалось 7)"
            )

        if cubes_in_component != 1:
            print(
                f"   ⚠️ Неожиданное количество кубов в компоненте: {cubes_in_component} (ожидался 1)"
            )

    else:
        print("❌ Компонент OptimizedSuspensionCorner не найден!")

    # Проверяем использование компонента
    usage_matches = re.findall(
        r"OptimizedSuspensionCorner\s*{[^}]*id:\s*(\w+)[^}]*}", content, re.DOTALL
    )
    print(f"\nИспользования OptimizedSuspensionCorner: {len(usage_matches)}")
    for usage in usage_matches:
        print(f"   - {usage}")

    if len(usage_matches) != 4:
        print("   ⚠️ Должно быть ровно 4 использования (по одному на угол)")


def main():
    """Главная функция анализа"""

    print("🚀 Запуск анализа дублирования геометрии и эффектов...")

    # Основной анализ
    results = analyze_qml_geometry_duplication()

    # Детальный анализ
    analyze_specific_geometry_issues()

    # Итоговые выводы
    print("\n" + "=" * 80)
    print("📋 ИТОГОВЫЕ ВЫВОДЫ:")
    print("=" * 80)

    issues_found = []

    if results["cylinder_count"] > results["expected_cylinders"]:
        issues_found.append(
            f"🚨 ДУБЛИРОВАНИЕ ЦИЛИНДРОВ: {results['cylinder_count']} вместо {results['expected_cylinders']}"
        )

    if results["outside_cylinders"] > 0:
        issues_found.append(
            f"⚠️ Цилиндры вне компонента: {results['outside_cylinders']}"
        )

    if results["effects_missing"]:
        issues_found.append(
            f"❌ Отсутствующие эффекты: {len(results['effects_missing'])}"
        )

    if results["corner_components"] != 4:
        issues_found.append(
            f"⚠️ Неправильное количество углов: {results['corner_components']} вместо 4"
        )

    if issues_found:
        print("❌ НАЙДЕНЫ ПРОБЛЕМЫ:")
        for issue in issues_found:
            print(f"   {issue}")

        print("\n💡 ПРИОРИТЕТНЫЕ ИСПРАВЛЕНИЯ:")
        print("1. Удалить дублированные цилиндры (причина муара)")
        print("2. Исправить IBL lightProbe (HDR дергается)")
        print("3. Реализовать отсутствующие эффекты")
        print("4. Проверить применение эффектов к правильной сцене")
    else:
        print("✅ Серьезных проблем не найдено!")

    print("\n🎯 Для исправления муара - удалите дублированные цилиндры!")
    print("🎯 Для исправления HDR - проверьте lightProbe привязку!")


if __name__ == "__main__":
    main()
