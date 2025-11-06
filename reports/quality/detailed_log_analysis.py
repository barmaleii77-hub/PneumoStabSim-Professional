#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Детальный анализ логов с категоризацией ошибок."""

import re
from pathlib import Path
from collections import Counter, defaultdict


def analyze_errors():
    """Анализирует ошибки из run.log с детальной категоризацией."""

    log_path = Path("logs/run.log")
    if not log_path.exists():
        print("❌ Файл logs/run.log не найден")
        return

    log_content = log_path.read_text(encoding="utf-8")
    lines = log_content.split("\n")

    # Фильтруем строки с ошибками
    error_lines = [
        line for line in lines if "ERROR" in line.upper() or "CRITICAL" in line.upper()
    ]

    # Категории ошибок
    categories = {
        "shader_compilation": [],
        "qml_property": [],
        "fog_effect": [],
        "depth_texture": [],
        "spirv_compiler": [],
        "qt_customMain": [],
        "other": [],
    }

    for line in error_lines:
        line_lower = line.lower()

        if "qt_custommain" in line_lower:
            categories["qt_customMain"].append(line)
        elif "spirv" in line_lower or "qspirvcompiler" in line_lower:
            categories["spirv_compiler"].append(line)
        elif "shader" in line_lower and "compil" in line_lower:
            categories["shader_compilation"].append(line)
        elif "fog" in line_lower and (
            "effect" in line_lower or "manifest" in line_lower
        ):
            categories["fog_effect"].append(line)
        elif "depth" in line_lower or "velocity" in line_lower:
            categories["depth_texture"].append(line)
        elif "cannot assign" in line_lower or "non-existent property" in line_lower:
            categories["qml_property"].append(line)
        else:
            categories["other"].append(line)

    # Вывод результатов
    print("\n" + "=" * 80)
    print("📊 ДЕТАЛЬНЫЙ АНАЛИЗ ОШИБОК LOGS/RUN.LOG")
    print("=" * 80 + "\n")

    print(f"Всего строк с ошибками: {len(error_lines)}\n")

    print("РАСПРЕДЕЛЕНИЕ ПО КАТЕГОРИЯМ:")
    print("-" * 80)

    for category, items in sorted(
        categories.items(), key=lambda x: len(x[1]), reverse=True
    ):
        count = len(items)
        if count > 0:
            percentage = (count / len(error_lines)) * 100
            icon = {
                "qt_customMain": "🔧",
                "spirv_compiler": "⚙️",
                "shader_compilation": "🎨",
                "fog_effect": "🌫️",
                "depth_texture": "📷",
                "qml_property": "📝",
                "other": "❓",
            }.get(category, "•")

            print(f"{icon} {category:25} {count:4} ({percentage:5.1f}%)")

    # Детальный анализ критичных категорий
    print("\n" + "=" * 80)
    print("🔍 ДЕТАЛЬНЫЙ АНАЛИЗ КРИТИЧНЫХ КАТЕГОРИЙ")
    print("=" * 80 + "\n")

    # 1. qt_customMain ошибки (самые частые)
    if categories["qt_customMain"]:
        print(f"1️⃣ qt_customMain ОШИБКИ ({len(categories['qt_customMain'])})")
        print("-" * 80)

        # Извлекаем номера строк где произошла ошибка
        line_numbers = []
        for err in categories["qt_customMain"]:
            match = re.search(r"ERROR: :(\d+):", err)
            if match:
                line_numbers.append(int(match.group(1)))

        if line_numbers:
            line_counter = Counter(line_numbers)
            print(f"   Всего вхождений: {len(categories['qt_customMain'])}")
            print(f"   Уникальных строк: {len(line_counter)}")
            print(f"\n   Топ строк с ошибками:")
            for line_num, count in line_counter.most_common(5):
                print(f"      Строка {line_num}: {count}× ошибок")

        print(f"\n   Пример:")
        print(f"      {categories['qt_customMain'][0][:150]}")
        print()

    # 2. Fog Effect ошибки
    if categories["fog_effect"]:
        print(f"2️⃣ FOG EFFECT ОШИБКИ ({len(categories['fog_effect'])})")
        print("-" * 80)

        # Анализируем какие файлы проблемные
        fog_files = defaultdict(int)
        for err in categories["fog_effect"]:
            if "fog.frag" in err:
                fog_files["fog.frag"] += 1
            elif "fog.vert" in err:
                fog_files["fog.vert"] += 1
            elif "fog_fallback.frag" in err:
                fog_files["fog_fallback.frag"] += 1
            elif "fog_es" in err:
                fog_files["fog_es.*"] += 1

        print("   Проблемные файлы:")
        for file, count in sorted(fog_files.items(), key=lambda x: x[1], reverse=True):
            print(f"      {file:25} {count:3}× ошибок")

        # Типы проблем
        manifest_errors = len(
            [e for e in categories["fog_effect"] if "manifest mismatch" in e]
        )
        normalization_errors = len(
            [e for e in categories["fog_effect"] if "normalization skipped" in e]
        )

        print(f"\n   Типы проблем:")
        print(f"      Manifest mismatch:        {manifest_errors}")
        print(f"      Normalization skipped:    {normalization_errors}")
        print()

    # 3. Depth Texture ошибки
    if categories["depth_texture"]:
        print(f"3️⃣ DEPTH/VELOCITY TEXTURE ОШИБКИ ({len(categories['depth_texture'])})")
        print("-" * 80)

        properties = set()
        for err in categories["depth_texture"]:
            if "explicitDepthTextureEnabled" in err:
                properties.add("explicitDepthTextureEnabled")
            if "explicitVelocityTextureEnabled" in err:
                properties.add("explicitVelocityTextureEnabled")
            if "requiresDepthTexture" in err:
                properties.add("requiresDepthTexture")
            if "requiresVelocityTexture" in err:
                properties.add("requiresVelocityTexture")

        print("   Недостающие свойства:")
        for prop in sorted(properties):
            count = sum(1 for e in categories["depth_texture"] if prop in e)
            print(f"      {prop:35} {count:2}× попыток установки")
        print()

    # 4. QML Property ошибки
    if categories["qml_property"]:
        print(f"4️⃣ QML PROPERTY ОШИБКИ ({len(categories['qml_property'])})")
        print("-" * 80)

        properties = []
        for err in categories["qml_property"]:
            match = re.search(r'property "(\w+)"', err)
            if match:
                properties.append(match.group(1))

        if properties:
            prop_counter = Counter(properties)
            print("   Несуществующие свойства:")
            for prop, count in prop_counter.most_common(10):
                print(f"      {prop:30} {count:2}× попыток присвоения")
        print()

    # Рекомендации
    print("=" * 80)
    print("💡 РЕКОМЕНДАЦИИ ПО УСТРАНЕНИЮ")
    print("=" * 80 + "\n")

    recommendations = []

    if categories["qt_customMain"]:
        recommendations.append(
            "1. qt_customMain ошибки:\n"
            "   - Проблема: Шейдеры используют устаревший API qt_customMain\n"
            "   - Решение: Обновить шейдеры под Qt 6.10 API (void main() вместо qt_customMain)\n"
            "   - Приоритет: ВЫСОКИЙ (блокирует рендеринг эффектов)"
        )

    if categories["fog_effect"]:
        recommendations.append(
            "2. Fog Effect ошибки:\n"
            "   - Проблема: Несоответствие манифеста шейдеров (пути post_effects/ vs effects/)\n"
            "   - Решение: Синхронизировать пути в FogEffect и файловой структуре\n"
            "   - Приоритет: СРЕДНИЙ (эффект работает, но с предупреждениями)"
        )

    if categories["depth_texture"]:
        recommendations.append(
            "3. Depth Texture ошибки:\n"
            "   - Проблема: ExtendedSceneEnvironment не поддерживает explicit*TextureEnabled\n"
            "   - Решение: Удалить попытки установки этих свойств из DepthTextureActivator\n"
            "   - Приоритет: НИЗКИЙ (не влияет на функциональность)"
        )

    if categories["qml_property"]:
        recommendations.append(
            "4. QML Property ошибки:\n"
            "   - Проблема: Попытки присвоения несуществующим свойствам\n"
            "   - Решение: Проверить имена свойств в QML компонентах\n"
            "   - Приоритет: СРЕДНИЙ (может сломать синхронизацию)"
        )

    for rec in recommendations:
        print(rec)
        print()

    print("=" * 80)
    print("✅ Анализ завершён")
    print("=" * 80)


if __name__ == "__main__":
    analyze_errors()
