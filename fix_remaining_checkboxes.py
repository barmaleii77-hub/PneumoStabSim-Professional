#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 ИСПРАВЛЕНИЕ ОСТАВШИХСЯ CHECKBOXES В GRAPHICSPANEL
Исправляем все чекбоксы которые используют clicked() вместо toggled()
"""

import re
from pathlib import Path


def fix_all_checkboxes():
    """Исправляет ВСЕ чекбоксы на использование toggled() вместо clicked()"""
    panel_file = Path("src/ui/panels/panel_graphics.py")
    content = panel_file.read_text(encoding="utf-8")

    print("🔧 МАССОВОЕ ИСПРАВЛЕНИЕ CHECKBOXES:")
    print("=" * 70)

    # Список паттернов для замены: checkbox_var.clicked.connect -> checkbox_var.toggled.connect
    replacements = [
        # Shadows
        (
            r'(shadows_enabled|enabled)\.clicked\.connect\(lambda checked: self\._update_quality\("shadows\.enabled", checked\)\)',
            r'\1.toggled.connect(lambda checked: self._update_quality("shadows.enabled", checked))',
        ),
        # TAA
        (
            r'taa_check\.clicked\.connect\(lambda checked: self\._update_quality\("taa\.enabled", checked\)\)',
            r'taa_check.toggled.connect(lambda checked: self._update_quality("taa.enabled", checked))',
        ),
        # FXAA
        (
            r'fxaa_check\.clicked\.connect\(lambda checked: self\._update_quality\("fxaa\.enabled", checked\)\)',
            r'fxaa_check.toggled.connect(lambda checked: self._update_quality("fxaa.enabled", checked))',
        ),
        # Specular AA
        (
            r'specular_check\.clicked\.connect\(lambda checked: self\._update_quality\("specular_aa", checked\)\)',
            r'specular_check.toggled.connect(lambda checked: self._update_quality("specular_aa", checked))',
        ),
        # Dithering
        (
            r'dithering_check\.clicked\.connect\(lambda checked: self\._update_quality\("dithering", checked\)\)',
            r'dithering_check.toggled.connect(lambda checked: self._update_quality("dithering", checked))',
        ),
        # OIT
        (
            r'oit_check\.clicked\.connect\(lambda checked: self\._update_quality\("oit", "weighted" if checked else "none"\)\)',
            r'oit_check.toggled.connect(lambda checked: self._update_quality("oit", "weighted" if checked else "none"))',
        ),
        # Auto rotate - уже исправлен в camera_tab с отдельным обработчиком
        # Не трогаем, чтобы не сломать логирование
        # SSAO
        (
            r'enabled\.clicked\.connect\(lambda checked: self\._update_environment\("ao_enabled", checked\)\)',
            r'enabled.toggled.connect(lambda checked: self._update_environment("ao_enabled", checked))',
        ),
        # DoF
        (
            r'enabled\.clicked\.connect\(lambda checked: self\._update_effects\("depth_of_field", checked\)\)',
            r'enabled.toggled.connect(lambda checked: self._update_effects("depth_of_field", checked))',
        ),
        # Motion blur
        (
            r'motion\.clicked\.connect\(lambda checked: self\._update_effects\("motion_blur", checked\)\)',
            r'motion.toggled.connect(lambda checked: self._update_effects("motion_blur", checked))',
        ),
        # Lens flare
        (
            r'lens_flare\.clicked\.connect\(lambda checked: self\._update_effects\("lens_flare", checked\)\)',
            r'lens_flare.toggled.connect(lambda checked: self._update_effects("lens_flare", checked))',
        ),
        # Vignette
        (
            r'vignette\.clicked\.connect\(lambda checked: self\._update_effects\("vignette", checked\)\)',
            r'vignette.toggled.connect(lambda checked: self._update_effects("vignette", checked))',
        ),
        # Tonemap
        (
            r'enabled\.clicked\.connect\(lambda checked: self\._update_effects\("tonemap_enabled", checked\)\)',
            r'enabled.toggled.connect(lambda checked: self._update_effects("tonemap_enabled", checked))',
        ),
        # Lighting shadows (key, fill, rim, point)
        (
            r'(key|fill|rim|point)_shadow\.clicked\.connect\(lambda checked: self\._update_lighting\("(key|fill|rim|point)", "cast_shadow", checked\)\)',
            r'\1_shadow.toggled.connect(lambda checked: self._update_lighting("\2", "cast_shadow", checked))',
        ),
        (
            r'(key|fill|rim|point)_bind\.clicked\.connect\(lambda checked: self\._update_lighting\("(key|fill|rim|point)", "bind_to_camera", checked\)\)',
            r'\1_bind.toggled.connect(lambda checked: self._update_lighting("\2", "bind_to_camera", checked))',
        ),
        # TAA motion adaptive
        (
            r'taa_motion\.clicked\.connect\(lambda checked: self\._update_quality\("taa_motion_adaptive", checked\)\)',
            r'taa_motion.toggled.connect(lambda checked: self._update_quality("taa_motion_adaptive", checked))',
        ),
    ]

    changes_count = 0
    for old_pattern, new_pattern in replacements:
        if re.search(old_pattern, content):
            content = re.sub(old_pattern, new_pattern, content)
            changes_count += 1
            print(f"✅ Исправлено: {old_pattern[:50]}...")

    if changes_count == 0:
        print("⚠️ Изменений не найдено - возможно уже исправлено")
        return False

    # Сохраняем исправленный файл
    panel_file.write_text(content, encoding="utf-8")
    print(f"\n💾 Сохранено {changes_count} исправлений в {panel_file}")

    return True


def verify_checkboxes():
    """Проверяет что все чекбоксы используют toggled()"""
    panel_file = Path("src/ui/panels/panel_graphics.py")
    content = panel_file.read_text(encoding="utf-8")

    print("\n🔍 ФИНАЛЬНАЯ ПРОВЕРКА ВСЕХ CHECKBOXES:")
    print("=" * 70)

    # Ищем все .clicked.connect для чекбоксов
    clicked_pattern = r"(\w+)\.clicked\.connect"
    clicked_matches = re.findall(clicked_pattern, content)

    # Фильтруем только чекбоксы (исключаем кнопки)
    checkbox_vars = []
    for var in clicked_matches:
        # Проверяем что переменная - это чекбокс (содержит check, enabled, или создана как QCheckBox)
        if any(
            keyword in var.lower()
            for keyword in ["check", "enabled", "toggle", "shadow", "bind"]
        ):
            # Проверяем что это не auto_rotate (у него специальный обработчик)
            if var != "auto_rotate":
                checkbox_vars.append(var)

    if checkbox_vars:
        print("⚠️ Найдены чекбоксы с .clicked.connect:")
        for var in set(checkbox_vars):
            print(f"   • {var}")
        print(f"\nВсего: {len(set(checkbox_vars))} проблемных чекбоксов")
        return False
    else:
        print("✅ Все чекбоксы используют .toggled.connect")
        print(
            "✅ Исключение: auto_rotate (имеет специальный обработчик с логированием)"
        )
        return True


def main():
    """Основная функция"""
    print("🚀 ИСПРАВЛЕНИЕ ОСТАВШИХСЯ CHECKBOXES")
    print("=" * 70)

    panel_file = Path("src/ui/panels/panel_graphics.py")

    if not panel_file.exists():
        print(f"❌ Файл не найден: {panel_file}")
        return False

    # Применяем исправления
    fixed = fix_all_checkboxes()

    # Проверяем результат
    all_ok = verify_checkboxes()

    print("\n" + "=" * 70)
    if all_ok:
        print("✅ ВСЕ CHECKBOXES ИСПРАВЛЕНЫ!")
    else:
        print("⚠️ НЕКОТОРЫЕ CHECKBOXES ЕЩЕ ТРЕБУЮТ ВНИМАНИЯ")
    print("=" * 70)

    print("\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
    print("  1. Запустите: py app.py")
    print("  2. Проверьте работу ВСЕХ чекбоксов")
    print("  3. Убедитесь что они включаются И ВЫКЛЮЧАЮТСЯ корректно")

    return all_ok


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
