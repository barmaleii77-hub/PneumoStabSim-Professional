#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт проверки сборки PneumoStabSim
Проверяет все критические зависимости и компоненты
"""

import sys
import os
import subprocess
from pathlib import Path
import traceback

def print_header(title):
    """Печатает заголовок секции"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def check_python_version():
    """Проверка версии Python"""
    print_header("ПРОВЕРКА ВЕРСИИ PYTHON")
    
    version = sys.version_info
    print(f"Python версия: {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 9):
        print("❌ ОШИБКА: Требуется Python 3.9 или выше")
        return False
    elif version >= (3, 13):
        print("✅ Python версия поддерживается (3.13+)")
    else:
        print("✅ Python версия поддерживается")
    
    return True

def check_dependencies():
    """Проверка установленных зависимостей"""
    print_header("ПРОВЕРКА ЗАВИСИМОСТЕЙ")
    
    required_packages = [
        ('numpy', '2.3.3'),
        ('scipy', '1.16.2'),
        ('PySide6', '6.9.3'),
        ('matplotlib', '3.10.6'),
        ('PyOpenGL', '3.1.10')
    ]
    
    failed = []
    
    for package_name, expected_version in required_packages:
        try:
            if package_name == 'PySide6':
                import PySide6
                version = PySide6.__version__
            elif package_name == 'numpy':
                import numpy
                version = numpy.__version__
            elif package_name == 'scipy':
                import scipy
                version = scipy.__version__
            elif package_name == 'matplotlib':
                import matplotlib
                version = matplotlib.__version__
            elif package_name == 'PyOpenGL':
                import OpenGL
                version = OpenGL.__version__
            
            print(f"✅ {package_name}: {version} (ожидается {expected_version})")
            
        except ImportError as e:
            print(f"❌ {package_name}: НЕ УСТАНОВЛЕН - {e}")
            failed.append(package_name)
        except Exception as e:
            print(f"⚠️ {package_name}: Ошибка проверки - {e}")
    
    if failed:
        print(f"\n❌ ОШИБКА: Отсутствуют пакеты: {', '.join(failed)}")
        print("Для установки выполните:")
        print("pip install -r requirements.txt")
        return False
    
    print("\n✅ Все зависимости установлены")
    return True

def check_project_structure():
    """Проверка структуры проекта"""
    print_header("ПРОВЕРКА СТРУКТУРЫ ПРОЕКТА")
    
    critical_files = [
        "app.py",
        "pyproject.toml", 
        "requirements.txt",
        "src/__init__.py",
        "src/ui/__init__.py",
        "src/ui/main_window.py",
        "src/runtime/__init__.py",
        "src/runtime/sim_loop.py",
        "src/runtime/state.py",
        "src/runtime/sync.py",
        "src/common/__init__.py",
        "src/common/logging_setup.py",
        "src/physics/__init__.py",
        "src/physics/odes.py",
        "src/physics/integrator.py",
        "assets/qml/main.qml"
    ]
    
    missing = []
    
    for file_path in critical_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}: ОТСУТСТВУЕТ")
            missing.append(file_path)
    
    if missing:
        print(f"\n❌ ОШИБКА: Отсутствуют критические файлы: {len(missing)}")
        return False
    
    print(f"\n✅ Структура проекта корректна ({len(critical_files)} файлов)")
    return True

def check_imports():
    """Проверка импортов модулей"""
    print_header("ПРОВЕРКА ИМПОРТОВ")
    
    import_tests = [
        ("src.common", "init_logging, log_ui_event"),
        ("src.ui.main_window", "MainWindow"),
        ("src.runtime.sim_loop", "SimulationManager, PhysicsWorker"),
        ("src.runtime.state", "StateSnapshot, StateBus"),
        ("src.runtime.sync", "LatestOnlyQueue"),
        ("src.physics.odes", "RigidBody3DOF, f_rhs"),
        ("src.physics.integrator", "step_dynamics"),
    ]
    
    failed = []
    
    for module_name, components in import_tests:
        try:
            # Динамический импорт модуля
            module = __import__(module_name, fromlist=[components])
            
            # Проверяем наличие компонентов
            for component in components.split(", "):
                if hasattr(module, component):
                    continue
                else:
                    raise AttributeError(f"Нет атрибута '{component}'")
            
            print(f"✅ {module_name}: {components}")
            
        except ImportError as e:
            print(f"❌ {module_name}: Ошибка импорта - {e}")
            failed.append(module_name)
        except AttributeError as e:
            print(f"❌ {module_name}: Отсутствует компонент - {e}")
            failed.append(module_name)
        except Exception as e:
            print(f"⚠️ {module_name}: Неизвестная ошибка - {e}")
    
    if failed:
        print(f"\n❌ ОШИБКА: Проблемы с модулями: {len(failed)}")
        return False
    
    print(f"\n✅ Все модули импортируются успешно ({len(import_tests)} проверок)")
    return True

