#!/usr/bin/env python3
"""
Universal F5 Launcher для PneumoStabSim Professional
Работает из любой IDE с поддержкой F5
"""
import sys
import os
from pathlib import Path

# Добавляем корневую папку проекта в Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Настройка переменных окружения
os.environ.setdefault("PYTHONPATH", f"{project_root};{project_root / 'src'}")
os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")


def main():
    """Универсальная точка входа для F5 запуска"""

    # Импорт F5 launcher
    try:
        from f5_launch import F5LaunchConfig
    except ImportError:
        print("❌ Не удалось импортировать F5LaunchConfig")
        print("🔧 Запускаем setup_dev.py для настройки окружения...")

        import subprocess

        subprocess.run([sys.executable, "setup_dev.py"], cwd=project_root)

        # Повторная попытка импорта
        try:
            from f5_launch import F5LaunchConfig
        except ImportError:
            print("❌ Критическая ошибка: не удалось настроить окружение")
            return 1

    # Создание launcher instance
    launcher = F5LaunchConfig()

    # Определение режима запуска
    if "--debug" in sys.argv or "-d" in sys.argv:
        print("🐛 Universal F5: Запуск в режиме отладки...")
        process = launcher.launch_debug_mode()
    elif "--safe-mode" in sys.argv or "-s" in sys.argv:
        print("🛡️ Universal F5: Запуск в безопасном режиме...")
        # Safe mode - это обычный запуск с флагом --safe-mode
        if not launcher.setup_environment():
            return 1

        python_exe = launcher.venv_path / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        app_path = launcher.project_root / "app.py"

        import subprocess

        try:
            process = subprocess.Popen(
                [str(python_exe), str(app_path), "--safe-mode"],
                cwd=launcher.project_root,
                env=os.environ.copy(),
            )
        except Exception as e:
            print(f"❌ Ошибка запуска: {e}")
            return 1
    elif "--performance" in sys.argv or "-p" in sys.argv:
        print("⚡ Universal F5: Запуск с мониторингом производительности...")
        if not launcher.setup_environment():
            return 1

        python_exe = launcher.venv_path / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        app_path = launcher.project_root / "app.py"

        import subprocess

        try:
            process = subprocess.Popen(
                [str(python_exe), str(app_path), "--monitor-perf"],
                cwd=launcher.project_root,
                env=os.environ.copy(),
            )
        except Exception as e:
            print(f"❌ Ошибка запуска: {e}")
            return 1
    else:
        print("🚀 Universal F5: Запуск в обычном режиме...")
        process = launcher.launch_normal_mode()

    if not process:
        print("❌ Не удалось запустить приложение")
        return 1

    try:
        # Ожидание завершения процесса
        return_code = process.wait()
        print(f"✅ Приложение завершено с кодом: {return_code}")
        return return_code
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал прерывания...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        return 0


if __name__ == "__main__":
    sys.exit(main())
