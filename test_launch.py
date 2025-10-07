#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест различных режимов запуска PneumoStabSim
"""
import subprocess
import sys
import time

def test_import():
    """Проверяем, что импорты работают"""
    print("🔍 Тестирование импортов...")
    try:
        result = subprocess.run([
            sys.executable, "-c", 
            "from src.common import init_logging; print('✅ Импорты работают')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Импорты работают")
            return True
        else:
            print(f"❌ Ошибка импорта: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Ошибка тестирования импортов: {e}")
        return False

def test_help():
    """Проверяем справку"""
    print("\n🔍 Тестирование справки...")
    try:
        result = subprocess.run([
            sys.executable, "app.py", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "PneumoStabSim" in result.stdout:
            print("✅ Справка работает")
            return True
        else:
            print(f"❌ Ошибка справки: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Ошибка тестирования справки: {e}")
        return False

def test_test_mode():
    """Проверяем тестовый режим"""
    print("\n🔍 Тестирование test-mode...")
    try:
        start_time = time.time()
        result = subprocess.run([
            sys.executable, "app.py", "--test-mode"
        ], capture_output=True, text=True, timeout=15)
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0 and elapsed < 10:
            print(f"✅ Тестовый режим работает ({elapsed:.1f}s)")
            return True
        else:
            print(f"❌ Ошибка тестового режима: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Тестовый режим завис (превышен таймаут)")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования test-mode: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ РЕЖИМОВ ЗАПУСКА PNEUMOSTABSIM")
    print("=" * 60)
    
    tests = [
        ("Импорты", test_import),
        ("Справка", test_help),
        ("Тестовый режим", test_test_mode),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"   ⚠️ {name} не прошел тест")
        except KeyboardInterrupt:
            print(f"\n🛑 Тестирование прервано пользователем")
            break
        except Exception as e:
            print(f"   ❌ {name}: Исключение - {e}")
    
    print("\n" + "=" * 60)
    print(f"РЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("   Приложение готово к использованию")
        print("   Попробуйте: python launch.py --no-block")
    elif passed >= total // 2:
        print("⚠️ БОЛЬШИНСТВО ТЕСТОВ ПРОЙДЕНО")
        print("   Приложение скорее всего работает")
        print("   Попробуйте: python app.py --test-mode")
    else:
        print("❌ МНОГО ТЕСТОВ НЕ ПРОЙДЕНО")
        print("   Проверьте установку зависимостей")
        print("   Возможно нужно: pip install -r requirements.txt")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
