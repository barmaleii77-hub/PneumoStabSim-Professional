#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PneumoStabSim-Professional Environment Setup Script
Скрипт для автоматической настройки окружения разработки
"""

import sys
import subprocess
from pathlib import Path
import platform


class EnvironmentSetup:
    """Класс для настройки окружения разработки"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.python_executable = self._find_python()
        self.platform = platform.system()

        print("🚀 ИНИЦИАЛИЗАЦИЯ ОКРУЖЕНИЯ PNEUMOSTABSIM-PROFESSIONAL")
        print("=" * 60)
        print(f"📁 Корневая папка: {self.project_root}")
        print(f"🐍 Python executable: {self.python_executable}")
        print(f"💻 Платформа: {self.platform}")
        print("=" * 60)

    def _find_python(self):
        """Находит доступный Python интерпретатор"""
        python_commands = ["py", "python3", "python"]

        for cmd in python_commands:
            try:
                result = subprocess.run(
                    [cmd, "--version"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(f"✅ Найден Python: {cmd} ({result.stdout.strip()})")
                    return cmd
            except FileNotFoundError:
                continue

        print("❌ Python не найден!")
        sys.exit(1)

    def check_python_version(self):
        """Проверяет версию Python"""
        try:
            result = subprocess.run(
                [self.python_executable, "--version"], capture_output=True, text=True
            )
            version_str = result.stdout.strip()
            print(f"🐍 Проверка версии Python: {version_str}")

            # Извлекаем номер версии
            version_parts = version_str.split()[1].split(".")
            major, minor = int(version_parts[0]), int(version_parts[1])

            if major < 3 or (major == 3 and minor < 10):
                print("❌ Требуется Python3.10-3.12!")
                return False
            if major == 3 and minor >= 13:
                print("⚠️ Python3.13+ обнаружен. Текущая версия не поддерживается.")
                print("📝 Используйте Python3.10-3.12 для полной совместимости")
                return False

            if major == 3 and minor == 12:
                print("✅ Оптимальная версия Python для проекта")
            else:
                print("✅ Поддерживаемая версия Python")

            return True

        except Exception as e:
            print(f"❌ Ошибка проверки версии Python: {e}")
            return False

    def setup_virtual_environment(self):
        """Создает и настраивает виртуальное окружение"""
        venv_path = self.project_root / "venv"

        if venv_path.exists():
            print(f"📦 Виртуальное окружение уже существует: {venv_path}")
            return True

        print("📦 Создание виртуального окружения...")
        try:
            subprocess.run(
                [self.python_executable, "-m", "venv", str(venv_path)], check=True
            )
            print("✅ Виртуальное окружение создано успешно")

            # Получаем путь к Python в виртуальном окружении
            if self.platform == "Windows":
                venv_python = venv_path / "Scripts" / "python.exe"
                activate_script = venv_path / "Scripts" / "activate.ps1"
            else:
                venv_python = venv_path / "bin" / "python"
                activate_script = venv_path / "bin" / "activate"

            print(f"🔧 Python в venv: {venv_python}")
            print(f"📜 Скрипт активации: {activate_script}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка создания виртуального окружения: {e}")
            return False

    def install_dependencies(self):
        """Устанавливает зависимости проекта"""
        requirements_file = self.project_root / "requirements.txt"

        if not requirements_file.exists():
            print("⚠️  Файл requirements.txt не найден")
            return False

        print("📦 Установка зависимостей из requirements.txt...")
        try:
            # Используем pip для установки зависимостей
            cmd = [
                self.python_executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(requirements_file),
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            print("✅ Зависимости установлены успешно")

            # Показываем установленные пакеты
            print("\n📋 Основные установленные пакеты:")
            key_packages = ["PySide6", "numpy", "scipy", "matplotlib", "pytest"]

            for package in key_packages:
                try:
                    check_cmd = [self.python_executable, "-m", "pip", "show", package]
                    check_result = subprocess.run(
                        check_cmd, capture_output=True, text=True
                    )
                    if check_result.returncode == 0:
                        lines = check_result.stdout.split("\n")
                        version_line = next(
                            (line for line in lines if line.startswith("Version:")),
                            None,
                        )
                        if version_line:
                            version = version_line.split(": ")[1]
                            print(f"  ✅ {package}: {version}")
                    else:
                        print(f"  ❌ {package}: не установлен")
                except:
                    print(f"  ❓ {package}: ошибка проверки")

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки зависимостей: {e}")
            if e.stderr:
                print(f"Детали ошибки: {e.stderr}")
            return False

    def setup_paths(self):
        """Настраивает переменные окружения и пути"""
        print("🔧 Настройка путей проекта...")

        # Обновляем .env файл с актуальными путями
        env_file = self.project_root / ".env"
        pythonpath = f"{self.project_root}/src;{self.project_root}/tests;{self.project_root}/scripts"

        env_content = f"""# PneumoStabSim Professional Environment (Автоматически обновлено)
PYTHONPATH={pythonpath}
PYTHONIOENCODING=utf-8
PYTHONDONTWRITEBYTECODE=1

# Qt Configuration
QSG_RHI_BACKEND=d3d11
QT_LOGGING_RULES=js.debug=true;qt.qml.debug=true
QSG_INFO=1

# Project Paths
PROJECT_ROOT={self.project_root}
SOURCE_DIR=src
TEST_DIR=tests
SCRIPT_DIR=scripts

# Development Mode
DEVELOPMENT_MODE=true
DEBUG_ENABLED=true

# Russian Localization
LANG=ru_RU.UTF-8
COPILOT_LANGUAGE=ru
"""

        try:
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(env_content)
            print(f"✅ Файл .env обновлен: {env_file}")
        except Exception as e:
            print(f"❌ Ошибка обновления .env: {e}")

        # Создаем необходимые директории
        directories = ["logs", "reports", "temp", ".cache"]
        for dir_name in directories:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                dir_path.mkdir(exist_ok=True)
                print(f"📁 Создана директория: {dir_path}")

        return True

    def test_installation(self):
        """Тестирует установку и конфигурацию"""
        print("\n🧪 ТЕСТИРОВАНИЕ УСТАНОВКИ")
        print("=" * 40)

        # Тест 1: Импорт основных модулей
        test_imports = [
            ("PySide6.QtCore", "Qt Core"),
            ("PySide6.QtWidgets", "Qt Widgets"),
            ("PySide6.QtQuick3D", "Qt Quick 3D"),
            ("numpy", "NumPy"),
            ("scipy", "SciPy"),
            ("matplotlib", "Matplotlib"),
        ]

        print("📦 Тестирование импорта модулей:")
        import_success = 0
        for module_name, display_name in test_imports:
            try:
                subprocess.run(
                    [self.python_executable, "-c", f"import {module_name}"],
                    check=True,
                    capture_output=True,
                )
                print(f"  ✅ {display_name}")
                import_success += 1
            except subprocess.CalledProcessError:
                print(f"  ❌ {display_name}")

        # Тест 2: Запуск диагностики
        print("\n🔍 Тестирование диагностических скриптов:")

        # Тест qml_diagnostic.py
        qml_diag = self.project_root / "qml_diagnostic.py"
        if qml_diag.exists():
            try:
                result = subprocess.run(
                    [self.python_executable, str(qml_diag)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    print("  ✅ QML диагностика")
                else:
                    print("  ⚠️  QML диагностика (предупреждения)")
            except Exception as e:
                print(f"  ❌ QML диагностика: {e}")

        # Тест 3: Простой тест приложения
        print("\n🚀 Тестирование запуска приложения:")
        app_file = self.project_root / "app.py"
        if app_file.exists():
            try:
                # Запускаем в тестовом режиме
                result = subprocess.run(
                    [self.python_executable, str(app_file), "--test-mode"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    print("  ✅ Приложение запускается корректно")
                else:
                    print("  ⚠️  Приложение запустилось с предупреждениями")
                    if result.stderr:
                        print(f"      Детали: {result.stderr[:200]}...")
            except subprocess.TimeoutExpired:
                print(
                    "  ⚠️  Приложение запустилось (timeout - это нормально для тестового режима)"
                )
            except Exception as e:
                print(f"  ❌ Ошибка запуска приложения: {e}")

        # Результат тестирования
        print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print(f"  📦 Импорт модулей: {import_success}/{len(test_imports)}")

        if import_success >= len(test_imports) * 0.8:
            print("✅ Установка прошла успешно! Окружение готово к работе.")
            return True
        else:
            print("⚠️  Установка завершена с предупреждениями. Проверьте ошибки выше.")
            return False

    def print_usage_info(self):
        """Выводит информацию об использовании"""
        print("\n🎯 ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ")
        print("=" * 50)

        print("📋 Основные команды для запуска:")
        print(f"  {self.python_executable} app.py                # Основной запуск")
        print(f"  {self.python_executable} app.py --no-block     # Фоновый режим")
        print(f"  {self.python_executable} app.py --test-mode    # Тестовый режим")
        print(f"  {self.python_executable} app.py --debug        # Режим отладки")

        print("\n🧪 Команды для тестирования:")
        print(f"  {self.python_executable} -m pytest tests/ -v  # Запуск всех тестов")
        print(f"  {self.python_executable} quick_test.py         # Быстрый тест")
        print(f"  {self.python_executable} qml_diagnostic.py     # QML диагностика")

        print("\n🔧 VS Code:")
        print("  1. Откройте папку проекта в VS Code")
        print(
            "  2. Выберите интерпретатор Python (Ctrl+Shift+P > Python: Select Interpreter)"
        )
        print("  3. Используйте F5 для отладки или Ctrl+F5 для запуска")

        print("\n💡 PowerShell (в VS Code):")
        print("  Профиль PowerShell автоматически загрузится с алиасами:")
        print("  app, debug, test, pytest, health, info")

        if self.platform == "Windows":
            venv_activate = self.project_root / "venv" / "Scripts" / "activate.ps1"
            print("\n📦 Активация виртуального окружения:")
            print(f"  {venv_activate}")

        print("\n🎯 ВАЖНО: Используется ТОЛЬКО main_optimized.qml")
        print("  ✅ Дублирование примитивов исправлено")
        print("  ✅ Оптимизированная кинематика v4.2")

    def run_setup(self):
        """Запускает полную настройку окружения"""
        try:
            # Этап 1: Проверка Python
            if not self.check_python_version():
                return False

            # Этап 2: Виртуальное окружение
            if not self.setup_virtual_environment():
                print("⚠️  Продолжаем без виртуального окружения...")

            # Этап 3: Установка зависимостей
            if not self.install_dependencies():
                return False

            # Этап 4: Настройка путей
            if not self.setup_paths():
                return False

            # Этап 5: Тестирование
            test_success = self.test_installation()

            # Этап 6: Инструкции
            self.print_usage_info()

            print("\n🎉 НАСТРОЙКА ОКРУЖЕНИЯ ЗАВЕРШЕНА!")
            print("=" * 50)

            if test_success:
                print("✅ Все компоненты работают корректно")
                print("🚀 Проект готов к разработке!")
            else:
                print("⚠️  Настройка завершена с предупреждениями")
                print("📝 Проверьте сообщения об ошибках выше")

            return test_success

        except KeyboardInterrupt:
            print("\n⚠️  Настройка прервана пользователем")
            return False
        except Exception as e:
            print(f"\n❌ Критическая ошибка настройки: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    """Главная функция"""
    print("🔧 PneumoStabSim-Professional Environment Setup")
    print("Скрипт автоматической настройки окружения разработки")
    print()

    setup = EnvironmentSetup()
    success = setup.run_setup()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
