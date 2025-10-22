#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
КРИТИЧЕСКИЙ ФИКС: Убираем z: 1000 из CameraController
Это блокирует рендеринг View3D!
"""
import re
from pathlib import Path


def fix_camera_z_order():
    """Убирает z: 1000, который блокирует рендеринг View3D"""
    qml_file = Path("assets/qml/main.qml")

    if not qml_file.exists():
        print(f"❌ Файл не найден: {qml_file}")
        return False

    print(f"📁 Читаем: {qml_file}")
    content = qml_file.read_text(encoding="utf-8")

    # Ищем и удаляем z: 1000
    pattern = r"(\s*)z:\s*1000\s*//.*поверх.*мыши"

    if not re.search(pattern, content):
        print("⚠️ Строка z: 1000 не найдена (возможно уже исправлено)")
        return True

    # Удаляем строку
    fixed_content = re.sub(pattern, "", content)

    # Проверяем что что-то изменилось
    if content == fixed_content:
        print("⚠️ Контент не изменился")
        return False

    # Сохраняем
    qml_file.write_text(fixed_content, encoding="utf-8")

    print("✅ ИСПРАВЛЕНО:")
    print("   ❌ Удалено: z: 1000  // поверх всего для обработки мыши")
    print("   ✅ CameraController теперь прозрачен для рендеринга")
    print("   ✅ MouseArea всё равно получает события мыши")

    return True


if __name__ == "__main__":
    success = fix_camera_z_order()
    exit(0 if success else 1)
