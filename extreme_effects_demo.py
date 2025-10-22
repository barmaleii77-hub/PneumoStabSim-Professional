#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎪 ЭКСТРЕМАЛЬНАЯ ДЕМОНСТРАЦИЯ ЭФФЕКТОВ
Делаем туман и сглаживание максимально заметными
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ui.main_window import MainWindow


def extreme_effects_demo():
    """Экстремальная демонстрация эффектов"""
    print("🎪 ЭКСТРЕМАЛЬНАЯ ДЕМОНСТРАЦИЯ ЭФФЕКТОВ")
    print("=" * 70)
    print("Делаем эффекты МАКСИМАЛЬНО ЗАМЕТНЫМИ!")
    print("Следите за кардинальными изменениями в сцене!")
    print()

    app = QApplication([])

    try:
        # Создаем окно
        window = MainWindow(use_qml_3d=True)
        window.show()
        window.resize(1400, 900)

        print("🎯 ПЛАН ДЕМОНСТРАЦИИ:")
        print("   1. Максимальный туман (почти белая мгла)")
        print("   2. Кардинальные изменения цвета тумана")
        print("   3. Экстремальные режимы сглаживания")
        print("   4. Финальная конфигурация для максимального эффекта")
        print()

        # Планируем экстремальную демонстрацию
        demo_schedule = [
            (2000, lambda: extreme_fog_demo(window)),
            (6000, lambda: extreme_fog_colors(window)),
            (10000, lambda: extreme_antialiasing_demo(window)),
            (15000, lambda: extreme_combined_effects(window)),
            (20000, lambda: create_optimal_scene_for_effects(window)),
            (25000, lambda: final_extreme_check(window)),
            (30000, app.quit),
        ]

        for delay, action in demo_schedule:
            QTimer.singleShot(delay, action)

        app.exec()

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback

        traceback.print_exc()
    finally:
        app.quit()


def extreme_fog_demo(window):
    """Экстремальная демонстрация тумана"""
    print("\n🌫️ ЭКСТРЕМАЛЬНЫЙ ТУМАН")
    print("-" * 50)

    graphics_panel = window._graphics_panel

    if not graphics_panel:
        print("❌ GraphicsPanel недоступна")
        return

    print("📢 ВКЛЮЧАЕМ МАКСИМАЛЬНЫЙ ТУМАН (density=0.8)...")
    print("   Сцена должна стать почти полностью белой!")

    # Максимальные настройки тумана
    graphics_panel.current_graphics.update(
        {
            "fog_enabled": True,
            "fog_density": 0.8,  # Максимальная плотность
            "fog_color": "#ffffff",  # Белый туман
            "background_color": "#000000",  # Черный фон для контраста
        }
    )

    # Обновляем UI
    graphics_panel.fog_enabled.setChecked(True)
    graphics_panel.fog_density.setValue(0.8)
    graphics_panel.fog_color.set_color("#ffffff")
    graphics_panel.background_color.set_color("#000000")

    graphics_panel.emit_environment_update()

    QTimer.singleShot(3000, lambda: print("📢 Если сцена стала белой - туман работает!"))


def extreme_fog_colors(window):
    """Экстремальные цвета тумана"""
    print("\n🌈 КАРДИНАЛЬНЫЕ ИЗМЕНЕНИЯ ЦВЕТА ТУМАНА")
    print("-" * 50)

    graphics_panel = window._graphics_panel

    if not graphics_panel:
        return

    colors = [
        ("#ff0000", "КРАСНЫЙ"),
        ("#00ff00", "ЗЕЛЕНЫЙ"),
        ("#0000ff", "СИНИЙ"),
        ("#ff00ff", "ФИОЛЕТОВЫЙ"),
    ]

    for i, (color, name) in enumerate(colors):
        QTimer.singleShot(
            i * 1000,
            lambda c=color, n=name: change_fog_color_extreme(graphics_panel, c, n),
        )


def change_fog_color_extreme(graphics_panel, color, name):
    """Меняет цвет тумана на экстремальный"""
    print(f"📢 ТУМАН ТЕПЕРЬ {name} ({color})!")

    graphics_panel.current_graphics["fog_color"] = color
    graphics_panel.fog_color.set_color(color)
    graphics_panel.emit_environment_update()


def extreme_antialiasing_demo(window):
    """Экстремальная демонстрация сглаживания"""
    print("\n⚙️ ЭКСТРЕМАЛЬНОЕ СГЛАЖИВАНИЕ")
    print("-" * 50)

    graphics_panel = window._graphics_panel

    if not graphics_panel:
        return

    # Сначала полностью отключаем сглаживание
    print("📢 ПОЛНОСТЬЮ ОТКЛЮЧАЕМ СГЛАЖИВАНИЕ!")
    print("   Все края должны стать зубчатыми!")

    graphics_panel.current_graphics.update(
        {"antialiasing": 0, "aa_quality": 0}  # No AA  # Lowest quality
    )

    graphics_panel.antialiasing.setCurrentIndex(0)
    graphics_panel.aa_quality.setCurrentIndex(0)
    graphics_panel.emit_quality_update()

    # Через 3 секунды включаем максимальное сглаживание
    QTimer.singleShot(3000, lambda: enable_max_antialiasing(graphics_panel))


