#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 ПОЛНАЯ ТРАССИРОВКА ГРАФИЧЕСКИХ ПАРАМЕТРОВ ДО CANVAS
Проверяем ВЕСЬ ПУТЬ: Python → QML → ExtendedSceneEnvironment → Canvas Rendering
"""

import sys
from pathlib import Path


def trace_parameter_to_canvas(param_name: str):
    """Трассировка параметра от Python до Canvas"""

    print(f"\n{'='*80}")
    print(f"🔍 ТРАССИРОВКА ПАРАМЕТРА: {param_name}")
    print(f"{'='*80}")

    # ШАГ 1: Проверка в GraphicsPanel
    graphics_panel = Path("src/ui/panels/panel_graphics.py")
    if graphics_panel.exists():
        content = graphics_panel.read_text(encoding="utf-8")

        # Поиск параметра в current_graphics
        if f"'{param_name}'" in content or f'"{param_name}"' in content:
            print("✅ ШАГ 1: Найден в GraphicsPanel current_graphics")

            # Поиск emit функции
            emit_found = False
            for emit_func in [
                "emit_lighting_update",
                "emit_material_update",
                "emit_environment_update",
                "emit_quality_update",
                "emit_camera_update",
                "emit_effects_update",
            ]:
                if f"def {emit_func}" in content:
                    func_start = content.find(f"def {emit_func}")
                    func_end = content.find("\n    def ", func_start + 1)
                    if func_end == -1:
                        func_end = len(content)
                    func_body = content[func_start:func_end]

                    if param_name in func_body:
                        print(f"✅ ШАГ 2: Параметр отправляется через {emit_func}()")
                        emit_found = True

                        # Проверяем сигнал
                        signal_name = emit_func.replace("emit_", "") + "_changed"
                        if signal_name in content:
                            print(f"✅ ШАГ 3: Сигнал {signal_name} существует")
                        else:
                            print(f"❌ ШАГ 3: Сигнал {signal_name} НЕ НАЙДЕН!")
                        break

            if not emit_found:
                print("❌ ШАГ 2: Параметр НЕ отправляется в QML!")
        else:
            print("❌ ШАГ 1: Параметр НЕ найден в GraphicsPanel!")
            return

    # ШАГ 4: Проверка в MainWindow
    main_window = Path("src/ui/main_window.py")
    if main_window.exists():
        content = main_window.read_text(encoding="utf-8")

        # Поиск подключения сигнала
        handler_found = False
        for handler in [
            "_on_lighting_changed",
            "_on_material_changed",
            "_on_environment_changed",
            "_on_quality_changed",
            "_on_camera_changed",
            "_on_effects_changed",
        ]:
            if handler in content:
                handler_start = content.find(f"def {handler}")
                handler_end = content.find("\n    def ", handler_start + 1)
                if handler_end == -1:
                    handler_end = content.find("\n    @Slot", handler_start + 1)
                if handler_end == -1:
                    handler_end = len(content)
                handler_body = content[handler_start:handler_end]

                if (
                    "invokeMethod" in handler_body
                    or "updateLighting" in handler_body
                    or "updateMaterials" in handler_body
                    or "updateEnvironment" in handler_body
                    or "updateQuality" in handler_body
                    or "updateEffects" in handler_body
                ):
                    print(f"✅ ШАГ 4: MainWindow вызывает QML функцию через {handler}")
                    handler_found = True
                    break

        if not handler_found:
            print("❌ ШАГ 4: MainWindow НЕ вызывает QML функцию!")

    # ШАГ 5: Проверка в main.qml
    main_qml = Path("assets/qml/main.qml")
    if main_qml.exists():
        content = main_qml.read_text(encoding="utf-8")

        # Проверка property
        qml_property_found = False
        for prop_pattern in [
            f"property real {param_name}",
            f"property bool {param_name}",
            f"property int {param_name}",
            f"property string {param_name}",
            f"property color {param_name}",
            f"property url {param_name}",
        ]:
            if prop_pattern in content:
                print(f"✅ ШАГ 5: QML property объявлен: {prop_pattern}")
                qml_property_found = True
                break

        if not qml_property_found:
            print(f"❌ ШАГ 5: QML property {param_name} НЕ ОБЪЯВЛЕН!")
            return

        # ШАГ 6: Проверка update функций
        update_found = False
        for update_func in [
            "applyLightingUpdates",
            "applyMaterialUpdates",
            "applyEnvironmentUpdates",
            "applyQualityUpdates",
            "applyCameraUpdates",
            "applyEffectsUpdates",
        ]:
            if f"function {update_func}" in content:
                func_start = content.find(f"function {update_func}")
                func_end = content.find("\n    }", func_start)
                if func_end == -1:
                    func_end = content.find("\n    function ", func_start + 1)
                if func_end == -1:
                    func_end = len(content)
                func_body = content[func_start:func_end]

                if param_name in func_body:
                    print(f"✅ ШАГ 6: Параметр обрабатывается в {update_func}()")

                    # Проверяем присваивание
                    if f"{param_name} =" in func_body:
                        print("✅ ШАГ 7: Параметр ПРИСВАИВАЕТСЯ в QML property")
                        update_found = True
                    else:
                        print("❌ ШАГ 7: Параметр НЕ присваивается!")
                    break

        if not update_found:
            print("❌ ШАГ 6: Параметр НЕ обрабатывается в update функциях!")
            return

        # ШАГ 8: КРИТИЧЕСКИЙ - Проверка использования в ExtendedSceneEnvironment или материалах
        canvas_found = False

        # Проверка в ExtendedSceneEnvironment
        if "ExtendedSceneEnvironment {" in content:
            env_start = content.find("ExtendedSceneEnvironment {")
            env_end = content.find("\n        }", env_start)
            if env_end == -1:
                env_end = len(content)
            env_body = content[env_start:env_end]

            # Проверяем привязку параметра к свойству ExtendedSceneEnvironment
            if f": {param_name}" in env_body or f": root.{param_name}" in env_body:
                print("✅ ШАГ 8: Параметр ПРИВЯЗАН к ExtendedSceneEnvironment!")
                canvas_found = True

                # Детальная проверка какое свойство использует
                for line in env_body.split("\n"):
                    if param_name in line and ":" in line:
                        prop_name = line.split(":")[0].strip()
                        print(f"   📌 Привязка: {prop_name}: {param_name}")
            else:
                print("⚠️ ШАГ 8: Параметр НЕ привязан к ExtendedSceneEnvironment!")

        # Проверка в материалах (PrincipledMaterial)
        if "PrincipledMaterial {" in content:
            mat_positions = []
            start = 0
            while True:
                pos = content.find("PrincipledMaterial {", start)
                if pos == -1:
                    break
                mat_positions.append(pos)
                start = pos + 1

            for mat_start in mat_positions:
                mat_end = content.find("\n            }", mat_start)
                if mat_end == -1:
                    mat_end = len(content)
                mat_body = content[mat_start:mat_end]

                if f": {param_name}" in mat_body or f": root.{param_name}" in mat_body:
                    print("✅ ШАГ 8: Параметр ПРИВЯЗАН к PrincipledMaterial!")
                    canvas_found = True

                    # Детальная проверка
                    for line in mat_body.split("\n"):
                        if param_name in line and ":" in line:
                            prop_name = line.split(":")[0].strip()
                            print(f"   📌 Привязка материала: {prop_name}: {param_name}")
                    break

        # Проверка в DirectionalLight/PointLight
        for light_type in ["DirectionalLight {", "PointLight {"]:
            if light_type in content:
                light_start = content.find(light_type)
                light_end = content.find("\n        }", light_start)
                if light_end == -1:
                    light_end = len(content)
                light_body = content[light_start:light_end]

                if (
                    f": {param_name}" in light_body
                    or f": root.{param_name}" in light_body
                ):
                    print(
                        f"✅ ШАГ 8: Параметр ПРИВЯЗАН к {light_type.replace(' {', '')}!"
                    )
                    canvas_found = True

                    for line in light_body.split("\n"):
                        if param_name in line and ":" in line:
                            prop_name = line.split(":")[0].strip()
                            print(f"   📌 Привязка света: {prop_name}: {param_name}")

        if not canvas_found:
            print("❌ ШАГ 8 КРИТИЧЕСКИЙ: Параметр НЕ ИСПОЛЬЗУЕТСЯ В РЕНДЕРИНГЕ!")
            print("   ⚠️ Параметр есть в QML, но НЕ ПРИВЯЗАН к визуальным компонентам!")
            print(
                "   💡 Нужно добавить привязку к ExtendedSceneEnvironment/PrincipledMaterial/Light"
            )
        else:
            print("✅ ПОЛНАЯ ЦЕПОЧКА: Python → QML → Canvas РАБОТАЕТ!")

    print(f"{'='*80}\n")


def main():
    """Главная функция - проверяем все критические параметры"""

    print("🔍 ДЕТЕКТИВНАЯ ПРОВЕРКА ГРАФИЧЕСКИХ ПАРАМЕТРОВ ДО CANVAS")
    print("=" * 80)

    # Критические параметры для проверки
    critical_params = {
        # Освещение
        "keyLightBrightness": "Яркость основного света",
        "keyLightColor": "Цвет основного света",
        "fillLightBrightness": "Яркость заполняющего света",
        "pointLightBrightness": "Яркость точечного света",
        # Материалы - КРИТИЧНО!
        "metalRoughness": "Шероховатость металла",
        "metalMetalness": "Металличность",
        "glassOpacity": "Прозрачность стекла",
        "glassRoughness": "Шероховатость стекла",
        "glassIOR": "🔥 КОЭФФИЦИЕНТ ПРЕЛОМЛЕНИЯ (IOR)",
        # Окружение
        "backgroundColor": "Цвет фона",
        "iblEnabled": "🔥 IBL ВКЛЮЧЕНИЕ",
        "iblIntensity": "🔥 IBL ИНТЕНСИВНОСТЬ",
        "skyboxEnabled": "Skybox включение",
        "fogEnabled": "Туман включение",
        # Эффекты
        "bloomEnabled": "Bloom включение",
        "bloomIntensity": "Bloom интенсивность",
        "bloomThreshold": "🔥 BLOOM ПОРОГ",
        "ssaoEnabled": "SSAO включение",
        "ssaoIntensity": "SSAO интенсивность",
        "ssaoRadius": "🔥 SSAO РАДИУС",
        "tonemapEnabled": "🔥 ТОНЕМАППИНГ ВКЛЮЧЕНИЕ",
        "tonemapMode": "🔥 РЕЖИМ ТОНЕМАППИНГА",
        "depthOfFieldEnabled": "Depth of Field",
        "dofFocusDistance": "🔥 DOF ДИСТАНЦИЯ ФОКУСА",
        "lensFlareEnabled": "Lens Flare включение",
        # Качество
        "shadowsEnabled": "Тени включение",
        "shadowSoftness": "🔥 МЯГКОСТЬ ТЕНЕЙ",
        "antialiasingMode": "Режим сглаживания",
    }

    broken_params = []
    working_params = []

    for param, description in critical_params.items():
        print(f"\n{'🔥' if '🔥' in description else '📝'} Проверяем: {description}")

        # Запускаем трассировку
        import io
        import contextlib

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            trace_parameter_to_canvas(param)

        result = output.getvalue()

        # Анализируем результат
        if "❌ ШАГ 8 КРИТИЧЕСКИЙ" in result:
            broken_params.append((param, description, "НЕ ПРИВЯЗАН К CANVAS"))
            print(f"❌ СЛОМАНО: {param} - НЕ привязан к рендерингу!")
        elif "❌" in result:
            broken_params.append((param, description, "ПРОБЛЕМА В ЦЕПОЧКЕ"))
            print(f"⚠️ ПРОБЛЕМА: {param} - есть ошибки в цепочке")
        else:
            working_params.append((param, description))
            print(f"✅ РАБОТАЕТ: {param}")

    # ФИНАЛЬНЫЙ ОТЧЕТ
    print("\n" + "=" * 80)
    print("📊 ФИНАЛЬНЫЙ АНАЛИЗ - ВЛИЯНИЕ НА КАРТИНКУ")
    print("=" * 80)

    print(f"\n✅ РАБОТАЮЩИЕ ПАРАМЕТРЫ ({len(working_params)}/{len(critical_params)}):")
    for param, desc in working_params:
        print(f"   ✅ {param}: {desc}")

    if broken_params:
        print(f"\n❌ СЛОМАННЫЕ ПАРАМЕТРЫ ({len(broken_params)}/{len(critical_params)}):")
        for param, desc, reason in broken_params:
            print(f"   ❌ {param}: {desc}")
            print(f"      💥 ПРИЧИНА: {reason}")

        print("\n" + "=" * 80)
        print("🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА ОБНАРУЖЕНА!")
        print("=" * 80)
        print(
            f"Найдено {len(broken_params)} параметров, которые НЕ ВЛИЯЮТ на картинку!"
        )
        print("Параметры доходят до QML, но НЕ ПРИВЯЗАНЫ к визуальным компонентам!")
        print("\n💡 РЕШЕНИЕ:")
        print("   1. Открыть assets/qml/main.qml")
        print("   2. Найти ExtendedSceneEnvironment { ... }")
        print("   3. Добавить привязки для сломанных параметров")
        print("   4. Пример: bloomThreshold: root.bloomThreshold")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("🎉 ВСЕ ПАРАМЕТРЫ РАБОТАЮТ КОРРЕКТНО!")
        print("=" * 80)
        print("Все графические параметры правильно привязаны к Canvas!")
        print("Изменения в панели графики должны влиять на картинку.")
        print("=" * 80)

    return len(broken_params)


if __name__ == "__main__":
    sys.exit(main())
