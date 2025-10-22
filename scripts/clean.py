#!/usr/bin/env python3
"""
Скрипт очистки временных файлов для PneumoStabSim Professional
"""
import shutil
from pathlib import Path


def clean_cache():
    """Очистка Python cache"""
    print("🧹 Очистка Python cache...")

    cache_patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        "**/.pytest_cache",
        "**/.mypy_cache",
        "**/.coverage",
        "**/htmlcov",
        "**/*.egg-info",
    ]

    for pattern in cache_patterns:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                print(f"  Удаление директории: {path}")
                shutil.rmtree(path, ignore_errors=True)
            elif path.is_file():
                print(f"  Удаление файла: {path}")
                path.unlink(missing_ok=True)


def clean_build():
    """Очистка build артефактов"""
    print("🧹 Очистка build артефактов...")

    build_dirs = ["build", "dist", ".eggs"]

    for dir_name in build_dirs:
        path = Path(dir_name)
        if path.exists():
            print(f"  Удаление: {path}")
            shutil.rmtree(path, ignore_errors=True)


def clean_logs():
    """Очистка старых логов (старше 7 дней)"""
    print("🧹 Очистка старых логов...")

    logs_dir = Path("logs")
    if not logs_dir.exists():
        return

    import time

    current_time = time.time()
    week_ago = current_time - (7 * 24 * 60 * 60)  # 7 дней назад

    for log_file in logs_dir.glob("*.log"):
        if log_file.stat().st_mtime < week_ago:
            print(f"  Удаление старого лога: {log_file}")
            log_file.unlink(missing_ok=True)


def clean_temp():
    """Очистка временных файлов"""
    print("🧹 Очистка временных файлов...")

    temp_patterns = [
        "**/*.tmp",
        "**/*.temp",
        "**/Thumbs.db",
        "**/.DS_Store",
        "**/*.rej",  # Файлы отклоненных патчей
        "**/*~",  # Backup файлы
    ]

    for pattern in temp_patterns:
        for path in Path(".").glob(pattern):
            if path.is_file():
                print(f"  Удаление: {path}")
                path.unlink(missing_ok=True)


def main():
    """Основная функция очистки"""
    print("🧹 Очистка проекта PneumoStabSim Professional")
    print("=" * 45)

    clean_cache()
    clean_build()
    clean_logs()
    clean_temp()

    print("=" * 45)
    print("✅ Очистка завершена!")


if __name__ == "__main__":
    main()
