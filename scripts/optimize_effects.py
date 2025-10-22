#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простая проверка версии Qt и создание оптимальной конфигурации эффектов
"""

import sys
from pathlib import Path


def check_pyside_version():
    """Проверяет версию PySide6 и создает оптимальную конфигурацию эффектов"""

    print("=" * 60)
    print("PYSIDE6 VERSION CHECK & EFFECTS OPTIMIZER")
    print("=" * 60)

    try:
        import PySide6
        from PySide6.QtCore import qVersion

        pyside_version = PySide6.__version__
        qt_version = qVersion()

        print(f"✅ PySide6 version: {pyside_version}")
        print(f"✅ Qt version: {qt_version}")

        # Определяем поддерживаемые эффекты на основе версии Qt
        major, minor = map(int, qt_version.split(".")[:2])
        qt_version_num = major * 100 + minor  # 6.5 -> 605, 6.7 -> 607

        print(f"📊 Qt version number: {qt_version_num}")

        # Конфигурации эффектов для разных версий Qt
        effects_config = {
            605: {  # Qt 6.5
                "available": ["BloomEffect"],
                "description": "Базовая поддержка эффектов",
            },
            606: {  # Qt 6.6
                "available": ["BloomEffect", "SSAOEffect"],
                "description": "Добавлена поддержка SSAO",
            },
            607: {  # Qt 6.7+
                "available": [
                    "BloomEffect",
                    "SSAOEffect",
                    "TonemappingEffect",
                    "DepthOfFieldEffect",
                ],
                "description": "Полная поддержка эффектов",
            },
        }

        # Выбираем конфигурацию
        config = None
        for version_threshold in sorted(effects_config.keys(), reverse=True):
            if qt_version_num >= version_threshold:
                config = effects_config[version_threshold]
                break

        if not config:
            config = {"available": [], "description": "Эффекты не поддерживаются"}

        print(f"🎨 {config['description']}")
        print(f"✅ Доступные эффекты: {len(config['available'])}")

        for effect in config["available"]:
            print(f"   • {effect}")

        # Генерируем QML код
        qml_code = generate_effects_qml(config["available"])

        print("\n📝 ОПТИМАЛЬНАЯ QML КОНФИГУРАЦИЯ:")
        print("-" * 60)
        print(qml_code)

        # Сохраняем конфигурацию в файл
        config_file = Path("assets/qml/effects_config_optimized.qml")
        config_file.write_text(qml_code, encoding="utf-8")
        print(f"\n💾 Конфигурация сохранена в: {config_file}")

        return config["available"]

    except ImportError as e:
        print(f"❌ PySide6 не найден: {e}")
        return []
    except Exception as e:
        print(f"💀 Ошибка: {e}")
        return []


def generate_effects_qml(available_effects):
    """Генерирует оптимальный QML код для эффектов"""

    if not available_effects:
        return "        // Эффекты недоступны в данной версии Qt\n        effects: []"

    effects_code = []
    effects_code.append("        // --- ОПТИМИЗИРОВАННЫЕ ПОСТ-ЭФФЕКТЫ ---")
    effects_code.append("        effects: [")

    for i, effect in enumerate(available_effects):
        comma = "," if i < len(available_effects) - 1 else ""

        if effect == "BloomEffect":
            effects_code.extend(
                [
                    "            BloomEffect {",
                    "                id: bloom",
                    "                enabled: root.bloomEnabled",
                    "                threshold: root.bloomThreshold || 0.7",
                    "                strength: root.bloomIntensity || 0.3",
                    f"            }}{comma}",
                ]
            )
        elif effect == "SSAOEffect":
            effects_code.extend(
                [
                    "            SSAOEffect {",
                    "                id: ssao",
                    "                enabled: root.ssaoEnabled",
                    "                radius: root.ssaoRadius || 2.0",
                    "                strength: root.ssaoIntensity || 0.5",
                    f"            }}{comma}",
                ]
            )
        elif effect == "TonemappingEffect":
            effects_code.extend(
                [
                    "            TonemappingEffect {",
                    "                id: tonemap",
                    "                enabled: root.tonemapEnabled",
                    "                mode: [",
                    "                    TonemappingEffect.Mode.None,",
                    "                    TonemappingEffect.Mode.Linear,",
                    "                    TonemappingEffect.Mode.Reinhard,",
                    "                    TonemappingEffect.Mode.Filmic",
                    "                ][root.tonemapMode || 2]",
                    f"            }}{comma}",
                ]
            )
        elif effect == "DepthOfFieldEffect":
            effects_code.extend(
                [
                    "            DepthOfFieldEffect {",
                    "                id: dof",
                    "                enabled: root.depthOfFieldEnabled || false",
                    "                focusDistance: root.dofFocusDistance || 2000",
                    "                focusRange: root.dofFocusRange || 1000",
                    f"            }}{comma}",
                ]
            )
        else:
            # Общий шаблон для неизвестных эффектов
            effects_code.extend(
                [
                    f"            {effect} {{",
                    "                enabled: true",
                    f"            }}{comma}",
                ]
            )

    effects_code.append("        ]")

    return "\n".join(effects_code)


if __name__ == "__main__":
    try:
        print("🚀 Проверяем версию Qt и оптимизируем эффекты...")
        available = check_pyside_version()

        print("\n" + "=" * 60)
        print("🎯 РЕКОМЕНДАЦИИ:")
        print("=" * 60)

        if available:
            print("✅ Эффекты доступны! Рекомендуется:")
            print("   1. Скопировать сгенерированный код в main_v2_realism.qml")
            print("   2. Заменить текущий блок effects: [...]")
            print("   3. Перезапустить приложение")
        else:
            print("⚠️ Эффекты недоступны. Рекомендуется:")
            print("   1. Обновить PySide6: pip install --upgrade PySide6")
            print("   2. Использовать effects: [] в QML")
            print("   3. Сосредоточиться на освещении и материалах")

        print("\n🎨 Для максимального реализма важнее всего:")
        print("   • Правильное PBR-освещение (уже настроено)")
        print("   • Качественные материалы (уже настроено)")
        print("   • HDR окружение (уже настроено)")
        print("   • Эффекты — это дополнение, а не основа")

    except KeyboardInterrupt:
        print("\n🛑 Прервано пользователем")
    except Exception as e:
        print(f"\n💀 Ошибка: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
