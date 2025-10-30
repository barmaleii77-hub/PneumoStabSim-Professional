#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PneumoStabSim-Professional Environment Setup Script
Скрипт для автоматической настройки окружения разработки
"""

import os
import platform
import subprocess
import sys
import hashlib
import shutil
import argparse
import glob
import textwrap
from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

QT_ENV_DEFAULTS: Dict[str, str] = {
    "QT_QPA_PLATFORM": "offscreen",
    "QT_QUICK_BACKEND": "software",
    "QT_PLUGIN_PATH": "",
    "QML2_IMPORT_PATH": "",
}

DEFAULT_SOURCES = [
    "https://download.qt.io/official_releases/qt/5.15/5.15.2/",
    "https://download.qt.io/archive/qt/5.15/5.15.2/",
    "https://download.qt.io/official_releases/qt/6.2/6.2.4/",
    "https://download.qt.io/archive/qt/6.2/6.2.4/",
]
QT_SOURCES_DIR = Path.home() / "qt_sources"


@lru_cache(maxsize=1)
def _detect_qt_environment() -> Dict[str, str]:
    """Возвращает рекомендуемые переменные окружения Qt."""

    environment = dict(QT_ENV_DEFAULTS)

    try:
        from PySide6.QtCore import QLibraryInfo, LibraryLocation  # type: ignore
    except Exception as exc:  # pragma: no cover - диагностический вывод
        print(f"⚠️ Не удалось автоматически определить пути Qt: {exc}")
        return environment

    plugin_path = QLibraryInfo.path(LibraryLocation.Plugins)
    if plugin_path:
        environment["QT_PLUGIN_PATH"] = plugin_path

    qml_import_path = QLibraryInfo.path(LibraryLocation.QmlImports)
    if qml_import_path:
        environment["QML2_IMPORT_PATH"] = qml_import_path

    return environment


class Logger:
    """Простой логгер для вывода сообщений с таймстемпом"""

    def __init__(self, prefix: str = ""):
        self.prefix = prefix

    def log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{timestamp} {self.prefix}{message}")


def _runtime_version_blocker(version: tuple[int, int]) -> Optional[str]:
    """Return a human readable error if the runtime Python is unsupported.

    The setup utilities intentionally target Python 3.11–3.13 because Qt 6.10 /
    PySide6 6.10.0 is not yet available for Python 3.14.  When the bootstrap
    script itself is executed with an unsupported interpreter the dependency
    installation stage will fail with a misleading pip resolution error.  By
    detecting the situation upfront we can provide an actionable explanation to
    the developer.
    """

    major, minor = version
    if major != 3:
        return (
            "Поддерживается только Python 3.x. "
            "Установите Python 3.13 и повторите настройку."
        )

    if minor >= 14:
        return (
            "Обнаружен Python 3.%d. Qt/PySide6 6.10.0 пока не выпускается "
            "для этой версии. Установите Python 3.13 и перезапустите скрипт." % minor
        )

    return None


class EnvironmentSetup:
    """Класс для настройки окружения разработки"""

    def __init__(self, qt_sdk_version: Optional[str] = None):
        self.project_root = Path(__file__).parent
        self.platform = platform.system()
        self.logger = Logger("[Setup] ")

        self.qt_environment = _detect_qt_environment()
        os.environ.update(self.qt_environment)

        self.python_executable = self._find_python()
        self.python_version = self._detect_python_version()
        self.qt_sdk_version = qt_sdk_version
        self.venv_path = self.project_root / ".venv"
        self._venv_python_cmd: Optional[List[str]] = None
        self._venv_python_announced = False
        self._root_warning_shown = False

        self._pip_extra_args = self._detect_pip_extra_args()

        self.logger.log("ИНИЦИАЛИЗАЦИЯ ОКРУЖЕНИЯ PNEUMOSTABSIM-PROFESSIONAL")
        self.logger.log("=" * 60)
        self.logger.log(f"Корневая папка: {self.project_root}")
        self.logger.log(f"Python executable: {self.python_executable}")
        self.logger.log(
            "Обнаруженная версия Python: "
            + ".".join(str(part) for part in self.python_version)
        )
        self.logger.log(f"Платформа: {self.platform}")
        self.logger.log("Qt окружение:")
        for key, value in self.qt_environment.items():
            self.logger.log(f" • {key}={value}")
        self.logger.log("=" * 60)

    def _find_python(self) -> List[str]:
        """Находит предпочтительный интерпретатор Python3.13 (fallback 3.11)."""

        python_candidates: List[List[str]] = [
            ["py", "-3.13"],
            ["python3.13"],
            ["py", "-3.11"],
            ["python3.11"],
            ["python3"],
            ["py", "-3"],
            ["python"],
        ]

        for candidate in python_candidates:
            try:
                result = subprocess.run(
                    candidate + ["--version"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    cmd_display = " ".join(candidate)
                    self.logger.log(
                        f"✅ Найден Python: {cmd_display} ({result.stdout.strip()})"
                    )
                    return candidate
            except FileNotFoundError:
                continue

        self.logger.log("❌ Не удалось найти поддерживаемую версию Python (3.11–3.13)!")
        sys.exit(1)

    def _detect_python_version(self) -> tuple[int, int, int]:
        try:
            result = subprocess.run(
                self.python_executable
                + [
                    "-c",
                    "import sys; print('.'.join(map(str, sys.version_info[:3])))",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            version_parts = tuple(
                int(part) for part in result.stdout.strip().split(".")
            )
            return version_parts  # type: ignore[return-value]
        except Exception:
            return sys.version_info[:3]

    def _detect_pip_extra_args(self) -> List[str]:
        """Возвращает дополнительные флаги pip для безопасного запуска от root."""

        geteuid = getattr(os, "geteuid", None)
        if callable(geteuid):
            try:
                if geteuid() == 0:
                    return ["--root-user-action=ignore"]
            except OSError:
                return []
        return []

    def _venv_executables(self) -> tuple[Path, Path]:
        if self.platform == "Windows":
            return (
                self.venv_path / "Scripts" / "python.exe",
                self.venv_path / "Scripts" / "activate.ps1",
            )
        return (
            self.venv_path / "bin" / "python",
            self.venv_path / "bin" / "activate",
        )

    def _register_venv_python(self, python_path: Path) -> bool:
        if not python_path.exists():
            self.logger.log(
                "⚠️ Не удалось найти интерпретатор виртуального окружения: "
                f"{python_path}"
            )
            return False

        self._venv_python_cmd = [str(python_path)]
        if not self._venv_python_announced:
            self.logger.log(
                "🛡️ pip команды будут выполняться в изолированном виртуальном окружении"
            )
            self._venv_python_announced = True
        return True

    def _pip_command(self, *args: str) -> List[str]:
        """Формирует команду pip с учётом дополнительных флагов."""

        launcher = self._resolve_pip_launcher()
        command = [*launcher, *args]
        return command

    def _resolve_pip_launcher(self) -> List[str]:
        if self._venv_python_cmd is None and self.venv_path.exists():
            venv_python, _ = self._venv_executables()
            if venv_python.exists():
                self._register_venv_python(venv_python)

        if self._venv_python_cmd is not None:
            return [*self._venv_python_cmd, "-m", "pip"]

        if self._pip_extra_args and not self._root_warning_shown:
            self.logger.log(
                "⚠️ Запуск pip от имени root без активного виртуального окружения"
            )
            self._root_warning_shown = True

        return [*self.python_executable, "-m", "pip", *self._pip_extra_args]

    def check_python_version(self):
        """Проверяет версию Python"""
        try:
            result = subprocess.run(
                self.python_executable + ["--version"],
                capture_output=True,
                text=True,
            )
            version_str = result.stdout.strip()
            self.logger.log(f"Проверка версии Python: {version_str}")

            # Извлекаем номер версии
            version_parts = version_str.split()[1].split(".")
            major, minor = int(version_parts[0]), int(version_parts[1])

            if major != 3 or minor not in {11, 12, 13}:
                self.logger.log("❌ Требуется Python3.11–3.13!")
                self.logger.log(
                    "📝 Установите поддерживаемую версию Python и повторите настройку"
                )
                return False

            if minor == 13:
                self.logger.log("✅ Обнаружена рекомендуемая версия Python3.13")
            else:
                self.logger.log(
                    "⚠️ Обнаружена поддерживаемая версия Python3."
                    + str(minor)
                    + ". Рекомендуем обновиться до 3.13 для основной конфигурации."
                )

            return True

        except Exception as e:
            self.logger.log(f"❌ Ошибка проверки версии Python: {e}")
            return False

    def setup_virtual_environment(self):
        """Создает и настраивает виртуальное окружение"""
        venv_path = self.venv_path
        venv_python, activate_script = self._venv_executables()

        if venv_path.exists():
            self.logger.log(f"📦 Виртуальное окружение уже существует: {venv_path}")
            self.logger.log(f"🔧 Python в venv: {venv_python}")
            self._register_venv_python(venv_python)
            if activate_script.exists():
                self.logger.log(f"📜 Скрипт активации: {activate_script}")
            else:
                self.logger.log(
                    "⚠️ Скрипт активации виртуального окружения не найден: "
                    f"{activate_script}"
                )
            return True

        self.logger.log("📦 Создание виртуального окружения...")
        try:
            subprocess.run(
                self.python_executable + ["-m", "venv", str(venv_path)],
                check=True,
            )
            self.logger.log("✅ Виртуальное окружение создано успешно")

            self.logger.log(f"🔧 Python в venv: {venv_python}")
            self.logger.log(f"📜 Скрипт активации: {activate_script}")
            self._register_venv_python(venv_python)

            return True

        except subprocess.CalledProcessError as e:
            self.logger.log(f"❌ Ошибка создания виртуального окружения: {e}")
            return False

    def _ensure_qt_runtime_dependencies(self) -> bool:
        """Проверяет и устанавливает системные пакеты PySide6 на Linux."""

        if self.platform != "Linux":
            return True

        required_packages = [
            "libegl1",
            "libgl1",
            "libxkbcommon0",
            "libxcb-cursor0",
            "libnss3",
            "libdbus-1-3",
        ]
        missing: list[str] = []

        for package in required_packages:
            try:
                result = subprocess.run(
                    ["dpkg-query", "-W", "-f=${Status}", package],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except FileNotFoundError:
                self.logger.log(
                    "⚠️ dpkg-query не найден. Установите зависимости вручную: "
                    + ", ".join(required_packages)
                )
                return False

            status = result.stdout.strip()
            if "install ok installed" not in status:
                missing.append(package)

        if not missing:
            self.logger.log(
                "✅ Системные библиотеки Qt уже установлены: "
                + ", ".join(required_packages)
            )
            return True

        apt_get = shutil.which("apt-get")
        if not apt_get:
            self.logger.log(
                "❌ apt-get не найден. Установите пакеты вручную: "
                + ", ".join(missing)
            )
            return False

        install_cmd = [apt_get, "install", "-y", *sorted(set(missing))]
        update_cmd = [apt_get, "update"]

        if os.geteuid() != 0:
            sudo = shutil.which("sudo")
            if not sudo:
                self.logger.log(
                    "❌ Недостаточно прав для установки системных пакетов. "
                    "Запустите скрипт с sudo или установите вручную: "
                    + ", ".join(missing)
                )
                return False
            update_cmd.insert(0, sudo)
            install_cmd.insert(0, sudo)

        try:
            self.logger.log(
                "🔧 Установка системных библиотек Qt: " + ", ".join(missing)
            )
            subprocess.run(update_cmd, check=True)
            subprocess.run(install_cmd, check=True)
        except subprocess.CalledProcessError as exc:
            self.logger.log(f"❌ Не удалось установить системные пакеты: {exc}")
            return False

        self.logger.log("✅ Qt зависимости для PySide6 установлены")
        return True

    def install_dependencies(self):
        """Устанавливает зависимости проекта"""
        if not self._ensure_qt_runtime_dependencies():
            return False

        uv_executable = shutil.which("uv")
        if uv_executable:
            self.logger.log("📦 Установка зависимостей через uv sync…")
            try:
                subprocess.run(
                    [uv_executable, "sync"], cwd=self.project_root, check=True
                )
                self.logger.log("✅ Зависимости установлены через uv")
                self._show_installed_packages()
                return True
            except subprocess.CalledProcessError as exc:
                self.logger.log(f"❌ Ошибка выполнения uv sync: {exc}")

        requirements_file = self.project_root / "requirements.txt"

        if not requirements_file.exists():
            self.logger.log("⚠️  Файл requirements.txt не найден")
            return self._install_project_editable()

        self.logger.log("📦 Установка зависимостей из requirements.txt...")
        try:
            # Используем pip для установки зависимостей
            cmd = self._pip_command(
                "install",
                "-r",
                str(requirements_file),
                "-c",
                str(self.project_root / "requirements-compatible.txt"),
            )
            subprocess.run(cmd, check=True)

            self.logger.log("✅ Зависимости установлены успешно")

            # Показываем установленные пакеты
            self._show_installed_packages()

            return True

        except subprocess.CalledProcessError as e:
            self.logger.log(f"❌ Ошибка установки зависимостей: {e}")
            if e.stderr:
                self.logger.log(f"Детали ошибки: {e.stderr}")
            self.logger.log(
                "⚠️  Пытаемся установить зависимости в editable-режиме из pyproject.toml"
            )
            return self._install_project_editable()

    def _install_project_editable(self) -> bool:
        """Пробует установить проект в editable-режиме в качестве запасного варианта."""

        commands = [
            self._pip_command("install", "-e", "."),
            self._pip_command("install", "-e", ".[dev]"),
        ]

        success = True
        for cmd in commands:
            try:
                subprocess.run(cmd, cwd=self.project_root, check=True)
            except subprocess.CalledProcessError as exc:
                self.logger.log(f"❌ Не удалось выполнить {' '.join(cmd)}: {exc}")
                success = False
                break

        if success:
            self.logger.log("✅ Зависимости установлены через editable-режим")
            self._show_installed_packages()
        else:
            self.logger.log(
                "❌ Установка зависимостей не удалась даже через editable-режим"
            )

        return success

    def _verify_dependencies_hashes(self, requirements_file: Path) -> bool:
        """Проверяет хеши файлов зависимостей для целостности"""
        self.logger.log("🔍 Проверка целостности файлов зависимостей...")
        try:
            # Получаем список всех файлов в requirements.txt
            with open(requirements_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Фильтруем только строки с зависимостями (без комментариев и пустых строк)
            dependencies = [
                line.split("#")[0].strip()
                for line in lines
                if line.strip() and not line.startswith("#")
            ]

            all_files_ok = True
            for dep in dependencies:
                if "@" in dep:
                    # Обрабатываем зависимости с указанием URL-адреса (например, Git)
                    package_name = dep.split("@")[0]
                    url = dep.split("@")[1]
                    if not self._check_url_hash(package_name, url):
                        all_files_ok = False
                else:
                    # Обрабатываем обычные зависимости
                    package_name = dep
                    if not self._check_package_hash(package_name):
                        all_files_ok = False

            return all_files_ok
        except Exception as e:
            self.logger.log(f"❌ Ошибка проверки хешей зависимостей: {e}")
            return False

    def _check_url_hash(self, package_name: str, url: str) -> bool:
        """Проверяет хеш зависимости, установленной по URL"""
        try:
            # Скачиваем файл и вычисляем его хеш
            response = subprocess.run(
                ["curl", "-sSL", url],
                capture_output=True,
                text=True,
                check=True,
            )
            file_hash = hashlib.sha256(response.stdout.encode()).hexdigest()

            # Сравниваем с хешем в requirements.txt
            expected_hash = url.split("#")[-1]
            if file_hash != expected_hash:
                self.logger.log(
                    f"❌ Хеш не совпадает для {package_name} (URL): ожидаемый {expected_hash}, найденный {file_hash}"
                )
                return False
            else:
                self.logger.log(f"✅ Хеш верифицирован для {package_name} (URL)")
                return True
        except Exception as e:
            self.logger.log(f"❌ Ошибка проверки хеша для {package_name} (URL): {e}")
            return False

    def _check_package_hash(self, package_name: str) -> bool:
        """Проверяет хеш установленного пакета"""
        try:
            # Получаем информацию о пакете
            result = subprocess.run(
                self._pip_command("show", package_name),
                capture_output=True,
                text=True,
                check=True,
            )
            # Ищем строку с хешем (SHA256)
            for line in result.stdout.splitlines():
                if line.startswith("Location:"):
                    package_dir = line.split(":", 1)[1].strip()
                    # Проверяем наличие файла .whl
                    wheel_files = list(Path(package_dir).glob(f"*.whl"))
                    if wheel_files:
                        # Вычисляем хеш первого найденного файла .whl
                        file_hash = hashlib.sha256(
                            wheel_files[0].read_bytes()
                        ).hexdigest()
                        self.logger.log(
                            f"📦 Найден пакет {package_name}, хеш={file_hash}"
                        )
                        return True
            self.logger.log(f"⚠️ Пакет {package_name} не найден или не имеет .whl файла")
            return False
        except Exception as e:
            self.logger.log(f"❌ Ошибка проверки хеша для {package_name}: {e}")
            return False

    def _show_installed_packages(self):
        """Показывает установленные пакеты после установки зависимостей"""
        self.logger.log("\n📋 Основные установленные пакеты:")
        key_packages = [
            "PySide6",
            "PySide6-QtQuick3D",
            "numpy",
            "scipy",
            "PyOpenGL",
            "pytest",
        ]

        for package in key_packages:
            try:
                check_cmd = self._pip_command("show", package)
                check_result = subprocess.run(check_cmd, capture_output=True, text=True)
                if check_result.returncode == 0:
                    lines = check_result.stdout.split("\n")
                    version_line = next(
                        (line for line in lines if line.startswith("Version:")),
                        None,
                    )
                    if version_line:
                        version = version_line.split(": ")[1]
                        self.logger.log(f"  ✅ {package}: {version}")
                else:
                    self.logger.log(f"  ❌ {package}: не установлен")
            except Exception:
                self.logger.log(f"  ❓ {package}: ошибка проверки")

    def setup_paths(self):
        """Настраивает переменные окружения и пути"""
        self.logger.log("🔧 Настройка путей проекта...")

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
            self.logger.log(f"✅ Файл .env обновлен: {env_file}")
        except Exception as e:
            self.logger.log(f"❌ Ошибка обновления .env: {e}")

        # Создаем необходимые директории
        directories = ["logs", "reports", "temp", ".cache"]
        for dir_name in directories:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                dir_path.mkdir(exist_ok=True)
                self.logger.log(f"📁 Создана директория: {dir_path}")

        return True

    def test_installation(self):
        """Тестирует установку и конфигурацию"""
        self.logger.log("\n🧪 ТЕСТИРОВАНИЕ УСТАНОВКИ")
        self.logger.log("=" * 40)

        # Тест 1: Импорт основных модулей
        test_imports = [
            ("PySide6.QtCore", "Qt Core"),
            ("PySide6.QtWidgets", "Qt Widgets"),
            ("PySide6.QtQuick3D", "Qt Quick 3D"),
            ("numpy", "NumPy"),
            ("scipy", "SciPy"),
            ("matplotlib", "Matplotlib"),
        ]

        self.logger.log("📦 Тестирование импорта модулей:")
        import_success = 0
        for module_name, display_name in test_imports:
            try:
                subprocess.run(
                    self.python_executable + ["-c", f"import {module_name}"],
                    check=True,
                    capture_output=True,
                )
                self.logger.log(f"  ✅ {display_name}")
                import_success += 1
            except subprocess.CalledProcessError:
                self.logger.log(f"  ❌ {display_name}")

        # Результат тестирования
        self.logger.log("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        self.logger.log(f"  📦 Импорт модулей: {import_success}/{len(test_imports)}")

        if import_success >= len(test_imports) * 0.8:
            self.logger.log("✅ Установка прошла успешно! Окружение готово к работе.")
            return True
        else:
            self.logger.log(
                "⚠️  Установка завершена с предупреждениями. Проверьте ошибки выше."
            )
            return False

    def print_usage_info(self):
        """Выводит информацию об использовании"""
        self.logger.log("\n🎯 ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ")
        self.logger.log("=" * 50)

        self.logger.log("📋 Основные команды для запуска:")
        executable = " ".join(self.python_executable)
        self.logger.log(f"  {executable} app.py        # Основной запуск")
        self.logger.log(f"  {executable} app.py --no-block     # Фоновый режим")
        self.logger.log(f"  {executable} app.py --test-mode    # Тестовый режим")
        self.logger.log(f"  {executable} app.py --debug        # Режим отладки")

        self.logger.log("\n🧪 Команды для тестирования:")
        self.logger.log(f"  {executable} -m pytest tests/ -v  # Запуск всех тестов")

        if self.platform == "Windows":
            venv_activate = self.project_root / "venv" / "Scripts" / "activate.ps1"
            self.logger.log("\n📦 Активация виртуального окружения:")
            self.logger.log(f"  {venv_activate}")

        self.logger.log("\n📚 Подробнее о профилях окружения: docs/environments.md")

    def download_qt_sdk(self):
        """Скачивает и устанавливает Qt SDK"""
        if not self.qt_sdk_version:
            self.logger.log("➕ Qt SDK не указана, пропуск загрузки.")
            return True

        # Устанавливаем необходимые зависимости для загрузки
        self.logger.log("Установка зависимостей для загрузки Qt SDK...")
        try:
            if self.platform == "Windows":
                arch = "win32" if platform.architecture()[0] == "32bit" else "win64"
                url = f"https://download.qt.io/official_releases/qt/6.2/6.2.4/qt-installer-windows-{arch}.exe"
                installer = "qt-installer.exe"
            elif self.platform == "Linux":
                url = "https://download.qt.io/official_releases/qt/6.2/6.2.4/qt-unified-linux-x64-online.run"
                installer = "qt-installer.run"
            else:
                self.logger.log(
                    "❌ Поддержка установки Qt SDK доступна только для Windows и Linux"
                )
                return False

            # Скачиваем установщик
            response = subprocess.run(
                ["curl", "-L", "-o", installer, url],
                check=True,
                capture_output=True,
                text=True,
            )
            if response.returncode != 0:
                self.logger.log(f"❌ Ошибка скачивания Qt SDK: {response.stderr}")
                return False

            # Запускаем установщик
            self.logger.log(f"📥 Запуск установщика Qt SDK: {installer}")
            if self.platform == "Windows":
                response = subprocess.run(
                    [
                        "cmd",
                        "/c",
                        installer,
                        "--silent",
                        "--skip-components",
                        "qt.5.15.2.ansic",
                        "--include-subdir",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            else:
                response = subprocess.run(
                    [
                        installer,
                        "--silent",
                        "--skip-components",
                        "qt.5.15.2.ansic",
                        "--include-subdir",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

            if response.returncode != 0:
                self.logger.log(f"❌ Ошибка установки Qt SDK: {response.stderr}")
                return False

            self.logger.log("✅ Qt SDK установлена успешно")

            return True
        except Exception as e:
            self.logger.log(f"❌ Ошибка установки Qt SDK: {e}")
            return False
        finally:
            # Удаляем установщик после завершения
            if Path(installer).exists():
                self.logger.log(f"🗑️ Удаление установщика: {installer}")
                try:
                    if platform.system() == "Windows":
                        subprocess.run(
                            ["cmd", "/c", "del", "/F", "/Q", installer], check=True
                        )
                    else:
                        subprocess.run(["rm", "-f", installer], check=True)
                except Exception as e:
                    self.logger.log(f"⚠️ Ошибка удаления установщика: {e}")

    def run_setup(self):
        """Запускает полную настройку окружения"""
        try:
            # Этап 1: Проверка Python
            if not self.check_python_version():
                return False

            # Этап 2: Виртуальное окружение
            if not self.setup_virtual_environment():
                self.logger.log("⚠️  Продолжаем без виртуального окружения...")

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

            self.logger.log("\n🎉 НАСТРОЙКА ОКРУЖЕНИЯ ЗАВЕРШЕНА!")
            self.logger.log("=" * 50)

            if test_success:
                self.logger.log("✅ Все компоненты работают корректно")
                self.logger.log("🚀 Проект готов к разработке!")
            else:
                self.logger.log("⚠️  Настройка завершена с предупреждениями")
                self.logger.log("📝 Проверьте сообщения об ошибках выше")

            return test_success

        except KeyboardInterrupt:
            self.logger.log("\n⚠️  Настройка прервана пользователем")
            return False
        except Exception as e:
            self.logger.log(f"\n❌ Критическая ошибка настройки: {e}")
            import traceback

            traceback.print_exc()
            return False


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(
            """\
            PneumoStabSim-Professional Environment Setup Script
            Скрипт для автоматической настройки окружения разработки

            Примечание: Для успешного выполнения скрипта требуются права администратора/суперпользователя.
            """
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--install-qt",
        action="store_true",
        help="Скачать и установить последнюю версию Qt SDK",
    )
    parser.add_argument(
        "--qt-version",
        type=str,
        default=None,
        help="Версия Qt SDK для установки (например, 6.2.4).",
    )
    parser.add_argument(
        "--no-pip",
        action="store_true",
        help="Пропустить этап установки зависимостей с помощью pip",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Подробный вывод информации о процессе установки",
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Тихий режим, без дополнительного вывода",
    )

    return parser.parse_args()


def main():
    """Главная функция"""
    args = parse_arguments()

    blocker_message = _runtime_version_blocker(sys.version_info[:2])
    if blocker_message is not None:
        if not args.silent:
            print("❌ Неподдерживаемая версия Python")
            print(blocker_message)
            print(
                "PySide6 6.10.0 поддерживает только Python 3.11–3.13. "
                "Подробнее см. SETUP_GUIDE.md."
            )
        return 1

    with suppress_stdout(args.silent):
        if not args.silent:
            print("🔧 PneumoStabSim-Professional Environment Setup")
            print("Скрипт автоматической настройки окружения разработки")
            print()

        setup = EnvironmentSetup(qt_sdk_version=args.qt_version)
        success = setup.run_setup()

    return 0 if success else 1


@contextmanager
def suppress_stdout(enabled: bool):
    """Подавляет вывод stdout, если включен тихий режим."""

    if not enabled:
        yield
        return

    original_stdout = sys.stdout
    try:
        with open(os.devnull, "w", encoding="utf-8") as devnull:
            sys.stdout = devnull
            yield
    finally:
        sys.stdout = original_stdout


if __name__ == "__main__":
    sys.exit(main())
