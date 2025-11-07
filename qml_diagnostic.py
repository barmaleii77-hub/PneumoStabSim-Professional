#!/usr/bin/env python3
"""
Диагностика загрузки QML файлов
"""

from pathlib import Path
import os


def main():
    print("🔍 ДИАГНОСТИКА ЗАГРУЗКИ QML ФАЙЛОВ")
    print("=" * 50)

    # Проверяем рабочую директорию
    cwd = os.getcwd()
    print(f"📂 Рабочая директория: {cwd}")

    # Проверяем оба файла
    files = ["assets/qml/main_optimized.qml", "assets/qml/main.qml"]

    for file_path in files:
        path = Path(file_path)
        exists = path.exists()
        print(f"\n📄 {file_path}:")
        print(f"   Существует: {exists}")

        if exists:
            try:
                stat = path.stat()
                print(f"   Размер: {stat.st_size:,} байт")
                print(f"   Полный путь: {path.absolute()}")

                # Проверяем первые строки файла
                with open(path, encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    print(f"   Первая строка: {first_line}")

            except Exception as e:
                print(f"   ❌ Ошибка чтения: {e}")

    # Симулируем логику загрузки из MainWindow
    print("\n🔄 СИМУЛЯЦИЯ ЛОГИКИ ЗАГРУЗКИ:")

    qml_path = Path("assets/qml/main_optimized.qml")
    print(f"1. Проверяем main_optimized.qml: {qml_path.exists()}")

    if not qml_path.exists():
        print("   ⚠️ Оптимизированная версия не найдена, переключаемся на main.qml")
        qml_path = Path("assets/qml/main.qml")

    print(f"2. Итоговый файл для загрузки: {qml_path}")
    print(f"   Существует: {qml_path.exists()}")

    if qml_path.exists():
        print(f"   ✅ Будет загружен: {qml_path.name}")
    else:
        print("   ❌ Файл не найден!")


if __name__ == "__main__":
    main()