def enable_max_antialiasing(graphics_panel):
    """Включает максимальное сглаживание"""
    print("📢 ВКЛЮЧАЕМ МАКСИМАЛЬНОЕ СГЛАЖИВАНИЕ!")
    print("   Все края должны стать гладкими!")

    graphics_panel.current_graphics.update(
        {"antialiasing": 2, "aa_quality": 2}  # MSAA  # Highest quality
    )

    graphics_panel.antialiasing.setCurrentIndex(2)
    graphics_panel.aa_quality.setCurrentIndex(2)
    graphics_panel.emit_quality_update()


def extreme_combined_effects(window):
    """Экстремальные комбинированные эффекты"""
    print("\n🎭 ЭКСТРЕМАЛЬНАЯ КОМБИНАЦИЯ ВСЕХ ЭФФЕКТОВ")
    print("-" * 50)

    graphics_panel = window._graphics_panel

    if not graphics_panel:
        return

    print("📢 ВКЛЮЧАЕМ ВСЕ ЭФФЕКТЫ НА МАКСИМУМ!")

    # Экстремальная конфигурация
    graphics_panel.current_graphics.update(
        {
            # Экстремальный туман
            "fog_enabled": True,
            "fog_density": 0.6,
            "fog_color": "#ffaa00",  # Оранжевый туман
            # Максимальное сглаживание
            "antialiasing": 2,
            "aa_quality": 2,
            # Максимальные тени
            "shadows_enabled": True,
            "shadow_quality": 2,
            "shadow_softness": 2.0,
            # Контрастный фон
            "background_color": "#001122",
            # IBL на максимум
            "ibl_enabled": True,
            "ibl_intensity": 3.0,
        }
    )

    # Обновляем все UI элементы
    graphics_panel.fog_enabled.setChecked(True)
    graphics_panel.fog_density.setValue(0.6)
    graphics_panel.fog_color.set_color("#ffaa00")
    graphics_panel.antialiasing.setCurrentIndex(2)
    graphics_panel.aa_quality.setCurrentIndex(2)
    graphics_panel.shadows_enabled.setChecked(True)
    graphics_panel.shadow_quality.setCurrentIndex(2)
    graphics_panel.shadow_softness.setValue(2.0)
    graphics_panel.background_color.set_color("#001122")
    graphics_panel.ibl_enabled.setChecked(True)
    graphics_panel.ibl_intensity.setValue(3.0)

    # Отправляем все обновления
    graphics_panel.emit_environment_update()
    graphics_panel.emit_quality_update()
    graphics_panel.emit_effects_update()

    print("📢 Сцена должна кардинально измениться!")


def create_optimal_scene_for_effects(window):
    """Создает оптимальную сцену для демонстрации эффектов"""
    print("\n🎯 ОПТИМАЛЬНАЯ КОНФИГУРАЦИЯ ДЛЯ ЭФФЕКТОВ")
    print("-" * 50)

    graphics_panel = window._graphics_panel
    qml = window._qml_root_object

    if not graphics_panel or not qml:
        return

    print("📢 НАСТРАИВАЕМ ИДЕАЛЬНУЮ СЦЕНУ ДЛЯ ДЕМОНСТРАЦИИ ЭФФЕКТОВ...")

    # Оптимальная конфигурация для видимости эффектов
    optimal_config = {
        # Умеренный, но заметный туман
        "fog_enabled": True,
        "fog_density": 0.15,
        "fog_color": "#aaccff",  # Светло-синий туман
        # Сглаживание для сравнения
        "antialiasing": 2,
        "aa_quality": 2,
        # Тени для глубины
        "shadows_enabled": True,
        "shadow_quality": 2,
        "shadow_softness": 1.0,
        # Темный фон для контраста с туманом
        "background_color": "#1a1a2e",
        # IBL для реалистичного освещения
        "ibl_enabled": True,
        "ibl_intensity": 1.5,
    }

    graphics_panel.current_graphics.update(optimal_config)

    # Обновляем UI
    graphics_panel.fog_enabled.setChecked(True)
    graphics_panel.fog_density.setValue(0.15)
    graphics_panel.fog_color.set_color("#aaccff")
    graphics_panel.antialiasing.setCurrentIndex(2)
    graphics_panel.aa_quality.setCurrentIndex(2)
    graphics_panel.background_color.set_color("#1a1a2e")
    graphics_panel.ibl_intensity.setValue(1.5)

    graphics_panel.emit_environment_update()
    graphics_panel.emit_quality_update()

    print("📢 Теперь сцена оптимизирована для видимости эффектов!")

    # Демонстрируем разницу через 3 секунды
    QTimer.singleShot(3000, lambda: demonstrate_on_off_effects(graphics_panel))


