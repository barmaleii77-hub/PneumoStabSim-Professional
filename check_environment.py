#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Диагностика окружения PneumoStabSim
Environment diagnostics for PneumoStabSim
"""
import sys
import os
from pathlib import Path

def check_python_version():
    """Проверка версии Python"""
    print("🐍 PYTHON VERSION CHECK")
    print(f"   Version: {sys.version}")
    print(f"   Executable: {sys.executable}")
    
    if sys.version_info < (3, 8):
        print("   ❌ ERROR: Python 3.8+ required")
        return False
    else:
        print("   ✅ OK: Python version is compatible")
        return True

def check_dependencies():
    """Проверка зависимостей"""
    print("\n📦 DEPENDENCIES CHECK")
    
    required_packages = [
        'PySide6',
        'numpy',
        'scipy',
        'matplotlib',
        'OpenGL'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'OpenGL':
                import OpenGL.GL
                version = "installed"
            else:
                module = __import__(package)
                version = getattr(module, '__version__', 'unknown')
            
            print(f"   ✅ {package}: {version}")
        except ImportError as e:
            print(f"   ❌ {package}: NOT FOUND")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_qt_functionality():
    """Проверка функциональности Qt"""
    print("\n🖼️  QT FUNCTIONALITY CHECK")
    
    try:
        from PySide6.QtCore import QCoreApplication, qVersion
        from PySide6.QtWidgets import QApplication
        from PySide6.QtQuick3D import QQuick3DGeometry
        from PySide6.QtQuickWidgets import QQuickWidget
        
        print(f"   ✅ Qt Version: {qVersion()}")
        print("   ✅ QtCore: OK")
        print("   ✅ QtWidgets: OK")  
        print("   ✅ QtQuick3D: OK")
        print("   ✅ QtQuickWidgets: OK")
        return True
        
    except ImportError as e:
        print(f"   ❌ Qt Import Error: {e}")
        return False

def check_project_structure():
    """Проверка структуры проекта"""
    print("\n📁 PROJECT STRUCTURE CHECK")
    
    required_dirs = [
        'src',
        'src/ui',
        'src/ui/panels',
        'src/ui/widgets',
        'src/common',
        'src/runtime',
        'assets',
        'assets/qml'
    ]
    
    required_files = [
        'app.py',
        'requirements.txt',
        'assets/qml/main.qml',
        'src/ui/main_window.py',
        'src/ui/panels/panel_geometry.py',
        'src/ui/widgets/range_slider.py'
    ]
    
    all_good = True
    
    # Проверка папок
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"   ✅ {dir_path}/")
        else:
            print(f"   ❌ {dir_path}/ - NOT FOUND")
            all_good = False
    
    # Проверка файлов
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - NOT FOUND")
            all_good = False
    
    return all_good

def check_graphics_backend():
    """Проверка графического бэкенда"""
    print("\n🎨 GRAPHICS BACKEND CHECK")
    
    # Проверяем переменные окружения
    rhi_backend = os.environ.get("QSG_RHI_BACKEND", "not set")
    print(f"   QSG_RHI_BACKEND: {rhi_backend}")
    
    if rhi_backend == "d3d11":
        print("   ✅ Direct3D 11 backend configured")
    else:
        print("   ⚠️  Direct3D 11 not explicitly set")
    
    # Проверяем доступность OpenGL
    try:
        import OpenGL.GL as gl
        print("   ✅ OpenGL available")
        return True
    except ImportError:
        print("   ❌ OpenGL not available")
        return False

def run_minimal_test():
    """Запуск минимального теста Qt приложения"""
    print("\n🧪 MINIMAL QT TEST")
    
    try:
        from PySide6.QtWidgets import QApplication, QLabel, QWidget
        from PySide6.QtCore import Qt
        
        app = QApplication([])
        
        # Создаем простое окно
        window = QWidget()
        window.setWindowTitle("PneumoStabSim Environment Test")
        window.resize(300, 200)
        
        label = QLabel("Environment test successful!\nQt is working properly.", window)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setGeometry(50, 50, 200, 100)
        
        window.show()
        
        print("   ✅ Qt application created successfully")
        print("   ✅ Test window should be visible")
        print("   📝 Close the test window to continue...")
        
        app.exec()  # Запускаем на короткое время
        return True
        
    except Exception as e:
        print(f"   ❌ Qt test failed: {e}")
        return False

def main():
    """Основная функция диагностики"""
    print("=" * 60)
    print("🔧 PneumoStabSim Environment Diagnostics")
    print("=" * 60)
    
    # Результаты проверок
    results = {
        'python': check_python_version(),
        'dependencies': check_dependencies(),
        'qt': check_qt_functionality(),
        'structure': check_project_structure(),
        'graphics': check_graphics_backend()
    }
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📋 SUMMARY REPORT")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name.upper():12}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL CHECKS PASSED!")
        print("   Environment is ready for PneumoStabSim")
        print("   You can run: py app.py")
        
        # Предложим запустить минимальный тест
        response = input("\n🧪 Run minimal Qt test? (y/n): ").lower()
        if response == 'y':
            run_minimal_test()
            
    else:
        print("\n⚠️  SOME CHECKS FAILED!")
        print("   Please fix the issues above before running PneumoStabSim")
        print("   Install missing dependencies: py -m pip install -r requirements.txt")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
