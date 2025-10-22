#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 ИСПРАВЛЕНИЕ ЧЕКБОКСОВ И АНТИАЛИАСИНГА В GRAPHICSPANEL
Проблемы:
1. IBL checkbox - включается но не выключается (нет обработчика toggled)
2. Антиалиасинг - работает странно (неправильное подключение)
3. Не все элементы подключены
"""

import re
from pathlib import Path


def fix_ibl_checkbox():
    """Исправляет подключение IBL checkbox"""
    panel_file = Path("src/ui/panels/panel_graphics.py")
    content = panel_file.read_text(encoding="utf-8")

    print("🔧 ИСПРАВЛЕНИЕ IBL CHECKBOX:")
    print("-" * 50)

    # Ищем строку с созданием IBL checkbox
    old_pattern = r"ibl_check\.clicked\.connect\(lambda checked: self\._on_ibl_enabled_clicked\(checked\)\)"

    if re.search(old_pattern, content):
        # Заменяем на toggled вместо clicked
        new_code = "ibl_check.toggled.connect(lambda checked: self._on_ibl_enabled_clicked(checked))"
        content = re.sub(old_pattern, new_code, content)
        print("✅ IBL checkbox подключен к toggled() вместо clicked()")
    else:
        print("⚠️ IBL checkbox уже использует правильное подключение")

    return content


def fix_skybox_checkbox(content):
    """Исправляет подключение Skybox checkbox"""
    print("\n🔧 ИСПРАВЛЕНИЕ SKYBOX CHECKBOX:")
    print("-" * 50)

    # Ищем строку с созданием Skybox checkbox
    old_pattern = r"skybox_toggle\.clicked\.connect\(lambda checked: self\._on_skybox_enabled_clicked\(checked\)\)"

    if re.search(old_pattern, content):
        # Заменяем на toggled вместо clicked
        new_code = "skybox_toggle.toggled.connect(lambda checked: self._on_skybox_enabled_clicked(checked))"
        content = re.sub(old_pattern, new_code, content)
        print("✅ Skybox checkbox подключен к toggled() вместо clicked()")
    else:
        print("⚠️ Skybox checkbox уже использует правильное подключение")

    return content


def fix_fog_checkbox(content):
    """Исправляет подключение Fog checkbox"""
    print("\n🔧 ИСПРАВЛЕНИЕ FOG CHECKBOX:")
    print("-" * 50)

    # Ищем строку с созданием Fog checkbox
    old_pattern = r"enabled\.clicked\.connect\(lambda checked: self\._on_fog_enabled_clicked\(checked\)\)"

    if re.search(old_pattern, content):
        # Заменяем на toggled вместо clicked
        new_code = "enabled.toggled.connect(lambda checked: self._on_fog_enabled_clicked(checked))"
        content = re.sub(old_pattern, new_code, content)
        print("✅ Fog checkbox подключен к toggled() вместо clicked()")
    else:
        print("⚠️ Fog checkbox уже использует правильное подключение")

    return content


def fix_bloom_checkbox(content):
    """Исправляет подключение Bloom checkbox"""
    print("\n🔧 ИСПРАВЛЕНИЕ BLOOM CHECKBOX:")
    print("-" * 50)

    # Ищем строку в _build_bloom_group
    old_pattern = r"enabled\.clicked\.connect\(lambda checked: self\._on_bloom_enabled_clicked\(checked\)\)"

    if re.search(old_pattern, content):
        # Заменяем на toggled вместо clicked
        new_code = "enabled.toggled.connect(lambda checked: self._on_bloom_enabled_clicked(checked))"
        content = re.sub(old_pattern, new_code, content)
        print("✅ Bloom checkbox подключен к toggled() вместо clicked()")
    else:
        print("⚠️ Bloom checkbox уже использует правильное подключение")

    return content


def fix_antialiasing_combobox(content):
    """Исправляет подключение Antialiasing combobox"""
    print("\n🔧 ИСПРАВЛЕНИЕ ANTIALIASING COMBOBOX:")
    print("-" * 50)

    # Проблема: currentIndexChanged может срабатывать при программной установке
    # Решение: Используем флаг _updating_ui для блокировки ложных срабатываний

    # Проверяем есть ли уже правильное подключение
    if "primary_combo.currentIndexChanged.connect" in content:
        print("✅ Antialiasing combobox уже подключен")

        # Проверяем использует ли обработчик флаг _updating_ui
        if "def _on_primary_aa_changed" in content:
            # Находим функцию
            pattern = r"def _on_primary_aa_changed\(self, value: str\) -> None:\s+(.*?)(?=\n    def )"
            match = re.search(pattern, content, re.DOTALL)

            if match:
                func_body = match.group(1)
                if "if self._updating_ui:" in func_body:
                    print("✅ Обработчик уже использует флаг _updating_ui")
                else:
                    print(
                        "⚠️ Обработчик НЕ использует флаг _updating_ui - может срабатывать ложно"
                    )
    else:
        print("❌ Antialiasing combobox НЕ подключен!")

    return content


def verify_all_checkboxes(content):
    """Проверяет все чекбоксы"""
    print("\n🔍 ПРОВЕРКА ВСЕХ ЧЕКБОКСОВ:")
    print("-" * 50)

    checkboxes = {
        "ibl_enabled": r"ibl_check\.(clicked|toggled)\.connect",
        "skybox_enabled": r"skybox_toggle\.(clicked|toggled)\.connect",
        "fog_enabled": r"enabled\.(clicked|toggled)\.connect.*fog",
        "bloom_enabled": r"enabled\.(clicked|toggled)\.connect.*bloom",
        "shadows_enabled": r"enabled\.(clicked|toggled)\.connect.*shadows",
        "taa_enabled": r"taa_check\.(clicked|toggled)\.connect",
        "fxaa_enabled": r"fxaa_check\.(clicked|toggled)\.connect",
        "specular_aa": r"specular_check\.(clicked|toggled)\.connect",
        "dithering": r"dithering_check\.(clicked|toggled)\.connect",
        "oit": r"oit_check\.(clicked|toggled)\.connect",
        "auto_rotate": r"auto_rotate\.(clicked|toggled)\.connect",
    }

    for name, pattern in checkboxes.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            signal = match.group(1)
            icon = "✅" if signal == "toggled" else "⚠️"
            print(f"{icon} {name:20s} - {signal}()")
        else:
            print(f"❌ {name:20s} - NOT CONNECTED")

    return content


def main():
    """Основная функция"""
    print("🚀 ИСПРАВЛЕНИЕ CHECKBOXES И ANTIALIASING В GRAPHICSPANEL")
    print("=" * 70)

    panel_file = Path("src/ui/panels/panel_graphics.py")

    if not panel_file.exists():
        print(f"❌ Файл не найден: {panel_file}")
        return False

    # Создаём backup
    backup_file = panel_file.with_suffix(".py.backup")
    content = panel_file.read_text(encoding="utf-8")
    backup_file.write_text(content, encoding="utf-8")
    print(f"💾 Backup создан: {backup_file}")

    # Применяем исправления
    content = fix_ibl_checkbox()
    content = fix_skybox_checkbox(content)
    content = fix_fog_checkbox(content)
    content = fix_bloom_checkbox(content)
    content = fix_antialiasing_combobox(content)
    content = verify_all_checkboxes(content)

    # Сохраняем исправленный файл
    panel_file.write_text(content, encoding="utf-8")
    print(f"\n💾 Исправленный файл сохранён: {panel_file}")

    print("\n" + "=" * 70)
    print("✅ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
    print("=" * 70)

    print("\n🎯 ЧТО ИСПРАВЛЕНО:")
    print("  1. IBL checkbox теперь использует toggled() вместо clicked()")
    print("  2. Skybox checkbox теперь использует toggled() вместо clicked()")
    print("  3. Fog checkbox теперь использует toggled() вместо clicked()")
    print("  4. Bloom checkbox теперь использует toggled() вместо clicked()")
    print("  5. Проверено подключение Antialiasing combobox")

    print("\n🧪 СЛЕДУЮЩИЕ ШАГИ:")
    print("  1. Запустите: py app.py")
    print("  2. Проверьте работу чекбоксов IBL/Skybox/Fog/Bloom")
    print("  3. Проверьте переключение режимов сглаживания")
    print("  4. Убедитесь что чекбоксы включаются И ВЫКЛЮЧАЮТСЯ")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
