"""
Детальный анализ запуска приложения
"""
import subprocess
import sys
from pathlib import Path


def analyze_startup():
    """Детальный анализ запуска"""

    print("=" * 70)
    print("ДЕТАЛЬНЫЙ АНАЛИЗ ЗАПУСКА ПРИЛОЖЕНИЯ")
    print("=" * 70)

    log_file = Path("startup_analysis.log")

    print("\n1. Запуск приложения в test-mode...")
    print("   (автозакрытие через 5 секунд)")

    # Запускаем с перенаправлением в файл
    cmd = [sys.executable, "app.py", "--test-mode"]

    try:
        with open(log_file, "w", encoding="utf-8", errors="replace") as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            # Ждём завершения (макс 10 секунд)
            try:
                return_code = process.wait(timeout=10)
                print(f"\n2. Процесс завершился с кодом: {return_code}")
            except subprocess.TimeoutExpired:
                print("\n2. Процесс не завершился за 10 секунд, убиваем...")
                process.kill()
                return_code = -1

        # Читаем лог
        print("\n3. Анализ логов...")

        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        lines = content.split("\n")
        print(f"   Всего строк: {len(lines)}")

        # Статистика
        stats = {"errors": 0, "warnings": 0, "qml_debug": 0, "success_markers": 0}

        error_lines = []
        warning_lines = []
        qml_lines = []
        success_lines = []

        for line in lines:
            line_lower = line.lower()

            # Фильтруем известные безопасные сообщения
            if "sethighdpiscalefactorroundingpolicy" in line_lower:
                continue
            if "charmap" in line_lower:
                continue

            if "error" in line_lower or "fatal" in line_lower:
                stats["errors"] += 1
                error_lines.append(line.strip())
            elif "warning" in line_lower:
                stats["warnings"] += 1
                warning_lines.append(line.strip())
            elif "qml debug" in line_lower or "qml:" in line_lower:
                stats["qml_debug"] += 1
                qml_lines.append(line.strip())

            # Маркеры успеха
            if any(
                marker in line
                for marker in [
                    "APPLICATION READY",
                    "APPLICATION CLOSED",
                    "loaded successfully",
                    "initialized",
                    "created successfully",
                ]
            ):
                stats["success_markers"] += 1
                success_lines.append(line.strip())

        # Выводим статистику
        print("\n" + "=" * 70)
        print("СТАТИСТИКА:")
        print("=" * 70)
        print(f"  Ошибки (Error/Fatal):     {stats['errors']}")
        print(f"  Предупреждения (Warning): {stats['warnings']}")
        print(f"  QML отладка:              {stats['qml_debug']}")
        print(f"  Маркеры успеха:           {stats['success_markers']}")

        # Показываем ошибки
        if error_lines:
            print("\n" + "=" * 70)
            print("ОШИБКИ:")
            print("=" * 70)
            for i, line in enumerate(error_lines[:10], 1):  # Первые 10
                print(f"  {i}. {line[:100]}")
            if len(error_lines) > 10:
                print(f"  ... и ещё {len(error_lines) - 10} ошибок")

        # Показываем предупреждения
        if warning_lines:
            print("\n" + "=" * 70)
            print("ПРЕДУПРЕЖДЕНИЯ (первые 5):")
            print("=" * 70)
            for i, line in enumerate(warning_lines[:5], 1):
                print(f"  {i}. {line[:100]}")

        # Показываем QML отладку
        if qml_lines:
            print("\n" + "=" * 70)
            print("QML ОТЛАДКА (первые 5):")
            print("=" * 70)
            for i, line in enumerate(qml_lines[:5], 1):
                print(f"  {i}. {line[:100]}")

        # Показываем успехи
        if success_lines:
            print("\n" + "=" * 70)
            print("МАРКЕРЫ УСПЕХА:")
            print("=" * 70)
            for i, line in enumerate(success_lines[:10], 1):
                print(f"  {i}. {line[:100]}")

        # Финальная оценка
        print("\n" + "=" * 70)
        print("ФИНАЛЬНАЯ ОЦЕНКА:")
        print("=" * 70)

        if stats["errors"] == 0 and stats["success_markers"] > 5:
            print("✅ УСПЕХ: Приложение запустилось БЕЗ ОШИБОК!")
            print("✅ Все компоненты инициализированы корректно")
            return True
        elif stats["errors"] == 0 and stats["success_markers"] > 0:
            print("⚠️ ЧАСТИЧНЫЙ УСПЕХ: Ошибок нет, но мало маркеров успеха")
            return True
        elif stats["errors"] < 3:
            print("⚠️ ЕСТЬ ПРОБЛЕМЫ: Обнаружены незначительные ошибки")
            return False
        else:
            print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ: Множественные ошибки!")
            return False

    except Exception as e:
        print(f"\n❌ ОШИБКА АНАЛИЗА: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = analyze_startup()
    sys.exit(0 if success else 1)
