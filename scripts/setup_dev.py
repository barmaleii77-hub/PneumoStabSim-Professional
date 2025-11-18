#!/usr/bin/env python3
"""
Автоматическая настройка среды разработки PneumoStabSim
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Dict, Iterable, Tuple


def merge_paths(current: str, new_entries: Iterable[str], separator: str) -> str:
    values = []
    if current:
        values.extend(segment for segment in current.split(separator) if segment)

    for entry in new_entries:
        if entry and entry not in values:
            values.append(entry)

    return separator.join(values)


def detect_qt_paths(python_executable: Path) -> Tuple[str | None, str | None]:
    """Resolve Qt plugin and QML import paths using the specified interpreter."""

    script = """
from __future__ import annotations

import sys

try:
    from PySide6 import QtCore  # type: ignore
except Exception:
    sys.exit(1)

library_path = getattr(
    QtCore.QLibraryInfo.LibraryPath, "QmlImportsPath", QtCore.QLibraryInfo.LibraryPath.Qml2ImportsPath
)
print(QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.PluginsPath))
print(QtCore.QLibraryInfo.path(library_path))
"""

    try:
        result = subprocess.run(
            [str(python_executable), "-c", script], capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError:
        return None, None

    lines = result.stdout.strip().splitlines()
    if len(lines) < 2:
        return None, None

    return lines[0].strip() or None, lines[1].strip() or None


def update_env_paths(env_path: Path, updates: Dict[str, str], separator: str) -> None:
    """Update or append environment variables in .env without dropping comments."""

    env_path.parent.mkdir(parents=True, exist_ok=True)
    original_lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    processed_keys = set()
    output_lines = []

    for line in original_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            output_lines.append(line)
            continue

        key, _, value = stripped.partition("=")
        if key in updates:
            merged_value = merge_paths(value, [updates[key]], separator)
            output_lines.append(f"{key}={merged_value}")
            processed_keys.add(key)
        else:
            output_lines.append(line)

    for key, value in updates.items():
        if key in processed_keys:
            continue
        output_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")


def run_command(cmd, description=""):
    """Выполняет команду с обработкой ошибок"""
    if description:
        print(f"➤ {description}...")

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )
        print("✅ Успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e}")
        if e.stdout:
            print(f"Вывод: {e.stdout}")
        if e.stderr:
            print(f"Ошибка: {e.stderr}")
        return False


def announce_platform_context() -> None:
    """Отображает сведения о платформе и рекомендуемом сценарии использования."""

    system = platform.system()
    print("=== ИНФОРМАЦИЯ О ПЛАТФОРМЕ ===")
    print(f"Обнаружена платформа: {system}")

    if system == "Windows":
        print(
            "Режим: Visual Studio / VS Code Copilot. Все действия выполняются "
            "на рабочей станции Windows."
        )
        print(
            "Перед запуском задач убедитесь, что зависимости обновлены через "
            "этот скрипт и `pip`."
        )
    else:
        print(
            "Режим: Codex или контейнерная среда (Linux). Используйте `uv sync` "
            "и Makefile для установки зависимостей и запуска тестов."
        )
        print(
            "Если необходимо повторить шаги Windows, запустите их в отдельной "
            "рабочей среде."
        )


def check_prerequisites():
    """Проверяет необходимые компоненты"""
    print("=== ПРОВЕРКА ПРЕДУСТАНОВОК ===")

    # Проверяем Python версию
    version = sys.version_info
    print(f"Python версия: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 13):
        print("❌ Требуется Python 3.13+")
        return False

    # Проверяем pip
    if not run_command("pip --version", "Проверка pip"):
        return False

    # Проверяем git
    if not run_command("git --version", "Проверка git"):
        return False

    return True


def create_virtual_environment():
    """Создает виртуальное окружение"""
    print("\n=== СОЗДАНИЕ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ ===")

    venv_path = Path(".venv")

    if venv_path.exists():
        print("⚠️ Виртуальное окружение уже существует")
        return True

    if not run_command("python -m venv .venv", "Создание .venv"):
        return False

    return True


def activate_and_install():
    """Активирует окружение и устанавливает зависимости"""
    print("\n=== УСТАНОВКА ЗАВИСИМОСТЕЙ ===")

    # Команды активации в зависимости от ОС
    system = platform.system()

    if system == "Windows":
        activate_cmd = r".venv\Scripts\activate.bat &&"
    else:
        activate_cmd = "source .venv/bin/activate &&"

    # Обновляем pip
    if not run_command(f"{activate_cmd} pip install --upgrade pip", "Обновление pip"):
        return False

    requirements_dev = Path("requirements-dev.txt")
    requirements_base = Path("requirements.txt")

    if requirements_dev.exists():
        if not run_command(
            f"{activate_cmd} pip install -r {requirements_dev}",
            "Установка зависимостей для полного тестирования",
        ):
            return False
    elif requirements_base.exists():
        if not run_command(
            f"{activate_cmd} pip install -r {requirements_base}",
            "Установка основных зависимостей",
        ):
            return False

        fallback_dev_packages = [
            "pytest>=8.0.0",
            "pytest-qt>=4.5.0",
            "pytest-cov>=4.1.0",
            "black>=24.0.0",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
            "ruff>=0.14.0",
            "bandit>=1.7.0",
            "coverage[toml]>=7.6.0",
            "pre-commit>=3.7.0",
        ]

        dev_cmd = f"{activate_cmd} pip install " + " ".join(fallback_dev_packages)
        if not run_command(dev_cmd, "Установка дополнительных dev-зависимостей"):
            return False
    else:
        print("❌ Не найдены файлы requirements.txt или requirements-dev.txt")
        return False

    return True


def configure_qt_environment():
    """Detect Qt plugin/QML paths and persist them into .env for Windows sessions."""

    env_path = Path(".env")
    separator = os.pathsep
    venv_python = Path(".venv") / ("Scripts" if platform.system() == "Windows" else "bin") / (
        "python.exe" if platform.system() == "Windows" else "python"
    )

    interpreter = venv_python if venv_python.exists() else Path(sys.executable)
    plugin_path, qml_path = detect_qt_paths(interpreter)

    if not plugin_path and not qml_path:
        print("⚠️ PySide6 not available; skipping Qt path export")
        return True

    updates: Dict[str, str] = {}
    if plugin_path:
        updates["QT_PLUGIN_PATH"] = plugin_path
    if qml_path:
        updates["QML2_IMPORT_PATH"] = merge_paths("", [qml_path], separator)
        updates["QML_IMPORT_PATH"] = qml_path
        updates["QT_QML_IMPORT_PATH"] = qml_path

    try:
        update_env_paths(env_path, updates, separator)
        if "QT_QUICK_CONTROLS_STYLE" not in env_path.read_text(encoding="utf-8"):
            with env_path.open("a", encoding="utf-8") as handle:
                handle.write(f"QT_QUICK_CONTROLS_STYLE=Basic\n")
        print("✅ Qt environment variables persisted to .env")
        return True
    except Exception as exc:  # pragma: no cover - defensive logging for setup utility
        print(f"❌ Не удалось обновить .env: {exc}")
        return False


def setup_git_hooks():
    """Настраивает Git hooks"""
    print("\n=== НАСТРОЙКА GIT HOOKS ===")

    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        print("⚠️ .git/hooks не найден, пропускаем настройку хуков")
        return True

    # Создаем pre-commit hook для форматирования кода
    pre_commit_hook = hooks_dir / "pre-commit"
    hook_content = """#!/bin/bash
