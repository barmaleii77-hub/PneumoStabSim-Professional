#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PneumoStabSim Quick Diagnostic Tool
Утилита для быстрой диагностики проблем с производительностью
"""

import sys
import os
import time
import psutil
from pathlib import Path

def check_system_resources():
    """Проверить системные ресурсы"""
    print("🔍 ПРОВЕРКА СИСТЕМНЫХ РЕСУРСОВ")
    print("=" * 40)
    
    # CPU
    cpu_count = psutil.cpu_count()
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"CPU: {cpu_count} ядер, загрузка: {cpu_percent}%")
    
    # Память
    memory = psutil.virtual_memory()
    print(f"Память: {memory.total // (1024**3)} GB всего, {memory.available // (1024**3)} GB доступно ({memory.percent}% используется)")
    
    # Диск
    disk = psutil.disk_usage('.')
    print(f"Диск: {disk.total // (1024**3)} GB всего, {disk.free // (1024**3)} GB свободно")
    
    # Рекомендации
    if cpu_percent > 80:
        print("⚠️  ВНИМАНИЕ: Высокая загрузка CPU")
    if memory.percent > 80:
        print("⚠️  ВНИМАНИЕ: Мало свободной памяти")
    if disk.free < 1024**3:  # Меньше 1GB
        print("⚠️  ВНИМАНИЕ: Мало свободного места на диске")
    
    print()

def check_python_environment():
    """Проверить Python окружение"""
    print("🐍 ПРОВЕРКА PYTHON ОКРУЖЕНИЯ")
    print("=" * 40)
    
    print(f"Python версия: {sys.version}")
    print(f"Путь к Python: {sys.executable}")
    print(f"Кодировка по умолчанию: {sys.getdefaultencoding()}")
    
    # Проверяем ключевые пакеты
    packages_to_check = [
        'PySide6',
        'psutil',
        'numpy',
        'logging'
    ]
    
    for package in packages_to_check:
        try:
            __import__(package)
            print(f"✅ {package}: установлен")
        except ImportError:
            print(f"❌ {package}: НЕ УСТАНОВЛЕН")
    
    print()

def check_qtquick3d_setup():
    """Проверить настройку QtQuick3D"""
    print("🎨 ПРОВЕРКА QTQUICK3D")
    print("=" * 40)
    
    # Проверяем переменные окружения
    qt_vars = [
        'QML2_IMPORT_PATH',
        'QML_IMPORT_PATH', 
        'QT_PLUGIN_PATH',
        'QT_QML_IMPORT_PATH',
        'QSG_RHI_BACKEND'
    ]
    
    for var in qt_vars:
        value = os.environ.get(var, 'НЕ УСТАНОВЛЕНА')
        print(f"{var}: {value}")
    
    # Проверяем доступность PySide6
    try:
        from PySide6.QtCore import QLibraryInfo
        qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
        print(f"✅ QML Import Path: {qml_path}")
        
        if Path(qml_path).exists():
            print("✅ QML путь существует")
        else:
            print("❌ QML путь не найден")
            
    except ImportError:
        print("❌ PySide6 не доступен")
    
    print()

def check_file_structure():
    """Проверить структуру файлов проекта"""
    print("📁 ПРОВЕРКА СТРУКТУРЫ ПРОЕКТА")
    print("=" * 40)
    
    critical_files = [
        'app.py',
        'src/common.py',
        'src/ui/main_window.py',
        'assets/qml/main.qml',
        'src/ui/panels/panel_graphics.py'
    ]
    
    for file_path in critical_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"✅ {file_path} ({size} bytes)")
        else:
            print(f"❌ {file_path}: НЕ НАЙДЕН")
    
    print()

def check_processes():
    """Проверить запущенные процессы"""
    print("🔄 ПРОВЕРКА ПРОЦЕССОВ")
    print("=" * 40)
    
    # Ищем процессы Python
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            if 'python' in proc.info['name'].lower():
                python_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if python_processes:
        print(f"Найдено {len(python_processes)} Python процессов:")
        for proc in python_processes[:5]:  # Показываем первые 5
            try:
                memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                print(f"  PID {proc.info['pid']}: CPU {proc.info['cpu_percent']}%, Память {memory_mb:.1f}MB")
            except:
                print(f"  PID {proc.info['pid']}: информация недоступна")
    else:
        print("Python процессы не найдены")
    
    print()

def run_quick_diagnostic():
    """Запустить быструю диагностику"""
    print("🚀 PNEUMOSTABSIM QUICK DIAGNOSTIC")
    print("=" * 50)
    print(f"Время: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Рабочая директория: {os.getcwd()}")
    print("=" * 50)
    print()
    
    check_system_resources()
    check_python_environment()
    check_qtquick3d_setup()
    check_file_structure()
    check_processes()
    
    print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("=" * 50)

if __name__ == "__main__":
    try:
        run_quick_diagnostic()
    except KeyboardInterrupt:
        print("\n❌ Диагностика прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при диагностике: {e}")
        import traceback
        traceback.print_exc()
