"""
Анализ QML ошибок без эмодзи
"""
import subprocess
import sys
import re


def run_app_and_analyze():
    """Запустить приложение и проанализировать вывод"""

    print("=" * 60)
    print("АНАЛИЗ QML ОШИБОК")
    print("=" * 60)

    # Запускаем приложение
    try:
        result = subprocess.run(
            [sys.executable, "app.py", "--test-mode"],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace",
        )

        output = result.stdout + result.stderr

        # Ищем ошибки
        error_patterns = [
            r"(?i)error",
            r"(?i)critical",
            r"(?i)fatal",
            r"(?i)cannot",
            r"(?i)failed",
            r"(?i)warning.*qml",
        ]

        errors_found = []

        for line in output.split("\n"):
            for pattern in error_patterns:
                if re.search(pattern, line):
                    # Фильтруем известные безопасные предупреждения
                    if "setHighDpiScaleFactorRoundingPolicy" in line:
                        continue
                    if "charmap" in line:
                        continue

                    errors_found.append(line.strip())
                    break

        print(f"\nОбщее количество строк вывода: {len(output.split(chr(10)))}")
        print(f"Найдено потенциальных ошибок/предупреждений: {len(errors_found)}")

        if errors_found:
            print("\n" + "=" * 60)
            print("НАЙДЕННЫЕ ПРОБЛЕМЫ:")
            print("=" * 60)
            for i, error in enumerate(errors_found, 1):
                print(f"{i}. {error}")
        else:
            print("\n" + "=" * 60)
            print("РЕЗУЛЬТАТ: БЕЗ КРИТИЧЕСКИХ ОШИБОК!")
            print("=" * 60)

        # Проверяем успешность запуска
        if "APPLICATION READY" in output:
            print("\nSTATUS: Приложение запустилось успешно")

        if "APPLICATION CLOSED (code: 0)" in output:
            print("SHUTDOWN: Приложение закрылось корректно")

        # Проверяем QML загрузку
        if (
            "QML файл загружен успешно" in output
            or "main.qml loaded successfully" in output
        ):
            print("QML: Файл загружен успешно")

        return len(errors_found) == 0

    except subprocess.TimeoutExpired:
        print("TIMEOUT: Приложение не закрылось за 15 секунд (ожидаемо в test-mode)")
        return False
    except Exception as e:
        print(f"ОШИБКА: {e}")
        return False


if __name__ == "__main__":
    success = run_app_and_analyze()
    sys.exit(0 if success else 1)