def demonstrate_on_off_effects(graphics_panel):
    """Демонстрирует включение/выключение эффектов"""
    print("\n🔄 ДЕМОНСТРАЦИЯ ВКЛ/ВЫКЛ ЭФФЕКТОВ (для сравнения)")
    print("-" * 50)

    print("📢 ВЫКЛЮЧАЕМ ВСЕ ЭФФЕКТЫ...")

    # Выключаем все эффекты
    graphics_panel.current_graphics.update(
        {
            "fog_enabled": False,
            "antialiasing": 0,
            "shadows_enabled": False,
            "ibl_enabled": False,
        }
    )

    graphics_panel.fog_enabled.setChecked(False)
    graphics_panel.antialiasing.setCurrentIndex(0)
    graphics_panel.shadows_enabled.setChecked(False)
    graphics_panel.ibl_enabled.setChecked(False)

    graphics_panel.emit_environment_update()
    graphics_panel.emit_quality_update()

    print("📢 Сравните с предыдущим состоянием!")

    # Включаем обратно через 3 секунды
    QTimer.singleShot(3000, lambda: reenable_effects(graphics_panel))


def reenable_effects(graphics_panel):
    """Снова включает эффекты"""
    print("📢 СНОВА ВКЛЮЧАЕМ ВСЕ ЭФФЕКТЫ...")

    graphics_panel.current_graphics.update(
        {
            "fog_enabled": True,
            "antialiasing": 2,
            "shadows_enabled": True,
            "ibl_enabled": True,
        }
    )

    graphics_panel.fog_enabled.setChecked(True)
    graphics_panel.antialiasing.setCurrentIndex(2)
    graphics_panel.shadows_enabled.setChecked(True)
    graphics_panel.ibl_enabled.setChecked(True)

    graphics_panel.emit_environment_update()
    graphics_panel.emit_quality_update()

    print("📢 Разница должна быть очевидной!")


def final_extreme_check(window):
    """Финальная проверка экстремальной демонстрации"""
    print("\n🏁 ФИНАЛЬНАЯ ПРОВЕРКА ЭКСТРЕМАЛЬНОЙ ДЕМОНСТРАЦИИ")
    print("-" * 50)

    qml = window._qml_root_object

    if not qml:
        return

    # Проверяем финальные значения
    fog_enabled = qml.property("fogEnabled")
    fog_density = qml.property("fogDensity")
    fog_color = qml.property("fogColor")
    aa_mode = qml.property("antialiasingMode")
    aa_quality = qml.property("antialiasingQuality")

    print("📊 ФИНАЛЬНЫЕ ЗНАЧЕНИЯ ЭФФЕКТОВ:")
    print(f"   Туман: {fog_enabled} (плотность: {fog_density}, цвет: {fog_color})")
    print(f"   Сглаживание: режим {aa_mode} (качество: {aa_quality})")

    print("\n🎯 ИТОГОВЫЕ ВЫВОДЫ:")

    if fog_enabled:
        print("   ✅ Туман включен и должен быть виден")
        if fog_density > 0.1:
            print("   ✅ Плотность тумана достаточна для видимости")
        else:
            print("   ⚠️ Плотность тумана может быть слишком низкой")
    else:
        print("   ❌ Туман выключен")

    if aa_mode > 0:
        print("   ✅ Сглаживание включено")
        if aa_quality > 1:
            print("   ✅ Качество сглаживания высокое")
    else:
        print("   ❌ Сглаживание выключено")

    print("\n🎪 ЗАКЛЮЧЕНИЕ ЭКСТРЕМАЛЬНОЙ ДЕМОНСТРАЦИИ:")
    print("   Если вы видели кардинальные изменения в сцене:")
    print("     ✅ Туман и сглаживание работают правильно!")
    print("   Если изменений не было:")
    print("     ⚠️ Возможно проблема в настройках 3D движка или сцены")


if __name__ == "__main__":
    print("🚀 ЗАПУСК ЭКСТРЕМАЛЬНОЙ ДЕМОНСТРАЦИИ ЭФФЕКТОВ")
    print()
    print("Цель: сделать эффекты максимально заметными")
    print("Метод: экстремальные значения параметров")
    print("Ожидание: кардинальные изменения внешнего вида сцены")
    print()

    extreme_effects_demo()

    print("\n✅ Экстремальная демонстрация завершена!")
    print("\n🎯 ФИНАЛЬНАЯ ОЦЕНКА:")
    print("   Если видели изменения - туман и сглаживание 100% работают")
    print("   Если не видели - проблема в 3D движке или настройках сцены")
