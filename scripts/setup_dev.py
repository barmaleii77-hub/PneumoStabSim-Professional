#!/usr/bin/env python3
"""
Автоматическая настройка среды разработки PneumoStabSim
"""
import sys
import subprocess
import platform
from pathlib import Path


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

    # Устанавливаем основные зависимости
    if not run_command(
        f"{activate_cmd} pip install -r requirements.txt",
        "Установка основных зависимостей",
    ):
        return False

    # Устанавливаем dev зависимости
    dev_packages = [
        "pytest>=7.0.0",
        "pytest-qt>=4.0.0",
        "pytest-cov>=4.0.0",
        "black>=22.0.0",
        "flake8>=5.0.0",
        "mypy>=1.0.0",
    ]

    dev_cmd = f"{activate_cmd} pip install " + " ".join(dev_packages)
    if not run_command(dev_cmd, "Установка dev зависимостей"):
        return False

    return True


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

    steps = [
        ("Проверка предустановок", check_prerequisites),
        ("Создание виртуального окружения", create_virtual_environment),
        ("Установка зависимостей", activate_and_install),
        ("Настройка Git hooks", setup_git_hooks),
        ("Настройка IDE", setup_ide_config),
        ("Финальная проверка", final_check),
    ]

    for step_name, step_func in steps:
        print(f"\n{'='*50}")
        print(f"ЭТАП: {step_name}")
        print("=" * 50)

        if not step_func():
            print(f"\n❌ ОШИБКА НА ЭТАПЕ: {step_name}")
            print("Настройка прервана. Исправьте ошибки и запустите заново.")
            return 1

    print(f"\n{'='*60}")
    print("🎉 НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!")
    print("='*60")
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
