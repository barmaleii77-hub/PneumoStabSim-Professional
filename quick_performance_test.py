#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Performance Test
Быстрый тест основной функциональности оптимизированного приложения
"""

import sys
import time
import subprocess


def quick_startup_test():
    """Быстрый тест запуска"""
    print("🚀 Быстрый тест запуска...")

    start_time = time.time()

    try:
        result = subprocess.run(
            ["py", "app.py", "--test-mode"],
            capture_output=True,
            text=True,
            timeout=20,
            encoding="utf-8",
            errors="ignore",
        )

        elapsed = time.time() - start_time

        print(f"   ⏱️  Время запуска: {elapsed:.2f} секунд")
        print(f"   ✅ Код возврата: {result.returncode}")

        if result.returncode == 0:
            print("   🎉 Приложение запустилось успешно!")
            return True
        else:
            print("   ❌ Ошибка запуска:")
            if result.stderr:
                print(f"   STDERR: {result.stderr[-200:]}")
            return False

    except subprocess.TimeoutExpired:
        print("   ❌ Тайм-аут запуска (>20 секунд)")
        return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


def quick_monitoring_test():
    """Быстрый тест мониторинга"""
    print("📈 Быстрый тест мониторинга...")

    try:
        result = subprocess.run(
            ["py", "app.py", "--test-mode", "--monitor-perf"],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="ignore",
        )

        # Проверяем по коду возврата
        success = result.returncode == 0

        print(f"   ✅ Мониторинг протестирован: {success}")

        return success

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


def quick_diagnostic_test():
    """Быстрый тест диагностики"""
    print("🔍 Быстрый тест диагностики...")

    try:
        result = subprocess.run(
            ["py", "diag.py"],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="ignore",
        )

        success = result.returncode == 0
        has_output = len(result.stdout) > 50

        print(f"   ✅ Диагностика работает: {success}")
        print(f"   ✅ Есть вывод: {has_output}")

        return success and has_output

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


def quick_caching_test():
    """Быстрый тест кэширования"""
    print("💾 Быстрый тест кэширования...")

    try:
        # Тестируем кэш системной информации
        result = subprocess.run(
            [
                "py",
                "-c",
                "import app; info1 = app.get_cached_system_info(); info2 = app.get_cached_system_info(); print('Cache works:', bool(info1 and info2 and info1 == info2))",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            encoding="utf-8",
            errors="ignore",
        )

        cache_works = "Cache works: True" in result.stdout

        print(f"   ✅ Кэш работает: {cache_works}")

        return cache_works

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


def main():
    """Главная функция быстрого теста"""
    print("⚡ PNEUMOSTABSIM QUICK PERFORMANCE TEST")
    print("=" * 40)

    tests = [
        ("Запуск приложения", quick_startup_test),
        ("Мониторинг производительности", quick_monitoring_test),
        ("Утилита диагностики", quick_diagnostic_test),
        ("Кэширование", quick_caching_test),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n--- {test_name.upper()} ---")

        try:
            start_time = time.time()
            success = test_func()
            test_time = time.time() - start_time

            results.append((test_name, success, test_time))

            status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
            print(f"   {status} ({test_time:.1f}с)")

        except Exception as e:
            print(f"   ❌ ОШИБКА: {e}")
            results.append((test_name, False, 0))

    # Сводка
    print("\n" + "=" * 40)
    print("📊 СВОДКА БЫСТРОГО ТЕСТА")
    print("=" * 40)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    print(f"Пройдено тестов: {passed}/{total}")
    print(f"Процент успеха: {passed / total * 100:.1f}%")

    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Оптимизации работают корректно")
    else:
        print("⚠️  НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        print("🔧 Требуется дополнительная отладка")

    print("=" * 40)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
