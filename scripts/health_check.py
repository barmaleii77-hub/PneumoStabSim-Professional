#!/usr/bin/env python3
"""
Проверка состояния проекта и зависимостей
"""

from __future__ import annotations

import sys
import subprocess
import importlib
from pathlib import Path

from importlib import metadata

from packaging.version import InvalidVersion, Version

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.platform_info import log_platform_context


def check_python_version():
    """Проверяет версию Python"""
    version = sys.version_info
    print(f"Python версия: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 13):
        print("❌ Требуется Python 3.13+")
        return False
    else:
        print("✅ Версия Python подходит")
        return True


def _pip_show_version(distribution_name: str) -> str | None:
    """Возвращает версию пакета через ``pip show`` для текущего интерпретатора."""

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", distribution_name],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None

    if result.returncode != 0 or not result.stdout:
        return None

    for line in result.stdout.splitlines():
        if line.lower().startswith("version:"):
            return line.split(":", 1)[1].strip()

    return None


def _get_distribution_version(
    distribution_names: tuple[str, ...],
) -> tuple[str | None, str | None]:
    """Пытается определить версию установленного дистрибутива."""

    for name in distribution_names:
        try:
            return metadata.version(name), name
        except metadata.PackageNotFoundError:
            version_from_pip = _pip_show_version(name)
            if version_from_pip:
                return version_from_pip, name

    return None, None


def check_dependencies():
    """Проверяет основные зависимости"""

    required_packages = (
        {
            "display": "PySide6",
            "min_version": "6.10.0",
            "import_names": ("PySide6",),
            "distributions": ("PySide6", "PySide6-Essentials", "PySide6-Addons"),
        },
        {
            "display": "numpy",
            "min_version": "2.0.0",
            "import_names": ("numpy",),
            "distributions": ("numpy",),
        },
        {
            "display": "scipy",
            "min_version": "1.10.0",
            "import_names": ("scipy",),
            "distributions": ("scipy",),
        },
        {
            "display": "matplotlib",
            "min_version": "3.5.0",
            "import_names": ("matplotlib",),
            "distributions": ("matplotlib",),
        },
    )

    all_ok = True

    for package in required_packages:
        display = package["display"]
        min_version = package["min_version"]
        import_names = package["import_names"]
        distributions = package["distributions"]

        module = None
        imported_name = None
        for import_name in import_names:
            try:
                module = importlib.import_module(import_name)
                imported_name = import_name
                break
            except ImportError:
                continue

        if module is None:
            print(f"❌ {display} не установлен (импорт не найден)")
            all_ok = False
            continue

        version_attr = getattr(module, "__version__", None)
        version, dist_name = _get_distribution_version(distributions)

        if version is None:
            version = version_attr or "unknown"

        info_suffix = ""
        if dist_name:
            info_suffix = f" (дистрибутив {dist_name})"
        elif imported_name:
            info_suffix = f" (модуль {imported_name})"

        print(f"✅ {display}: {version}{info_suffix}")

        try:
            current_version = Version(version)
            required_version = Version(min_version)
        except InvalidVersion:
            print(
                f"⚠️ Невозможно сравнить версии для {display}: текущее значение '{version}'"
            )
            continue

        if current_version < required_version:
            print(
                f"❌ {display}: требуется версия {min_version}+ (обнаружена {version})"
            )
            all_ok = False

    return all_ok


def check_project_structure():
    """Проверяет структуру проекта"""
    required_dirs = [
        "src",
        "src/ui",
        "src/core",
        "tests",
        "assets",
        "docs",
        "config",
        "scripts",
    ]

    required_files = [
        "app.py",
        "requirements.txt",
        ".editorconfig",
        ".gitignore",
        "README.md",
    ]

    all_ok = True

    print("\nПроверка директорий:")
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ отсутствует")
            all_ok = False

    print("\nПроверка файлов:")
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} отсутствует")
            all_ok = False

    return all_ok


def check_git_status():
    """Проверяет статус Git репозитория"""
    try:
        # Проверяем, что мы в git репозитории
        subprocess.run(["git", "status"], capture_output=True, check=True, text=True)
        print("✅ Git репозиторий инициализирован")

        # Проверяем удаленный репозиторий
        result = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True)
        if result.stdout:
            print("✅ Удаленный репозиторий настроен")
        else:
            print("⚠️ Удаленный репозиторий не настроен")

        return True
    except subprocess.CalledProcessError:
        print("❌ Git репозиторий не инициализирован")
        return False


def main():
    """Основная функция проверки"""
    print("=== ПРОВЕРКА СОСТОЯНИЯ ПРОЕКТА ===\n")
    log_platform_context({"script": "health_check"})

    checks = [
        ("Python версия", check_python_version),
        ("Зависимости", check_dependencies),
        ("Структура проекта", check_project_structure),
        ("Git репозиторий", check_git_status),
    ]

    results = {}

    for name, check_func in checks:
        print(f"\n--- {name} ---")
        results[name] = check_func()

    print("\n=== ИТОГОВЫЙ РЕЗУЛЬТАТ ===")

    all_passed = all(results.values())

    for name, passed in results.items():
        status = "✅ ПРОШЛА" if passed else "❌ ПРОВАЛЕНА"
        print(f"{name}: {status}")

    if all_passed:
        print("\n🎉 Все проверки пройдены! Проект готов к работе.")
        return 0
    else:
        print("\n⚠️ Есть проблемы, которые нужно исправить.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
