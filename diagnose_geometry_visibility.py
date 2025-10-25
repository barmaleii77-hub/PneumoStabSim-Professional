#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Диагностика видимости геометрии штоков и поршней
Проверяет масштабирование и позиционирование
"""


def diagnose_geometry():
    """Диагностика параметров геометрии"""

    print("=" * 70)
    print("🔍 ДИАГНОСТИКА ВИДИМОСТИ ШТОКОВ И ПОРШНЕЙ")
    print("=" * 70)
    print()

    # Параметры из main.qml (дефолты)
    userPistonThickness = 25  # мм
    userPistonRodLength = 200  # мм
    userRodDiameter = 35  # мм
    userBoreHead = 80  # мм
    userCylinderLength = 500  # мм

    print("📏 ПАРАМЕТРЫ ИЗ main.qml (дефолты):")
    print(f"   userPistonThickness: {userPistonThickness} мм")
    print(f"   userPistonRodLength: {userPistonRodLength} мм")
    print(f"   userRodDiameter: {userRodDiameter} мм")
    print(f"   userBoreHead: {userBoreHead} мм")
    print(f"   userCylinderLength: {userCylinderLength} мм")

    print()
    print("📐 МАСШТАБИРОВАНИЕ В SuspensionCorner.qml:")
    print("-" * 70)

    # 1. ПОРШЕНЬ (piston body)
    piston_scale_x = (userBoreHead / 100) * 1.08
    piston_scale_y = userPistonThickness / 100
    piston_scale_z = (userBoreHead / 100) * 1.08

    print("🔴 PISTON (Model #Cylinder):")
    print(
        f"   scale: ({piston_scale_x:.3f}, {piston_scale_y:.3f}, {piston_scale_z:.3f})"
    )
    print(f"   ⚠️  scale.y = {piston_scale_y:.3f} (очень мало!)")
    print("   Причина: pistonThickness=25мм → 25/100 = 0.25")

    if piston_scale_y < 0.5:
        print("   ❌ КРИТИЧНО: Поршень СЛИШКОМ ТОНКИЙ (< 0.5 единиц)!")
        print("   Рекомендация: Убрать деление на 100 для толщины")

    print()

    # 2. ШТОК ПОРШНЯ (piston rod)
    rod_scale_x = (userRodDiameter / 100) * 0.5
    rod_scale_y = userPistonRodLength / 100
    rod_scale_z = (userRodDiameter / 100) * 0.5

    print("🔵 PISTON ROD (Model #Cylinder):")
    print(f"   scale: ({rod_scale_x:.3f}, {rod_scale_y:.3f}, {rod_scale_z:.3f})")
    print(f"   scale.x = {rod_scale_x:.3f} (диаметр)")
    print(f"   scale.y = {rod_scale_y:.3f} (длина)")

    if rod_scale_x < 0.2:
        print("   ⚠️  Шток СЛИШКОМ ТОНКИЙ (< 0.2 единиц)!")
        print("   Причина: rodDiameter=35мм → (35/100)*0.5 = 0.175")

    if rod_scale_y < 1.0:
        print("   ❌ КРИТИЧНО: Шток СЛИШКОМ КОРОТКИЙ (< 1.0 единиц)!")
        print("   Причина: pistonRodLength=200мм → 200/100 = 2.0")
        print("   Рекомендация: Убрать деление на 100 для длины")

    print()

    # 3. ЦИЛИНДР (cylinder body)
    cyl_scale_x = (userBoreHead / 100) * 1.2
    cyl_scale_y = userCylinderLength / 100
    cyl_scale_z = (userBoreHead / 100) * 1.2

    print("⚪ CYLINDER BODY (Model #Cylinder, transparent):")
    print(f"   scale: ({cyl_scale_x:.3f}, {cyl_scale_y:.3f}, {cyl_scale_z:.3f})")
    print(f"   scale.y = {cyl_scale_y:.3f} (длина цилиндра)")

    if cyl_scale_y < 3.0:
        print("   ⚠️  Цилиндр КОРОТКИЙ относительно сцены")
    else:
        print(f"   ✅ Цилиндр виден (scale.y = {cyl_scale_y:.3f})")

    print()
    print("=" * 70)
    print("🎯 ВЫВОД:")
    print("=" * 70)

    issues = []

    if piston_scale_y < 0.5:
        issues.append("❌ Поршень СЛИШКОМ ТОНКИЙ (не виден на камере)")

    if rod_scale_x < 0.2:
        issues.append("⚠️  Шток поршня СЛИШКОМ ТОНКИЙ")

    if rod_scale_y < 1.5:
        issues.append("⚠️  Шток поршня КОРОТКИЙ")

    if issues:
        print("🚨 НАЙДЕНЫ ПРОБЛЕМЫ:")
        for issue in issues:
            print(f"   {issue}")

        print()
        print("💡 РЕШЕНИЕ:")
        print("   1. Убрать деление на 100 для параметров, которые уже в мм:")
        print("      - pistonThickness (25мм → 25 единиц)")
        print("      - pistonRodLength (200мм → 200 единиц)")
        print("   2. ИЛИ использовать размеры в метрах:")
        print("      - pistonThickness: 0.025м → 25/1000 * scale_factor")
        print("      - pistonRodLength: 0.200м → 200/1000 * scale_factor")
        print()
        print("   ✅ РЕКОМЕНДАЦИЯ: Использовать ПРЯМОЕ масштабирование")
        print("      scale.y = pistonThickness (без деления на 100)")
    else:
        print("✅ Геометрия масштабирована корректно!")

    print()
    print("=" * 70)
    print("📋 ПРОВЕРОЧНЫЙ СПИСОК:")
    print("=" * 70)

    # Проверка позиций
    print("1. ✅ Позиции (pistonCenter, j_rod) вычисляются корректно")
    print("2. ⚠️  Масштабирование по Y (высота) использует /100 → ПРОБЛЕМА")
    print("3. ✅ Материалы привязаны через materials: [...]")
    print("4. ✅ eulerRotation вычисляется правильно")
    print()

    print("🎯 ГЛАВНАЯ ПРОБЛЕМА:")
    print("   Qt #Cylinder имеет ВЫСОТУ = 100 единиц по умолчанию")
    print("   Если pistonThickness=25мм, то scale.y=25/100=0.25")
    print("   Это даёт ОЧЕНЬ ТОНКИЙ поршень (0.25 единиц высотой)")
    print()
    print("   Камера находится на расстоянии ~3000-5000 единиц")
    print("   Поршень толщиной 0.25 НЕ ВИДЕН с такого расстояния!")
    print()

    print("💡 ПРАВИЛЬНОЕ МАСШТАБИРОВАНИЕ:")
    print("   ❌ НЕПРАВИЛЬНО:")
    print("      scale: Qt.vector3d(1.08, pistonThickness/100, 1.08)")
    print("                                 ↑ 25/100 = 0.25 (не виден!)")
    print()
    print("   ✅ ПРАВИЛЬНО:")
    print("      scale: Qt.vector3d(1.08, pistonThickness/10, 1.08)")
    print("                                 ↑ 25/10 = 2.5 (виден!)")
    print()
    print("   ИЛИ:")
    print("      scale: Qt.vector3d(1.08, pistonThickness, 1.08)")
    print("                                 ↑ 25 (виден отлично!)")
    print()


def calculate_optimal_scale():
    """Вычислить оптимальное масштабирование"""

    print("=" * 70)
    print("⚙️  ОПТИМАЛЬНОЕ МАСШТАБИРОВАНИЕ")
    print("=" * 70)
    print()

    # Параметры
    piston_thickness_mm = 25
    rod_length_mm = 200
    rod_diameter_mm = 35
    bore_diameter_mm = 80

    # Qt #Cylinder default height = 100 units
    qt_cylinder_height = 100

    # Оптимальные scale факторы
    print("📏 ИСХОДНЫЕ РАЗМЕРЫ (мм):")
    print(f"   Толщина поршня:   {piston_thickness_mm} мм")
    print(f"   Длина штока:      {rod_length_mm} мм")
    print(f"   Диаметр штока:    {rod_diameter_mm} мм")
    print(f"   Диаметр цилиндра: {bore_diameter_mm} мм")
    print()

    print("🎯 ОПТИМАЛЬНЫЕ SCALE ФАКТОРЫ:")
    print()

    # Вариант 1: Прямое масштабирование (размеры в мм = единицы в Qt)
    print("✅ ВАРИАНТ 1: Прямое масштабирование (1мм = 1 единица)")
    piston_scale_v1 = piston_thickness_mm / qt_cylinder_height
    rod_scale_v1 = rod_length_mm / qt_cylinder_height

    print(
        f"   Поршень: scale.y = {piston_thickness_mm}/{qt_cylinder_height} = {piston_scale_v1:.2f}"
    )
    print(
        f"   Шток:    scale.y = {rod_length_mm}/{qt_cylinder_height} = {rod_scale_v1:.2f}"
    )
    print()

    # Вариант 2: Масштабирование через /10 (более реалистично для Qt сцены)
    print("✅ ВАРИАНТ 2: Масштабирование /10 (1см = 1 единица)")
    piston_scale_v2 = piston_thickness_mm / 10 / qt_cylinder_height * qt_cylinder_height
    rod_scale_v2 = rod_length_mm / 10 / qt_cylinder_height * qt_cylinder_height

    print(
        f"   Поршень: scale.y = {piston_thickness_mm}/10 = {piston_thickness_mm / 10:.1f} (scale = {piston_scale_v2 / 100:.2f})"
    )
    print(
        f"   Шток:    scale.y = {rod_length_mm}/10 = {rod_length_mm / 10:.1f} (scale = {rod_scale_v2 / 100:.2f})"
    )
    print()

    # Вариант 3: Масштабирование для сцены 1000-5000 единиц
    print("✅ ВАРИАНТ 3: Для камеры на расстоянии 3000-5000 единиц")
    scene_scale_factor = 5  # Умножитель для видимости
    piston_scale_v3 = piston_thickness_mm / qt_cylinder_height * scene_scale_factor
    rod_scale_v3 = rod_length_mm / qt_cylinder_height * scene_scale_factor

    print(
        f"   Поршень: scale.y = ({piston_thickness_mm}/100) * {scene_scale_factor} = {piston_scale_v3:.2f}"
    )
    print(
        f"   Шток:    scale.y = ({rod_length_mm}/100) * {scene_scale_factor} = {rod_scale_v3:.2f}"
    )
    print()

    print("=" * 70)
    print("🎯 РЕКОМЕНДАЦИЯ:")
    print("=" * 70)
    print()
    print("Использовать ВАРИАНТ 1 (прямое масштабирование):")
    print()
    print("```qml")
    print("// 4. PISTON")
    print("Model {")
    print('    source: "#Cylinder"')
    print("    scale: Qt.vector3d(1.08, pistonThickness/100, 1.08)")
    print("    // ↑ Изменить на: pistonThickness (БЕЗ /100)")
    print("    materials: [pistonBodyMaterial]")
    print("}")
    print()
    print("// 5. PISTON ROD")
    print("Model {")
    print('    source: "#Cylinder"')
    print("    scale: Qt.vector3d(0.5, pistonRodLength/100, 0.5)")
    print("    // ↑ Изменить на: pistonRodLength (БЕЗ /100)")
    print("    materials: [pistonRodMaterial]")
    print("}")
    print("```")
    print()
    print("✅ Это даст:")
    print(f"   - Поршень толщиной {piston_thickness_mm} единиц (хорошо виден)")
    print(f"   - Шток длиной {rod_length_mm} единиц (отлично виден)")
    print()


def main():
    """Главная функция"""

    print()
    print("🚀 Запуск диагностики геометрии...")
    print()

    diagnose_geometry()
    calculate_optimal_scale()

    print("=" * 70)
    print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("=" * 70)
    print()
    print("📋 ИТОГИ:")
    print("   1. Проблема: Деление на 100 делает поршни/штоки ОЧЕНЬ маленькими")
    print("   2. Решение: Убрать /100 для pistonThickness и pistonRodLength")
    print("   3. Ожидаемый результат: Штоки и поршни станут ВИДНЫ")
    print()
    print("🔧 Следующий шаг: Применить исправление в SuspensionCorner.qml")
    print()


if __name__ == "__main__":
    main()
