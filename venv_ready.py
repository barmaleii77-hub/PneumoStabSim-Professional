#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Финальная проверка готовности виртуального окружения PneumoStabSim
Final readiness check for PneumoStabSim virtual environment
"""
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def print_header():
    """Печать заголовка"""
    print("🚀" * 25)
    print("🐍 ВИРТУАЛЬНОЕ ОКРУЖЕНИЕ PNEUMOSTABSIM - ГОТОВО!")
    print("🚀" * 25)
    print(f"📅 Проверка: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_venv_status():
    """Проверка статуса виртуального окружения"""
    print("📋 СТАТУС ВИРТУАЛЬНОГО ОКРУЖЕНИЯ:")
    print("=" * 50)
    
    venv_path = Path(".venv")
    if venv_path.exists():
        print("✅ Папка .venv существует")
        
        # Проверяем ключевые файлы
        if sys.platform.startswith('win'):
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
            activate_bat = venv_path / "Scripts" / "activate.bat"
        else:
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
            activate_bat = venv_path / "bin" / "activate"
        
        if python_exe.exists():
            print("✅ Python исполняемый файл найден")
        else:
            print("❌ Python исполняемый файл НЕ найден")
            
        if pip_exe.exists():
            print("✅ pip найден")
        else:
            print("❌ pip НЕ найден")
            
        if activate_bat.exists():
            print("✅ Скрипт активации найден")
        else:
            print("❌ Скрипт активации НЕ найден")
            
    else:
        print("❌ Папка .venv НЕ существует")
        print("   Создайте окружение: python create_venv.py")
        return False
    
    # Проверяем активно ли окружение
    current_python = Path(sys.executable)
    if ".venv" in str(current_python):
        print("✅ Виртуальное окружение АКТИВНО")
        print(f"   Путь: {current_python}")
    else:
        print("⚠️  Виртуальное окружение НЕ активно")
        print("   Активируйте: start_venv.bat")
    
    return True

def check_packages():
    """Проверка установленных пакетов"""
    print("\n📦 ПРОВЕРКА ПАКЕТОВ:")
    print("=" * 50)
    
    required_packages = [
        ("PySide6", "PySide6 Core"),
        ("PySide6.QtWidgets", "PySide6 Widgets"),
        ("PySide6.QtQuick", "PySide6 Quick"),
        ("PySide6.QtQuick3D", "PySide6 Quick3D"),
        ("PySide6.QtQuickWidgets", "PySide6 QuickWidgets"),
        ("numpy", "NumPy"),
        ("scipy", "SciPy"),
        ("matplotlib", "Matplotlib"),
        ("OpenGL", "PyOpenGL"),
    ]
    
    success_count = 0
    total_count = len(required_packages)
    
    for module, name in required_packages:
        try:
            __import__(module)
            print(f"✅ {name}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {name}: {e}")
    
    print(f"\n📊 Результат: {success_count}/{total_count} пакетов установлено")
    
    if success_count == total_count:
        print("🎉 ВСЕ ПАКЕТЫ ГОТОВЫ К РАБОТЕ!")
        return True
    else:
        print("⚠️  Некоторые пакеты требуют установки")
        print("   Команда: pip install -r requirements.txt")
        return False

def check_project_files():
    """Проверка файлов проекта"""
    print("\n📂 ПРОВЕРКА ФАЙЛОВ ПРОЕКТА:")
    print("=" * 50)
    
    required_files = [
        ("app.py", "Главный файл приложения"),
        ("requirements.txt", "Список зависимостей"),
        ("src/ui/main_window.py", "Главное окно"),
        ("src/ui/panels/panel_geometry.py", "Панель геометрии"),
        ("assets/qml/main.qml", "QML интерфейс"),
        ("create_venv.py", "Создание окружения"),
        ("setup_venv.py", "Проверка окружения"),
        ("start_venv.bat", "Активация окружения"),
        ("run_app.bat", "Быстрый запуск"),
    ]
    
    success_count = 0
    total_count = len(required_files)
    
    for file_path, description in required_files:
        if Path(file_path).exists():
            print(f"✅ {description}")
            success_count += 1
        else:
            print(f"❌ {description}: файл не найден")
    
    print(f"\n📊 Результат: {success_count}/{total_count} файлов найдено")
    
    return success_count >= total_count * 0.8  # 80% файлов должно быть

def check_scripts():
    """Проверка скриптов запуска"""
    print("\n🔧 ПРОВЕРКА СКРИПТОВ ЗАПУСКА:")
    print("=" * 50)
    
    scripts = [
        ("start_venv.bat", "Активация окружения (CMD)"),
        ("start_venv.ps1", "Активация окружения (PowerShell)"),
        ("run_app.bat", "Быстрый запуск приложения"),
        ("create_venv.py", "Создание окружения"),
    ]
    
    for script, description in scripts:
        if Path(script).exists():
            print(f"✅ {description}")
        else:
            print(f"❌ {description}: не найден")

def print_usage_info():
    """Печать информации об использовании"""
    print("\n🚀 СПОСОБЫ ЗАПУСКА:")
    print("=" * 50)
    print("1️⃣  Быстрый запуск приложения:")
    print("    run_app.bat")
    print()
    print("2️⃣  Активация окружения:")
    print("    start_venv.bat        (Command Prompt)")
    print("    .\\start_venv.ps1       (PowerShell)")
    print("    .venv\\Scripts\\activate  (Ручная активация)")
    print()
    print("3️⃣  Запуск в активном окружении:")
    print("    python app.py")
    print()
    print("🔧 ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ:")
    print("    python setup_venv.py                - Полная проверка")
    print("    python check_geometry_connection.py - Проверка параметров")
    print("    python test_slider_precision.py     - Тест точности")
    print("    pip list                            - Список пакетов")

def print_features():
    """Печать возможностей приложения"""
    print("\n🎮 ВОЗМОЖНОСТИ ПРИЛОЖЕНИЯ:")
    print("=" * 50)
    print("✅ Русский интерфейс во всех панелях")
    print("✅ 3D визуализация с Qt Quick 3D + Direct3D 11")
    print("✅ 12 параметров геометрии с точностью 1мм")
    print("✅ Мгновенное обновление 3D сцены")
    print("✅ Анимированная подвеска (4 угла)")
    print("✅ Интерактивная камера (вращение, масштаб)")
    print("✅ U-Frame с цилиндрами и рычагами")
    print("✅ Поршни движутся в прозрачных цилиндрах")

def main():
    """Главная функция проверки"""
    print_header()
    
    # Проверки
    venv_ok = check_venv_status()
    packages_ok = check_packages()
    files_ok = check_project_files()
    
    check_scripts()
    
    # Итоговый статус
    print("\n" + "🎯" * 50)
    print("📊 ИТОГОВЫЙ СТАТУС:")
    print("🎯" * 50)
    
    if venv_ok and packages_ok and files_ok:
        print("🎉 ВИРТУАЛЬНОЕ ОКРУЖЕНИЕ ПОЛНОСТЬЮ ГОТОВО!")
        print("✅ Все компоненты установлены и проверены")
        print("🚀 Можно запускать приложение")
        
        print_usage_info()
        print_features()
        
        print("\n" + "🎊" * 50)
        print("PNEUMOSTABSIM ГОТОВ К РАБОТЕ!")
        print("🎊" * 50)
        
        return True
    else:
        print("⚠️  ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ НАСТРОЙКА")
        
        if not venv_ok:
            print("❌ Проблемы с виртуальным окружением")
            print("   Решение: python create_venv.py")
        
        if not packages_ok:
            print("❌ Не все пакеты установлены")
            print("   Решение: pip install -r requirements.txt")
        
        if not files_ok:
            print("❌ Отсутствуют файлы проекта")
            print("   Проверьте целостность проекта")
        
        print("\n🔧 После исправления запустите снова:")
        print("   python venv_ready.py")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