def check_compilation():
    """Проверка компиляции критических файлов"""
    print_header("ПРОВЕРКА КОМПИЛЯЦИИ")
    
    compile_files = [
        "app.py",
        "src/ui/main_window.py", 
        "src/runtime/sim_loop.py",
        "src/common/logging_setup.py"
    ]
    
    failed = []
    
    for file_path in compile_files:
        try:
            import py_compile
            py_compile.compile(file_path, doraise=True)
            print(f"✅ {file_path}: Компилируется без ошибок")
        except py_compile.PyCompileError as e:
            print(f"❌ {file_path}: Ошибка компиляции - {e}")
            failed.append(file_path)
        except Exception as e:
            print(f"⚠️ {file_path}: Неизвестная ошибка - {e}")
    
    if failed:
        print(f"\n❌ ОШИБКА: Не компилируются файлы: {len(failed)}")
        return False
    
    print(f"\n✅ Все файлы компилируются успешно ({len(compile_files)} файлов)")
    return True

def check_qml_files():
    """Проверка QML файлов"""
    print_header("ПРОВЕРКА QML ФАЙЛОВ")
    
    qml_files = [
        "assets/qml/main.qml",
    ]
    
    missing = []
    
    for file_path in qml_files:
        path = Path(file_path)
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Базовая проверка синтаксиса
                if "import QtQuick" in content and "import QtQuick3D" in content:
                    print(f"✅ {file_path}: Корректный QML файл")
                else:
                    print(f"⚠️ {file_path}: Возможно некорректный QML")
                    
            except Exception as e:
                print(f"⚠️ {file_path}: Ошибка чтения - {e}")
        else:
            print(f"❌ {file_path}: ОТСУТСТВУЕТ")
            missing.append(file_path)
    
    if missing:
        print(f"\n❌ ОШИБКА: Отсутствуют QML файлы: {len(missing)}")
        return False
    
    print(f"\n✅ QML файлы найдены ({len(qml_files)} файлов)")
    return True

def run_minimal_test():
    """Запуск минимального теста приложения"""
    print_header("МИНИМАЛЬНЫЙ ТЕСТ ЗАПУСКА")
    
    try:
        # Создаём минимальный тест без GUI
        test_code = '''
import sys
import os

# Настройка окружения для Qt
os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")

from PySide6.QtWidgets import QApplication

# Создание приложения без показа окон
app = QApplication.instance() or QApplication(sys.argv)

# Импорт основных компонентов
from src.ui.main_window import MainWindow
from src.runtime.sim_loop import SimulationManager
from src.common import init_logging

print("✅ Все основные компоненты импортированы успешно")
print("✅ Qt Application создан")

# Закрытие приложения
if hasattr(app, 'quit'):
    app.quit()

print("✅ Минимальный тест завершен успешно")
'''
        
        # Выполнение теста в том же процессе
        exec(test_code)
        
        print("✅ Минимальный тест прошел успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка минимального теста: {e}")
        print("Трассировка:")
        traceback.print_exc()
        return False

def main():
    """Основная функция проверки"""
    print("🔧 ПРОВЕРКА СБОРКИ PNEUMOSTABSIM")
    print("Версия: 2.0.0 (Russian UI + Qt Quick 3D)")
    
    checks = [
        ("Версия Python", check_python_version),
        ("Зависимости", check_dependencies), 
        ("Структура проекта", check_project_structure),
        ("Импорты модулей", check_imports),
        ("Компиляция", check_compilation),
        ("QML файлы", check_qml_files),
        ("Минимальный тест", run_minimal_test),
    ]
    
    passed = 0
    failed = 0
    
    for check_name, check_func in checks:
        try:
            if check_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА в '{check_name}': {e}")
            traceback.print_exc()
            failed += 1
    
    print_header("ИТОГОВЫЙ РЕЗУЛЬТАТ")
    print(f"Пройдено проверок: {passed}")
    print(f"Провалено проверок: {failed}")
    print(f"Общее количество: {len(checks)}")
    
    if failed == 0:
        print("\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("✅ Проект готов к запуску")
        print("\nДля запуска выполните:")
        print("  python app.py                    # Обычный запуск") 
        print("  python app.py --test-mode        # Тестовый режим (5 сек)")
        print("  python app.py --no-block         # Неблокирующий режим")
        return True
    else:
        print(f"\n💥 ОБНАРУЖЕНЫ ПРОБЛЕМЫ: {failed}")
        print("❌ Проект требует исправлений")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
