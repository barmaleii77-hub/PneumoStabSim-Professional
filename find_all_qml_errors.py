"""
Поиск ВСЕХ оставшихся ошибок QML
"""
import subprocess
import sys
import re


def find_all_qml_errors():
    print("=" * 70)
    print("ПОИСК ВСЕХ ОШИБОК QML")
    print("=" * 70)

    try:
        # Запускаем приложение
        result = subprocess.run(
            [sys.executable, "app.py", "--test-mode"],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace",
        )

        output = result.stdout + result.stderr

        # Ищем все ошибки "Cannot assign"
        cannot_assign_pattern = r'Cannot assign to non-existent property "([^"]+)"'
        cannot_errors = re.findall(cannot_assign_pattern, output)

        # Ищем все QML ошибки
        qml_error_pattern = r"file:///.*\.qml:\d+:\d+: (.+)"
        qml_errors = re.findall(qml_error_pattern, output)

        # Ищем критические ошибки
        critical_pattern = r"\[CRITICAL\] (.+)"
        critical_errors = re.findall(critical_pattern, output)

        print("\n" + "=" * 70)
        print("НАЙДЕННЫЕ ОШИБКИ:")
        print("=" * 70)

        if cannot_errors:
            print(
                f"\n1. НЕСУЩЕСТВУЮЩИЕ СВОЙСТВА ({len(set(cannot_errors))} уникальных):"
            )
            for prop in sorted(set(cannot_errors)):
                print(f"   - {prop}")

        if qml_errors:
            print(f"\n2. QML ОШИБКИ ({len(qml_errors)}):")
            for i, error in enumerate(qml_errors[:10], 1):
                print(f"   {i}. {error}")
            if len(qml_errors) > 10:
                print(f"   ... и ещё {len(qml_errors) - 10} ошибок")

        if critical_errors:
            print(f"\n3. КРИТИЧЕСКИЕ ОШИБКИ ({len(critical_errors)}):")
            for i, error in enumerate(critical_errors[:5], 1):
                print(f"   {i}. {error}")

        # Проверяем успешность запуска
        if "APPLICATION READY" in output:
            print("\n" + "=" * 70)
            print("✅ СТАТУС: Приложение запустилось успешно")
        else:
            print("\n" + "=" * 70)
            print("❌ СТАТУС: Приложение НЕ запустилось")

        # Сохраняем полный лог
        with open("full_qml_log.txt", "w", encoding="utf-8", errors="replace") as f:
            f.write(output)

        print("\n📄 Полный лог сохранён в: full_qml_log.txt")
        print("=" * 70)

        return len(cannot_errors) > 0 or len(critical_errors) > 0

    except subprocess.TimeoutExpired:
        print("\n⏰ TIMEOUT: Приложение не закрылось за 15 секунд")
        return True
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()
        return True


if __name__ == "__main__":
    has_errors = find_all_qml_errors()
    sys.exit(1 if has_errors else 0)
