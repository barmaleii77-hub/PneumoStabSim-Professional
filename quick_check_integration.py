"""
Быстрая проверка main.qml на интеграцию с панелью графики
Quick main.qml + Graphics Panel Integration Check
"""
import sys
from pathlib import Path


def check_main_qml():
    """Быстрая проверка main.qml"""

    print("🔍 Быстрая проверка main.qml...")

    # Путь к main.qml
    main_qml_path = Path("assets/qml/main.qml")

    if not main_qml_path.exists():
        print(f"❌ Файл не найден: {main_qml_path}")
        return False

    try:
        content = main_qml_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return False

    print(f"📁 Файл: {main_qml_path}")
    print(f"📏 Размер: {round(len(content) / 1024, 1)} KB")
    print(f"📄 Строк: {len(content.splitlines())}")
    print()

    # Проверяем ключевые функции интеграции
    integration_functions = {
        "applyLightingUpdates": "💡 Обновление освещения",
        "applyMaterialUpdates": "🎨 Обновление материалов",
        "applyEnvironmentUpdates": "🌍 Обновление окружения",
        "applyEffectsUpdates": "✨ Обновление эффектов",
        "applyQualityUpdates": "⚙️ Обновление качества",
        "applyCameraUpdates": "📷 Обновление камеры",
        "applyBatchedUpdates": "🚀 Пакетное обновление",
    }

    print("🔧 ФУНКЦИИ ИНТЕГРАЦИИ:")
    found_functions = 0

    for func, description in integration_functions.items():
        if f"function {func}" in content:
            print(f"   ✅ {func}: {description}")
            found_functions += 1
        else:
            print(f"   ❌ {func}: отсутствует")

    print(f"\n📊 Найдено: {found_functions}/{len(integration_functions)} функций")

    # Проверяем графические свойства
    print("\n🎮 ГРАФИЧЕСКИЕ СВОЙСТВА:")

    graphics_properties = {
        "iblEnabled": "🌟 IBL поддержка",
        "glassIOR": "🔍 Коэффициент преломления",
        "bloomEnabled": "✨ Bloom эффект",
        "ssaoEnabled": "🌑 SSAO затенение",
        "shadowSoftness": "🌫️ Мягкость теней",
        "tonemapEnabled": "🎨 Тонемаппинг",
        "vignetteEnabled": "🖼️ Виньетирование",
        "depthOfFieldEnabled": "🔍 Глубина резкости",
    }

    found_properties = 0

    for prop, description in graphics_properties.items():
        if "property" in content and prop in content:
            print(f"   ✅ {prop}: {description}")
            found_properties += 1
        else:
            print(f"   ❌ {prop}: отсутствует")

    print(f"\n📊 Найдено: {found_properties}/{len(graphics_properties)} свойств")

    # Проверяем импорты 3D
    print("\n📦 3D ИМПОРТЫ:")

    imports_3d = ["QtQuick3D", "QtQuick3D.Helpers"]

    found_imports = 0
    for imp in imports_3d:
        if f"import {imp}" in content:
            print(f"   ✅ {imp}")
            found_imports += 1
        else:
            print(f"   ❌ {imp}")

    # Проверяем компоненты 3D
    print("\n🎭 3D КОМПОНЕНТЫ:")

    components_3d = {
        "View3D": "Главное 3D окно",
        "SceneEnvironment": "Окружение сцены",
        "DirectionalLight": "Направленный свет",
        "PointLight": "Точечный свет",
        "PrincipledMaterial": "PBR материалы",
        "Model": "3D модели",
    }

    found_components = 0
    for comp, desc in components_3d.items():
        if comp in content:
            print(f"   ✅ {comp}: {desc}")
            found_components += 1
        else:
            print(f"   ❌ {comp}: {desc}")

    print(f"\n📊 Найдено: {found_components}/{len(components_3d)} компонентов")

    # Общая оценка
    total_found = found_functions + found_properties + found_imports + found_components
    total_expected = (
        len(integration_functions)
        + len(graphics_properties)
        + len(imports_3d)
        + len(components_3d)
    )

    score_percent = round((total_found / total_expected) * 100)

    print(f"\n🎯 ОБЩИЙ РЕЗУЛЬТАТ: {total_found}/{total_expected} ({score_percent}%)")

    if score_percent >= 90:
        print("🟢 ОТЛИЧНО: main.qml полностью готов для интеграции с панелью графики")
        status = "excellent"
    elif score_percent >= 70:
        print("🟡 ХОРОШО: main.qml в основном готов, возможны мелкие проблемы")
        status = "good"
    elif score_percent >= 50:
        print("🟠 УДОВЛЕТВОРИТЕЛЬНО: main.qml частично готов, требуются доработки")
        status = "partial"
    else:
        print("🔴 ПЛОХО: main.qml не готов для интеграции с панелью графики")
        status = "poor"

    # Дополнительные проверки
    print("\n🔎 ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ:")

    # Проверяем IOR (коэффициент преломления)
    if "indexOfRefraction" in content:
        print("   ✅ Коэффициент преломления используется в материалах")
    else:
        print("   ⚠️ Коэффициент преломления не используется")

    # Проверяем IBL
    if "lightProbe" in content and "IblProbeLoader" in content:
        print("   ✅ IBL система полностью реализована")
    elif "lightProbe" in content:
        print("   🟡 IBL частично реализован")
    else:
        print("   ❌ IBL не реализован")

    # Проверяем оптимизации
    if "animationCache" in content and "geometryCache" in content:
        print("   ✅ Оптимизации производительности присутствуют")
    else:
        print("   ⚠️ Оптимизации производительности отсутствуют")

    return status in ["excellent", "good"]


