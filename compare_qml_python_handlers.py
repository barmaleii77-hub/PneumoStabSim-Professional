# -*- coding: utf-8 -*-
"""
Скрипт для сравнения обработчиков между QML и panel_graphics.py
Находит недостающие свойства и обработчики
"""

import re
from pathlib import Path


def extract_qml_properties(qml_file):
    """Извлечь свойства из QML файла"""
    with open(qml_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем property объявления
    pattern = r"property\s+(\w+)\s+(\w+):\s*([^\n]+)"
    matches = re.findall(pattern, content)

    properties = {}
    for prop_type, prop_name, default_value in matches:
        properties[prop_name] = {"type": prop_type, "default": default_value.strip()}

    return properties


def extract_qml_functions(qml_file):
    """Извлечь функции из QML файла"""
    with open(qml_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем function объявления
    pattern = r"function\s+(\w+)\s*\([^)]*\)"
    matches = re.findall(pattern, content)

    return set(matches)


def extract_python_handlers(py_file):
    """Извлечь обработчики из Python файла"""
    with open(py_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем @Slot обработчики
    pattern = r"def\s+(on_\w+_changed)\s*\("
    matches = re.findall(pattern, content)

    return set(matches)


def extract_python_signals(py_file):
    """Извлечь сигналы из Python файла"""
    with open(py_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем Signal объявления
    pattern = r"(\w+_changed)\s*=\s*Signal"
    matches = re.findall(pattern, content)

    return set(matches)


def extract_python_properties(py_file):
    """Извлечь свойства из current_graphics словаря"""
    with open(py_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Ищем self.current_graphics словарь
    pattern = r"'(\w+)':\s*([^,\n]+)"
    matches = re.findall(pattern, content)

    properties = {}
    for prop_name, default_value in matches:
        properties[prop_name] = default_value.strip()

    return properties


def main():
    """Основная функция"""
    qml_file = Path("assets/qml/main_optimized.qml")
    py_file = Path("src/ui/panels/panel_graphics.py")

    if not qml_file.exists():
        print(f"❌ QML файл не найден: {qml_file}")
        return

    if not py_file.exists():
        print(f"❌ Python файл не найден: {py_file}")
        return

    print("=" * 80)
    print("🔍 СРАВНЕНИЕ ОБРАБОТЧИКОВ QML И PYTHON")
    print("=" * 80)

    # Извлекаем данные
    qml_props = extract_qml_properties(qml_file)
    qml_funcs = extract_qml_functions(qml_file)
    py_handlers = extract_python_handlers(py_file)
    py_signals = extract_python_signals(py_file)
    py_props = extract_python_properties(py_file)

    print("\n📊 СТАТИСТИКА:")
    print(f"   QML свойства: {len(qml_props)}")
    print(f"   QML функции: {len(qml_funcs)}")
    print(f"   Python обработчики: {len(py_handlers)}")
    print(f"   Python сигналы: {len(py_signals)}")
    print(f"   Python свойства: {len(py_props)}")

    # Проверяем соответствие
    print("\n🔍 АНАЛИЗ НЕДОСТАЮЩИХ ОБРАБОТЧИКОВ:")
    print("-" * 80)

    # Свойства в Python, но не в QML
    missing_in_qml = set()
    for py_prop in py_props.keys():
        # Преобразуем snake_case в camelCase для поиска
        camel_case_variants = [
            py_prop,
            "".join(
                word.capitalize() if i > 0 else word
                for i, word in enumerate(py_prop.split("_"))
            ),
        ]

        found = False
        for variant in camel_case_variants:
            if variant in qml_props:
                found = True
                break

        if not found:
            missing_in_qml.add(py_prop)

    if missing_in_qml:
        print(f"\n❌ СВОЙСТВА В PYTHON, НО НЕ В QML ({len(missing_in_qml)}):")
        for prop in sorted(missing_in_qml):
            print(f"   - {prop} = {py_props[prop]}")
    else:
        print("\n✅ Все свойства из Python присутствуют в QML")

    # Свойства в QML, но не в Python
    missing_in_python = set()
    for qml_prop in qml_props.keys():
        # Преобразуем camelCase в snake_case для поиска
        snake_case = re.sub(r"([A-Z])", r"_\1", qml_prop).lower().lstrip("_")

        if snake_case not in py_props and qml_prop not in py_props:
            missing_in_python.add(qml_prop)

    if missing_in_python:
        print(f"\n⚠️ СВОЙСТВА В QML, НО НЕ В PYTHON ({len(missing_in_python)}):")
        for prop in sorted(missing_in_python):
            prop_info = qml_props[prop]
            print(f"   - {prop}: {prop_info['type']} = {prop_info['default']}")
    else:
        print("\n✅ Все свойства из QML учтены в Python")

    # Функции обновления в QML
    update_functions = {
        f for f in qml_funcs if "update" in f.lower() or "apply" in f.lower()
    }

    print(f"\n📝 ФУНКЦИИ ОБНОВЛЕНИЯ В QML ({len(update_functions)}):")
    for func in sorted(update_functions):
        print(f"   - {func}()")

    # Обработчики в Python
    print(f"\n🔧 ОБРАБОТЧИКИ В PYTHON ({len(py_handlers)}):")
    handler_groups = {}
    for handler in sorted(py_handlers):
        # Группируем по префиксу
        prefix = handler.split("_")[1] if "_" in handler else "other"
        if prefix not in handler_groups:
            handler_groups[prefix] = []
        handler_groups[prefix].append(handler)

    for prefix, handlers in sorted(handler_groups.items()):
        print(f"\n   [{prefix.upper()}] ({len(handlers)} обработчиков):")
        for handler in handlers:
            print(f"      - {handler}()")

    # Сигналы в Python
    print(f"\n📡 СИГНАЛЫ В PYTHON ({len(py_signals)}):")
    for signal in sorted(py_signals):
        print(f"   - {signal}")

    # Рекомендации
    print("\n💡 РЕКОМЕНДАЦИИ:")
    print("-" * 80)

    if missing_in_qml:
        print("\n1. Добавить в QML следующие свойства:")
        for prop in sorted(missing_in_qml)[:5]:  # Показываем первые 5
            snake_to_camel = "".join(
                word.capitalize() if i > 0 else word
                for i, word in enumerate(prop.split("_"))
            )
            default_val = py_props[prop]

            # Определяем тип
            if default_val in ["true", "false", "True", "False"]:
                prop_type = "bool"
            elif default_val.startswith("#"):
                prop_type = "string"
            elif "." in default_val:
                prop_type = "real"
            else:
                prop_type = "int"

            print(f"   property {prop_type} {snake_to_camel}: {default_val}")

    if missing_in_python:
        print("\n2. Добавить в Python обработчики для:")
        for prop in sorted(missing_in_python)[:5]:  # Показываем первые 5
            snake_case = re.sub(r"([A-Z])", r"_\1", prop).lower().lstrip("_")
            print("   @Slot(...)")
            print(f"   def on_{snake_case}_changed(self, value):")
            print(f"       self.current_graphics['{snake_case}'] = value")
            print("       self.emit_..._update()")
            print()

    # Проверяем наличие критических функций
    critical_functions = [
        "applyBatchedUpdates",
        "applyGeometryUpdates",
        "applyLightingUpdates",
        "applyMaterialUpdates",
        "applyEnvironmentUpdates",
        "applyQualityUpdates",
        "applyCameraUpdates",
        "applyEffectsUpdates",
    ]

    missing_critical = set(critical_functions) - qml_funcs

    if missing_critical:
        print("\n⚠️ КРИТИЧЕСКИЕ ФУНКЦИИ ОТСУТСТВУЮТ В QML:")
        for func in missing_critical:
            print(f"   - {func}()")
    else:
        print("\n✅ Все критические функции обновления присутствуют в QML")

    print("\n" + "=" * 80)
    print("✅ АНАЛИЗ ЗАВЕРШЕН")
    print("=" * 80)


if __name__ == "__main__":
    main()
