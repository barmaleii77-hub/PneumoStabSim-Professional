#!/usr/bin/env python
"""Быстрый тест запуска приложения в headless-окружении."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from collections.abc import Callable


def _configure_qt_environment() -> None:
    """Настраивает переменные окружения для стабильного headless-запуска."""

    platform = os.environ.get("QT_QPA_PLATFORM", "").lower()
    is_headless = platform == "offscreen" or (
        not platform and not os.environ.get("DISPLAY")
    )

    if is_headless:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        os.environ.setdefault("QT_OPENGL", "software")
        os.environ.setdefault("QT_QUICK_BACKEND", "software")
        os.environ.setdefault("QSG_RHI_BACKEND", "software")
    else:
        os.environ.setdefault("QSG_RHI_BACKEND", "opengl")

    os.environ.setdefault("QSG_INFO", "1")
    os.environ.setdefault("QT_LOGGING_RULES", "js.debug=true;qt.qml.debug=true")


def _run_make_verify() -> None:
    if shutil.which("make"):
        print("🚦 Дополнительная проверка: make verify (smoke + integration)")
        verify_result = subprocess.run(["make", "verify"], check=False)
        print(f"ℹ️ make verify завершен с кодом: {verify_result.returncode}")
    else:
        print(
            "ℹ️ make не найден. Запустите вручную: python -m pytest -m 'smoke or integration'"
        )


def _validate_graphics_settings(settings_path: Path) -> None:
    from src.ui.environment_schema import (
        EnvironmentValidationError,
        validate_animation_settings,
        validate_environment_settings,
        validate_scene_settings,
    )

    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    graphics = payload.get("current", {}).get("graphics")
    if not isinstance(graphics, dict):
        raise EnvironmentValidationError("Отсутствует секция current.graphics")

    validators: dict[str, Callable[[dict], dict]] = {
        "environment": validate_environment_settings,
        "scene": validate_scene_settings,
        "animation": validate_animation_settings,
    }

    for key, validator in validators.items():
        section = graphics.get(key)
        if section is None:
            raise EnvironmentValidationError(f"Отсутствует секция graphics.{key}")
        validator(section)

    print("✅ Графические настройки соответствуют требованиям schema")


def _run_headless_validations() -> int:
    from tools import validate_settings

    settings_path = Path("config/app_settings.json")
    print("🛡️ Запускаем headless-проверку настроек")

    result = validate_settings.main(["--quiet"])
    if result != 0:
        print("❌ Ошибка валидации config/app_settings.json против schema")
        return result

    try:
        _validate_graphics_settings(settings_path)
    except Exception as exc:  # pragma: no cover - диагностические сообщения
        print(f"❌ Ошибка валидации графических настроек: {exc}")
        return 1

    qml_file = Path("assets/qml/main.qml")
    if not qml_file.exists():
        print(f"❌ QML файл не найден: {qml_file}")
        return 1

    linter = os.environ.get("QML_LINTER") or shutil.which("qmllint")
    if not linter:
        linter = shutil.which("pyside6-qmllint")

    if linter:
        print(f"🔍 Запускаем {linter} для статической проверки main.qml")
        lint_result = subprocess.run([linter, str(qml_file)], check=False)
        if lint_result.returncode != 0:
            print(f"❌ {linter} обнаружил проблемы с main.qml")
            return lint_result.returncode
        print("✅ main.qml успешно прошёл qmllint")
    else:
        print("ℹ️ qmllint недоступен, пропускаем статическую проверку QML")

    return 0


def _run_gui_smoke() -> int:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from src.ui.main_window import MainWindow

    print("🧪 Быстрый тест запуска приложения...")
    app = QApplication(sys.argv)
    print("✅ QApplication создан")

    window = MainWindow(use_qml_3d=True)
    print("✅ MainWindow создан")

    window.show()
    print("✅ MainWindow показан")

    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(app.quit)
    timer.start(3000)

    print("🔄 Запуск на 3 секунды...")
    result = app.exec()
    print(f"✅ Приложение завершено с кодом: {result}")

    _run_make_verify()
    return 0


def main() -> int:
    _configure_qt_environment()

    try:
        return _run_gui_smoke()
    except ImportError as exc:
        print(f"⚠️ PySide6 недоступен или отсутствуют системные зависимости: {exc}")
        return _run_headless_validations()
    except Exception as exc:
        print(f"❌ Ошибка при запуске GUI: {exc}")
        fallback_result = _run_headless_validations()
        return 1 if fallback_result == 0 else fallback_result


if __name__ == "__main__":
    sys.exit(main())