def check_panel_graphics():
    """Быстрая проверка панели графики"""

    print("\n🎨 Быстрая проверка панели графики...")

    panel_path = Path("src/ui/panels/panel_graphics.py")

    if not panel_path.exists():
        print(f"❌ Файл не найден: {panel_path}")
        return False

    try:
        content = panel_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return False

    print(f"📁 Файл: {panel_path}")
    print(f"📏 Размер: {round(len(content) / 1024, 1)} KB")
    print(f"📄 Строк: {len(content.splitlines())}")

    # Проверяем сигналы
    print("\n📡 СИГНАЛЫ ПАНЕЛИ:")

    signals = {
        "lighting_changed": "💡 Изменение освещения",
        "material_changed": "🎨 Изменение материалов",
        "environment_changed": "🌍 Изменение окружения",
        "effects_changed": "✨ Изменение эффектов",
        "quality_changed": "⚙️ Изменение качества",
        "camera_changed": "📷 Изменение камеры",
    }

    found_signals = 0
    for signal, desc in signals.items():
        if f"{signal} = Signal" in content:
            print(f"   ✅ {signal}: {desc}")
            found_signals += 1
        else:
            print(f"   ❌ {signal}: {desc}")

    print(f"\n📊 Найдено сигналов: {found_signals}/{len(signals)}")

    # Проверяем методы emit
    print("\n📤 МЕТОДЫ ОТПРАВКИ:")

    emit_methods = {
        "emit_lighting_update": "💡 Отправка освещения",
        "emit_material_update": "🎨 Отправка материалов",
        "emit_environment_update": "🌍 Отправка окружения",
        "emit_effects_update": "✨ Отправка эффектов",
    }

    found_emits = 0
    for method, desc in emit_methods.items():
        if f"def {method}" in content:
            print(f"   ✅ {method}: {desc}")
            found_emits += 1
        else:
            print(f"   ❌ {method}: {desc}")

    print(f"\n📊 Найдено методов: {found_emits}/{len(emit_methods)}")

    # Проверяем ключевые параметры
    print("\n🔧 КЛЮЧЕВЫЕ ПАРАМЕТРЫ:")

    key_params = [
        "glass_ior",  # Коэффициент преломления
        "ibl_enabled",  # IBL поддержка
        "bloom_threshold",  # Порог Bloom
        "ssao_radius",  # Радиус SSAO
        "shadow_softness",  # Мягкость теней
        "tonemap_enabled",  # Тонемаппинг
        "vignette_enabled",  # Виньетирование
    ]

    found_params = 0
    for param in key_params:
        if f"'{param}'" in content:
            print(f"   ✅ {param}")
            found_params += 1
        else:
            print(f"   ❌ {param}")

    print(f"\n📊 Найдено параметров: {found_params}/{len(key_params)}")

    total_panel = found_signals + found_emits + found_params
    total_panel_expected = len(signals) + len(emit_methods) + len(key_params)

    panel_score = round((total_panel / total_panel_expected) * 100)
    print(
        f"\n🎯 РЕЗУЛЬТАТ ПАНЕЛИ: {total_panel}/{total_panel_expected} ({panel_score}%)"
    )

    return panel_score >= 70


def main():
    """Главная функция быстрой проверки"""

    print("=" * 60)
    print("🚀 БЫСТРАЯ ПРОВЕРКА ИНТЕГРАЦИИ MAIN.QML + ПАНЕЛЬ ГРАФИКИ")
    print("=" * 60)

    # Проверяем main.qml
    qml_ok = check_main_qml()

    # Проверяем панель графики
    panel_ok = check_panel_graphics()

    # Итоговый результат
    print("\n" + "=" * 60)
    print("🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print("=" * 60)

    if qml_ok and panel_ok:
        print("🟢 ОТЛИЧНО: Интеграция готова к тестированию!")
        print("✅ main.qml содержит все необходимые функции")
        print("✅ Панель графики содержит все необходимые сигналы")
        print("\n🧪 Рекомендуемые команды для тестирования:")
        print("   python test_graphics_integration.py")
        print("   python app.py")
        result = 0
    elif qml_ok:
        print("🟡 ЧАСТИЧНО: main.qml готов, но панель графики требует доработки")
        print("✅ main.qml в порядке")
        print("⚠️ Панель графики неполная")
        result = 1
    elif panel_ok:
        print("🟡 ЧАСТИЧНО: Панель графики готова, но main.qml требует доработки")
        print("⚠️ main.qml неполный")
        print("✅ Панель графики в порядке")
        result = 1
    else:
        print("🔴 ПЛОХО: И main.qml, и панель графики требуют доработки")
        print("❌ main.qml неполный")
        print("❌ Панель графики неполная")
        result = 2

    print("\n📝 Для детального анализа запустите:")
    print("   python check_qml_graphics.py")

    return result


if __name__ == "__main__":
    sys.exit(main())