# Автоматическое форматирование кода перед коммитом

echo "Запуск проверки кода..."

# Форматирование с Black
black src/ tests/ scripts/ --check --diff
if [ $? -ne 0 ]; then
    echo "Код не отформатирован. Запустите: black src/ tests/ scripts/"
    exit 1
fi

# Проверка с flake8
flake8 src/ tests/ scripts/
if [ $? -ne 0 ]; then
    echo "Найдены проблемы с качеством кода"
    exit 1
fi

echo "Проверка кода прошла успешно!"
"""

    try:
        pre_commit_hook.write_text(hook_content)
        pre_commit_hook.chmod(0o755)  # Делаем исполняемым
        print("✅ Git pre-commit hook установлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания git hook: {e}")
        return False


def setup_ide_config():
    """Создает конфигурационные файлы для IDE"""
    print("\n=== НАСТРОЙКА IDE ===")

    # VS Code settings
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)

    # settings.json для VS Code
    vscode_settings = {
        "python.defaultInterpreterPath": (
            "./.venv/Scripts/python.exe"
            if platform.system() == "Windows"
            else "./.venv/bin/python"
        ),
        "python.formatting.provider": "black",
        "python.linting.enabled": True,
        "python.linting.flake8Enabled": True,
        "python.testing.pytestEnabled": True,
        "python.testing.pytestArgs": ["tests/"],
        "files.associations": {"*.qml": "qml"},
        "editor.formatOnSave": True,
        "editor.codeActionsOnSave": {"source.organizeImports": True},
    }

    try:
        import json

        (vscode_dir / "settings.json").write_text(json.dumps(vscode_settings, indent=2))
        print("✅ Конфигурация VS Code создана")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания конфигурации VS Code: {e}")
        return False


def final_check():
    """Финальная проверка настройки"""
    print("\n=== ФИНАЛЬНАЯ ПРОВЕРКА ===")

    # Запускаем health_check
    if Path("scripts/health_check.py").exists():
        system = platform.system()
        if system == "Windows":
            cmd = r".venv\Scripts\python.exe scripts\health_check.py"
        else:
            cmd = ".venv/bin/python scripts/health_check.py"

        return run_command(cmd, "Проверка состояния проекта")
    else:
        print("⚠️ scripts/health_check.py не найден")
        return True


def main():
    """Основная функция настройки"""
    print("🚀 АВТОМАТИЧЕСКАЯ НАСТРОЙКА СРЕДЫ РАЗРАБОТКИ PNEUMOSTABSIM 🚀\n")

    announce_platform_context()

    steps = [
        ("Проверка предустановок", check_prerequisites),
        ("Создание виртуального окружения", create_virtual_environment),
        ("Установка зависимостей", activate_and_install),
        ("Настройка Qt путей", configure_qt_environment),
        ("Настройка Git hooks", setup_git_hooks),
        ("Настройка IDE", setup_ide_config),
        ("Финальная проверка", final_check),
    ]

    for step_name, step_func in steps:
        print(f"\n{'=' * 50}")
        print(f"ЭТАП: {step_name}")
        print("=" * 50)

        if not step_func():
            print(f"\n❌ ОШИБКА НА ЭТАПЕ: {step_name}")
            print("Настройка прервана. Исправьте ошибки и запустите заново.")
            return 1

    print(f"\n{'=' * 60}")
    print("🎉 НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 60)
    print("\nТеперь вы можете:")
    print("1. Активировать окружение:")
    if platform.system() == "Windows":
        print("   .venv\\Scripts\\activate.bat")
    else:
        print("   source .venv/bin/activate")
    print("2. Запустить приложение: python app.py")
    print("3. Запустить тесты: pytest tests/ -v")
    print("4. Проверить здоровье проекта: python scripts/health_check.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
