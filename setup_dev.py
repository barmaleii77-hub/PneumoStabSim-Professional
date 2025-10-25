#!/usr/bin/env python3
"""
Setup script для PneumoStabSim Professional
Автоматическая настройка окружения разработки
"""

import sys
import subprocess
import platform
from pathlib import Path


def run_command(cmd, check=True):
    """Выполнить команду с выводом"""
    print(f"🔧 Выполняем: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, check=check, capture_output=True, text=True
        )
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e}")
        if e.stderr:
            print(f"Детали ошибки: {e.stderr}")
        return False


def check_python():
    """Проверка версии Python"""
    version = sys.version_info
    print(f"🐍 Версия Python: {version.major}.{version.minor}.{version.micro}")

    if version < (3, 8):
        print("❌ Требуется Python 3.8+")
        return False
    elif version >= (3, 12):
        print("⚠️ Python 3.12+ может иметь проблемы совместимости")

    return True


def setup_venv():
    """Создание виртуального окружения"""
    venv_path = Path("venv")

    if venv_path.exists():
        print("📦 Виртуальное окружение уже существует")
        return True

    print("📦 Создание виртуального окружения...")
    if not run_command([sys.executable, "-m", "venv", "venv"]):
        return False

    return True


def get_pip_command():
    """Получить команду pip для текущей системы"""
    if platform.system() == "Windows":
        return "venv\\Scripts\\pip"
    else:
        return "venv/bin/pip"


def install_dependencies():
    """Установка зависимостей"""
    pip_cmd = get_pip_command()

    print("📥 Обновление pip...")
    if not run_command([pip_cmd, "install", "--upgrade", "pip"]):
        return False

    print("📥 Установка основных зависимостей...")
    if not run_command([pip_cmd, "install", "-r", "requirements.txt"]):
        return False

    # Опционально устанавливаем dev зависимости
    if Path("requirements-dev.txt").exists():
        print("📥 Установка зависимостей разработки...")
        run_command([pip_cmd, "install", "-r", "requirements-dev.txt"], check=False)

    return True


def setup_pre_commit():
    """Настройка pre-commit hooks"""
    if Path(".pre-commit-config.yaml").exists():
        print("🪝 Настройка pre-commit hooks...")
        venv_python = (
            "venv\\Scripts\\python"
            if platform.system() == "Windows"
            else "venv/bin/python"
        )
        run_command([venv_python, "-m", "pre_commit", "install"], check=False)


def create_directories():
    """Создание необходимых директорий"""
    dirs = ["logs", "tests", "docs", "build", "dist"]

    for dir_name in dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            print(f"📁 Создание директории: {dir_name}")
            dir_path.mkdir(parents=True, exist_ok=True)


def main():
    """Основная функция настройки"""
    print("🚀 Настройка окружения PneumoStabSim Professional")
    print("=" * 50)

    # Проверки
    if not check_python():
        sys.exit(1)

    # Создание структуры
    create_directories()

    # Настройка виртуального окружения
    if not setup_venv():
        print("❌ Не удалось создать виртуальное окружение")
        sys.exit(1)

    # Установка зависимостей
    if not install_dependencies():
        print("❌ Не удалось установить зависимости")
        sys.exit(1)

    # Настройка pre-commit
    setup_pre_commit()

    print("\n" + "=" * 50)
    print("✅ Настройка завершена!")
    print("\n📋 Следующие шаги:")

    if platform.system() == "Windows":
        print("1. Активируйте окружение: venv\\Scripts\\activate")
    else:
        print("1. Активируйте окружение: source venv/bin/activate")

    print("2. Запустите приложение: py app.py")
    print("3. Для разработки откройте проект в VS Code или Visual Studio")

    print("\n🛠️ Доступные команды:")
    print("- py app.py                 # Запуск приложения")
    print("- py app.py --debug         # Режим отладки")
    print("- py app.py --safe-mode     # Безопасный режим")
    print("- py apply_patches.py       # Применение патчей")
    print("- pytest tests/             # Запуск тестов")


if __name__ == "__main__":
    main()
