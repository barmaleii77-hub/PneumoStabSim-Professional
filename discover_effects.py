#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Qt Quick 3D Effects Discovery Tool
Определяет, какие эффекты действительно доступны в текущей версии Qt
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def discover_qt_effects():
    """Исследует доступные эффекты Qt Quick 3D"""

    print("🔍 ПОИСК ДОСТУПНЫХ ЭФФЕКТОВ QT QUICK 3D")
    print("=" * 60)

    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtQml import QQmlApplicationEngine
        from PySide6.QtCore import QUrl
        import PySide6

        print(f"📦 PySide6 версия: {PySide6.__version__}")

        app = QApplication([])
        engine = QQmlApplicationEngine()

        # Список потенциальных эффектов для тестирования
        potential_effects = [
            # Основные эффекты
            "Bloom",
            "BloomEffect",
            "Glow",
            "GlowEffect",
            # SSAO эффекты
            "SSAO",
            "SSAOEffect",
            "AmbientOcclusion",
            # Tone mapping
            "ToneMapping",
            "TonemappingEffect",
            "Tonemap",
            # Depth of Field
            "DepthOfField",
            "DepthOfFieldEffect",
            "DOF",
            # Другие эффекты
            "Blur",
            "BlurEffect",
            "MotionBlur",
            "MotionBlurEffect",
            "Vignette",
            "VignetteEffect",
            "ColorGrading",
            "ColorGradingEffect",
            "ChromaticAberration",
            "FilmGrain",
            "Sharpen",
            "Noise",
            # Специальные эффекты
            "Fog",
            "FogEffect",
            "Scattering",
            "ScatteringEffect",
            "LensFlare",
            "GodRays",
            "Volumetric",
        ]

        available_effects = []
        unavailable_effects = []

        print(f"🧪 Тестирую {len(potential_effects)} потенциальных эффектов...\n")

        for effect in potential_effects:
            # Создаем минимальный QML для тестирования эффекта
            test_qml = f"""
import QtQuick
import QtQuick3D
import QtQuick3D.Effects 6.5

Item {{
    View3D {{
        anchors.fill: parent

        environment: SceneEnvironment {{
            backgroundMode: SceneEnvironment.Color
            clearColor: "#2a2a2a"
        }}

        PerspectiveCamera {{
            position: Qt.vector3d(0, 0, 500)
        }}

        DirectionalLight {{
            brightness: 1.0
        }}

        Model {{
            source: "#Cube"
            materials: PrincipledMaterial {{
                baseColor: "#ff6600"
            }}
        }}

        effects: [
            {effect} {{
                // Общие параметры
                enabled: true
            }}
        ]
    }}
}}
"""

            test_file = project_root / f"temp_test_{effect.lower()}.qml"

            try:
                test_file.write_text(test_qml, encoding="utf-8")

                engine.clearComponentCache()
                url = QUrl.fromLocalFile(str(test_file.absolute()))
                engine.load(url)

                if engine.rootObjects():
                    available_effects.append(effect)
                    print(f"✅ {effect:20} - ДОСТУПЕН")
                else:
                    unavailable_effects.append(effect)
                    print(f"❌ {effect:20} - не доступен")

            except Exception as e:
                unavailable_effects.append(effect)
                print(f"💥 {effect:20} - ошибка: {str(e)[:30]}...")

            finally:
                if test_file.exists():
                    test_file.unlink()

        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТЫ АНАЛИЗА:")
        print("=" * 60)

        print(f"✅ Доступные эффекты ({len(available_effects)}):")
        if available_effects:
            for effect in available_effects:
                print(f"   • {effect}")
        else:
            print("   Нет доступных эффектов")

        print(f"\n❌ Недоступные эффекты ({len(unavailable_effects)}):")
        for effect in unavailable_effects[:10]:  # Показываем только первые 10
            print(f"   • {effect}")
        if len(unavailable_effects) > 10:
            print(f"   ... и еще {len(unavailable_effects) - 10}")

        # Генерируем QML код для доступных эффектов
        if available_effects:
            print("\n🎨 РЕКОМЕНДОВАННЫЙ QML КОД:")
            print("-" * 40)
            print("effects: [")
            for i, effect in enumerate(available_effects):
                comma = "," if i < len(available_effects) - 1 else ""
                print(f"    {effect} {{")
                print("        enabled: true")
                # Добавляем специфичные параметры для известных эффектов
                if "bloom" in effect.lower() or "glow" in effect.lower():
                    print("        threshold: 0.7")
                    print("        intensity: 0.5")
                elif "ssao" in effect.lower():
                    print("        radius: 2.0")
                    print("        strength: 0.5")
                elif "tone" in effect.lower():
                    print("        mode: 1")
                print(f"    }}{comma}")
            print("]")

        app.quit()
        return available_effects

    except Exception as e:
        print(f"💀 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()
        return []


if __name__ == "__main__":
    try:
        available = discover_qt_effects()

        print("\n" + "🎯" * 20)
        print("ЗАКЛЮЧЕНИЕ:")
        print("🎯" * 20)

        if available:
            print(f"✅ Найдено {len(available)} работающих эффектов!")
            print("💡 Скопируйте рекомендованный QML код выше в main_v2_realism.qml")
        else:
            print("❌ Эффекты не поддерживаются в данной версии Qt")
            print("💡 Используйте effects: [] и сосредоточьтесь на освещении/материалах")

        print("\n🚀 После обновления QML файла приложение должно работать идеально!")

    except KeyboardInterrupt:
        print("\n🛑 Прервано пользователем")
    except Exception as e:
        print(f"\n💀 Ошибка: {e}")
        sys.exit(1)
