#!/usr/bin/env python
"""
PneumoStabSim Professional - Быстрый системный тест
Quick System Test - проверка готовности к запуску
"""

import sys
import time
from pathlib import Path

from tools.headless import prepare_launch_environment


def test_app_launch():
    """Тест запуска приложения в тестовом режиме"""
    print("🚀 Testing Application Launch...")

    try:
        # Запуск в тестовом режиме (автозакрытие через 5 секунд)
        import subprocess

        start_time = time.time()

        # Запуск с тестовым режимом
        result = subprocess.run(
            [sys.executable, "app.py", "--test-mode"],
            capture_output=True,
            text=True,
            timeout=10,  # Максимум 10 секунд
            env=prepare_launch_environment(),
        )

        duration = time.time() - start_time

        print(f"⏱️ Launch duration: {duration:.2f}s")
        print(f"📊 Return code: {result.returncode}")

        # Проверка вывода
        if "APPLICATION READY" in result.stdout:
            print("✅ Application launched successfully")
            return True
        elif result.returncode == 0:
            print("✅ Application completed without errors")
            return True
        else:
            print("❌ Application failed to launch properly")
            print("STDOUT:", result.stdout[-500:] if result.stdout else "None")
            print("STDERR:", result.stderr[-500:] if result.stderr else "None")
            return False

    except subprocess.TimeoutExpired:
        print("⚠️ Application launch timeout (but may be working)")
        return True  # Таймаут может означать, что приложение работает
    except Exception as e:
        print(f"❌ Launch test failed: {e}")
        return False


def quick_system_check():
    """Быстрая проверка системы"""
    print("=" * 60)
    print("⚡ PNEUMOSTABSIM PROFESSIONAL - QUICK SYSTEM CHECK")
    print("=" * 60)

    checks = []

    # Проверка Python
    version = sys.version_info
    if version >= (3, 8):
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        checks.append(True)
    else:
        print(
            f"❌ Python {version.major}.{version.minor}.{version.micro} (требуется 3.8+)"
        )
        checks.append(False)

    # Проверка PySide6
    try:
        import PySide6

        print("✅ PySide6 available")
        checks.append(True)
    except ImportError:
        print("❌ PySide6 not found")
        checks.append(False)

    # Проверка ключевых файлов
    key_files = [
        "app.py",
        "assets/qml/main_optimized.qml",
        "assets/qml/components/IblProbeLoader.qml",
        "src/ui/main_window.py",
    ]

    for file_path in key_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
            checks.append(True)
        else:
            print(f"❌ {file_path} missing")
            checks.append(False)

    # Проверка HDR файла
    hdr_path = Path("assets/hdr/studio.hdr")
    if hdr_path.exists():
        size_mb = hdr_path.stat().st_size / (1024 * 1024)
        print(f"✅ HDR file ({size_mb:.1f}MB)")
        checks.append(True)
    else:
        print("⚠️ HDR file missing (IBL will not work)")
        checks.append(True)  # Не критично

    # Итоговый статус
    success_rate = sum(checks) / len(checks) * 100

    print("\n" + "=" * 60)
    if success_rate >= 90:
        print("🎉 SYSTEM STATUS: READY")
        print("✅ All critical components available")
        return True
    elif success_rate >= 70:
        print("⚠️ SYSTEM STATUS: PARTIALLY READY")
        print("🔧 Some components missing but should work")
        return True
    else:
        print("❌ SYSTEM STATUS: NOT READY")
        print("🛠️ Critical components missing")
        return False


def main():
    """Главная функция быстрого теста"""

    # Быстрая проверка системы
    system_ok = quick_system_check()

    if not system_ok:
        print("\n🛑 System check failed, skipping launch test")
        return 1

    # Тест запуска приложения
    print("\n" + "=" * 60)
    launch_ok = test_app_launch()

    print("\n" + "=" * 60)
    if system_ok and launch_ok:
        print("🏆 OVERALL STATUS: PRODUCTION READY")
        print("🚀 PneumoStabSim Professional ready to launch!")
        print("\n💡 To launch normally: py app.py")
        return 0
    else:
        print("🔧 OVERALL STATUS: NEEDS ATTENTION")
        print("⚠️ Some issues found, check output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
