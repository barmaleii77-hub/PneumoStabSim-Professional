#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥 ДЕТЕКТИВНАЯ ПРОВЕРКА КРИТИЧЕСКИХ ПАРАМЕТРОВ ДО CANVAS
Трассировка ПОЛНОГО ПУТИ: Python → QML property → ExtendedSceneEnvironment → Рендеринг
"""

import re
from pathlib import Path

# Критические параметры для проверки
CRITICAL_PARAMS = {
    # Эффекты (КРИТИЧНО для качества)
    "bloomThreshold": {
        "description": "Порог Bloom эффекта",
        "expect_in_qml_property": True,
        "expect_in_environment": True,
        "qml_binding": "bloomThreshold:",
        "env_property": "glowHDRMinimumValue",
    },
    "ssaoRadius": {
        "description": "Радиус SSAO затенения",
        "expect_in_qml_property": True,
        "expect_in_environment": True,
        "qml_binding": "ssaoRadius:",
        "env_property": "aoDistance",
    },
    "shadowSoftness": {
        "description": "Мягкость теней",
        "expect_in_qml_property": True,
        "expect_in_light": True,
        "qml_binding": "shadowSoftness:",
        "light_property": "shadowFilter",
    },
    # Материалы (КРИТИЧНО для реализма)
    "glassIOR": {
        "description": "🔥 Коэффициент преломления стекла",
        "expect_in_qml_property": True,
        "expect_in_material": True,
        "qml_binding": "glassIOR:",
        "material_property": "indexOfRefraction",
    },
    # Окружение (КРИТИЧНО для освещения)
    "iblEnabled": {
        "description": "🌟 IBL включение",
        "expect_in_qml_property": True,
        "expect_in_environment": True,
        "qml_binding": "iblEnabled:",
        "env_property": "lightProbe",
    },
    "iblIntensity": {
        "description": "🌟 IBL интенсивность",
        "expect_in_qml_property": True,
        "expect_in_environment": True,
        "qml_binding": "iblIntensity:",
        "env_property": "probeExposure",
    },
    # Тонемаппинг (КРИТИЧНО для цвета)
    "tonemapModeIndex": {
        "description": "🎨 Режим тонемаппинга",
        "expect_in_qml_property": True,
        "expect_in_environment": True,
        "qml_binding": "tonemapMode:",
        "env_property": "tonemapMode",
    },
    # Depth of Field
    "dofFocusDistance": {
        "description": "📷 Дистанция фокуса",
        "expect_in_qml_property": True,
        "expect_in_environment": True,
        "qml_binding": "dofFocusDistance:",
        "env_property": "depthOfFieldFocusDistance",
    },
}


def check_python_panel():
    """Проверка наличия параметров в Python панели"""
    panel_file = Path("src/ui/panels/panel_graphics.py")

    if not panel_file.exists():
        print("❌ panel_graphics.py не найден!")
        return {}

    content = panel_file.read_text(encoding="utf-8")

    results = {}

    for param, info in CRITICAL_PARAMS.items():
        # Поиск в current_graphics
        pattern = rf"['\"]({param})['\"]"
        found_in_dict = bool(re.search(pattern, content))

        # Поиск UI компонента
        ui_pattern = rf"self\.{param}\s*="
        found_ui = bool(re.search(ui_pattern, content))

        # Поиск обработчика
        handler_pattern = rf"def on_{param}_changed"
        found_handler = bool(re.search(handler_pattern, content))

        # Поиск в emit функциях
        emit_pattern = rf"['\"]({param})['\"].*:"
        found_emit = bool(re.search(emit_pattern, content))

        results[param] = {
            "in_dict": found_in_dict,
            "has_ui": found_ui,
            "has_handler": found_handler,
            "in_emit": found_emit,
            "python_ok": found_in_dict and found_emit,
        }

    return results


def check_qml_properties():
    """Проверка наличия параметров как QML properties"""
    qml_file = Path("assets/qml/main.qml")

    if not qml_file.exists():
        print("❌ main.qml не найден!")
        return {}

    content = qml_file.read_text(encoding="utf-8")

    results = {}

    for param, info in CRITICAL_PARAMS.items():
        # Поиск property объявления
        property_pattern = rf"property\s+(real|int|bool|string|color|url)\s+{param}"
        found_property = bool(re.search(property_pattern, content))

        # Проверяем тип
        match = re.search(property_pattern, content)
        property_type = match.group(1) if match else None

        results[param] = {"declared": found_property, "type": property_type}

    return results


def check_qml_bindings():
    """Проверка привязки параметров к визуальным компонентам"""
    qml_file = Path("assets/qml/main.qml")

    if not qml_file.exists():
        return {}

    content = qml_file.read_text(encoding="utf-8")

    results = {}

    for param, info in CRITICAL_PARAMS.items():
        bindings_found = []

        # Поиск в ExtendedSceneEnvironment
        if info.get("expect_in_environment"):
            env_prop = info.get("env_property")
            if env_prop:
                # Ищем привязку вида: probeExposure: iblIntensity
                pattern = rf"{env_prop}\s*:\s*.*{param}"
                if re.search(pattern, content):
                    bindings_found.append(f"ExtendedSceneEnvironment.{env_prop}")

        # Поиск в PrincipledMaterial
        if info.get("expect_in_material"):
            mat_prop = info.get("material_property")
            if mat_prop:
                pattern = rf"{mat_prop}\s*:\s*.*{param}"
                if re.search(pattern, content):
                    bindings_found.append(f"PrincipledMaterial.{mat_prop}")

        # Поиск в DirectionalLight
        if info.get("expect_in_light"):
            light_prop = info.get("light_property")
            if light_prop:
                pattern = rf"{light_prop}\s*:\s*.*{param}"
                if re.search(pattern, content):
                    bindings_found.append(f"DirectionalLight.{light_prop}")

        results[param] = {
            "bound_to": bindings_found,
            "is_bound": len(bindings_found) > 0,
        }

    return results


def check_update_functions():
    """Проверка обработки параметров в update функциях"""
    qml_file = Path("assets/qml/main.qml")

    if not qml_file.exists():
        return {}

    content = qml_file.read_text(encoding="utf-8")

    results = {}

    # Определяем к какой update функции относится каждый параметр
    update_functions = {
        "applyEffectsUpdates": [
            "bloomThreshold",
            "ssaoRadius",
            "dofFocusDistance",
            "tonemapMode",
        ],
        "applyMaterialUpdates": ["glassIOR"],
        "applyEnvironmentUpdates": ["iblEnabled", "iblIntensity"],
        "applyQualityUpdates": ["shadowSoftness"],
    }

    for func_name, params in update_functions.items():
        # Находим тело функции
        func_start = content.find(f"function {func_name}")
        if func_start == -1:
            continue

        # Находим конец функции
        func_end = content.find("\n    }", func_start)
        if func_end == -1:
            func_end = content.find("\n    function ", func_start + 1)
        if func_end == -1:
            func_end = len(content)

        func_body = content[func_start:func_end]

        # Проверяем каждый параметр
        for param in params:
            if param in CRITICAL_PARAMS:
                # Ищем присваивание
                pattern = rf"{param}\s*="
                is_assigned = bool(re.search(pattern, func_body))

                if param not in results:
                    results[param] = {}

                results[param]["in_update_func"] = func_name if is_assigned else None
                results[param]["is_updated"] = is_assigned

    return results


def main():
    """Главная функция детективной проверки"""

    print("🔍 ДЕТЕКТИВНАЯ ПРОВЕРКА КРИТИЧЕСКИХ ПАРАМЕТРОВ")
    print("=" * 80)
    print()

    # ШАГ 1: Python Panel
    print("📋 ШАГ 1: Проверка Python Panel (panel_graphics.py)")
    print("-" * 80)
    python_results = check_python_panel()

    for param, result in python_results.items():
        status = "✅" if result["python_ok"] else "❌"
        print(
            f"{status} {param:20s} - Словарь:{result['in_dict']} | UI:{result['has_ui']} | Handler:{result['has_handler']} | Emit:{result['in_emit']}"
        )

    print()

    # ШАГ 2: QML Properties
    print("📋 ШАГ 2: Проверка QML Properties (main.qml)")
    print("-" * 80)
    qml_prop_results = check_qml_properties()

    for param, result in qml_prop_results.items():
        status = "✅" if result["declared"] else "❌"
        prop_type = result["type"] or "NONE"
        print(
            f"{status} {param:20s} - Объявлен: {result['declared']:5} | Тип: {prop_type}"
        )

    print()

    # ШАГ 3: QML Bindings (КРИТИЧНО!)
    print("📋 ШАГ 3: Проверка привязок к Canvas (main.qml)")
    print("-" * 80)
    binding_results = check_qml_bindings()

    for param, result in binding_results.items():
        status = "✅" if result["is_bound"] else "❌ СЛОМАНО"
        bindings = (
            ", ".join(result["bound_to"])
            if result["bound_to"]
            else "НЕ ПРИВЯЗАН К РЕНДЕРИНГУ!"
        )
        print(f"{status} {param:20s} - Привязки: {bindings}")

    print()

    # ШАГ 4: Update Functions
    print("📋 ШАГ 4: Проверка Update Functions (main.qml)")
    print("-" * 80)
    update_results = check_update_functions()

    for param, result in update_results.items():
        status = "✅" if result.get("is_updated") else "❌"
        func = result.get("in_update_func") or "НЕ ОБРАБАТЫВАЕТСЯ"
        print(f"{status} {param:20s} - Функция: {func}")

    print()
    print("=" * 80)

    # ФИНАЛЬНЫЙ АНАЛИЗ
    broken_params = []

    for param, info in CRITICAL_PARAMS.items():
        # Проверяем полную цепочку
        python_ok = python_results.get(param, {}).get("python_ok", False)
        qml_declared = qml_prop_results.get(param, {}).get("declared", False)
        is_bound = binding_results.get(param, {}).get("is_bound", False)
        is_updated = update_results.get(param, {}).get("is_updated", False)

        if not (python_ok and qml_declared and is_bound and is_updated):
            broken_params.append(
                (
                    param,
                    info["description"],
                    {
                        "python": python_ok,
                        "qml_prop": qml_declared,
                        "binding": is_bound,
                        "update": is_updated,
                    },
                )
            )

    if broken_params:
        print("🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ!")
        print("=" * 80)
        print(f"Найдено {len(broken_params)} сломанных параметров:\n")

        for param, desc, status in broken_params:
            print(f"❌ {param} - {desc}")
            print(f"   Python панель: {'✅' if status['python'] else '❌'}")
            print(f"   QML property:  {'✅' if status['qml_prop'] else '❌'}")
            print(
                f"   Привязка:      {'✅' if status['binding'] else '❌ НЕ ПРИВЯЗАН К CANVAS!'}"
            )
            print(f"   Update func:   {'✅' if status['update'] else '❌'}")
            print()

        print("💡 РЕШЕНИЕ:")
        print(
            "   Нужно добавить привязки в ExtendedSceneEnvironment/PrincipledMaterial/Light"
        )
        print("=" * 80)
    else:
        print("🎉 ВСЕ КРИТИЧЕСКИЕ ПАРАМЕТРЫ РАБОТАЮТ КОРРЕКТНО!")
        print("=" * 80)
        print("Все параметры правильно привязаны к Canvas рендерингу!")

    return len(broken_params)


if __name__ == "__main__":
    import sys

    sys.exit(main())
