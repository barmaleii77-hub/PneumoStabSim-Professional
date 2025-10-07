#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher script for PneumoStabSim
Provides convenient ways to launch the application
"""
import sys
import os
import subprocess
import time

def print_help():
    """Print help information"""
    print("🚀 PneumoStabSim Launcher")
    print("=" * 50)
    print()
    print("Доступные команды:")
    print()
    print("  python launch.py                    # Обычный запуск (блокирует терминал)")
    print("  python launch.py --no-block        # Неблокирующий запуск")
    print("  python launch.py --test            # Тестовый режим (5 сек)")
    print("  python launch.py --legacy          # Legacy OpenGL режим")
    print("  python launch.py --debug           # С отладкой")
    print("  python launch.py --help            # Эта справка")
    print()
    print("Комбинированные команды:")
    print("  python launch.py --no-block --debug  # Неблокирующий + отладка")
    print("  python launch.py --test --legacy     # Тест + legacy OpenGL")
    print()
    print("Прямой запуск (то же самое):")
    print("  python app.py --no-block           # Напрямую через app.py")
    print()
    print("💡 Советы:")
    print("  - Используйте --no-block если не хотите блокировать терминал")
    print("  - Используйте --test для быстрой проверки запуска")
    print("  - Используйте --legacy если Qt Quick 3D не работает")
    print("  - Ctrl+C для принудительного завершения")

def main():
    """Main launcher function"""
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        return 0
    
    # Build command
    cmd = [sys.executable, "app.py"]
    
    # Pass through all arguments except our own
    args = [arg for arg in sys.argv[1:] if arg not in ["--help", "-h"]]
    cmd.extend(args)
    
    # Special handling for convenience
    if "--test" in args:
        # Replace --test with --test-mode for app.py
        cmd = [arg if arg != "--test" else "--test-mode" for arg in cmd]
    
    print("🚀 Запуск PneumoStabSim...")
    print(f"   Команда: {' '.join(cmd)}")
    print()
    
    try:
        # Launch the application
        if "--no-block" in args:
            # Non-blocking launch
            print("🔓 Неблокирующий запуск...")
            process = subprocess.Popen(cmd)
            print(f"✅ Приложение запущено с PID {process.pid}")
            print("   Терминал свободен для других команд")
            print("   Для остановки приложения закройте окно или используйте диспетчер задач")
            return 0
        else:
            # Blocking launch
            print("🔒 Блокирующий запуск...")
            result = subprocess.run(cmd)
            return result.returncode
            
    except KeyboardInterrupt:
        print("\n🛑 Прервано пользователем (Ctrl+C)")
        return 1
    except FileNotFoundError:
        print("❌ Ошибка: Не найден app.py")
        print("   Убедитесь, что вы запускаете скрипт из корневой папки проекта")
        return 1
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
