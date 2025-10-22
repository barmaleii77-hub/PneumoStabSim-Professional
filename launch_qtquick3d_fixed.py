#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПОСТОЯННЫЙ ЛАУНЧЕР PneumoStabSim с исправлением QtQuick3D
Этот файл ГАРАНТИРУЕТ правильную работу QtQuick3D при каждом запуске
"""
import os
import sys
from pathlib import Path


def setup_qt_for_qtquick3d():
    """Настройка Qt для гарантированной работы QtQuick3D"""
    try:
        import PySide6

        pyside6_path = Path(PySide6.__file__).parent

        # КРИТИЧЕСКИЕ переменные для QtQuick3D
        critical_vars = {
            "QT_PLUGIN_PATH": str(pyside6_path / "plugins"),
            "QML_IMPORT_PATH": str(pyside6_path / "qml"),
            "QML2_IMPORT_PATH": str(pyside6_path / "qml"),
            "QTDIR": str(pyside6_path),
            "QSG_RHI_BACKEND": "d3d11" if sys.platform == "win32" else "opengl",
            "QT_QUICK3D_MODULE_PATH": str(pyside6_path / "qml" / "QtQuick3D"),
            "PYTHONIOENCODING": "utf-8",
        }

        for var, value in critical_vars.items():
            os.environ[var] = value

        print("✅ Qt окружение настроено для QtQuick3D")
        return True
    except Exception as e:
        print(f"❌ Ошибка настройки Qt: {e}")
        return False


if __name__ == "__main__":
    print("🚀 PneumoStabSim - ПОСТОЯННЫЙ ЛАУНЧЕР с исправлением QtQuick3D")
    print("=" * 70)

    # КРИТИЧНО: Настраиваем окружение ПЕРЕД любым импортом
    if not setup_qt_for_qtquick3d():
        print("❌ Не удалось настроить Qt окружение!")
        input("Нажмите Enter для закрытия...")
        sys.exit(1)

    # Теперь запускаем основное приложение
    try:
        # Добавляем текущую директорию в Python path
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))

        # Импортируем и запускаем приложение
        import app

        # Корректируем sys.argv для app.py
        if len(sys.argv) > 0:
            sys.argv[0] = "app.py"

        print("🎬 Запуск основного приложения...")
        result = app.main()

        print(f"✅ Приложение завершено с кодом: {result}")
        sys.exit(result)

    except Exception as e:
        print(f"💀 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()
        input("Нажмите Enter для закрытия...")
        sys.exit(1)
