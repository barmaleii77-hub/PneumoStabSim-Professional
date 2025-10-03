#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive environment check
"""
import sys
import os

print("="*80)
print("COMPREHENSIVE ENVIRONMENT CHECK")
print("="*80)
print()

# 1. Python basics
print("1. PYTHON ENVIRONMENT:")
print(f"   Python version: {sys.version}")
print(f"   Executable: {sys.executable}")
print(f"   Platform: {sys.platform}")
print()

# 2. Critical imports
print("2. CRITICAL IMPORTS:")
critical_imports = [
    "PySide6",
    "PySide6.QtCore", 
    "PySide6.QtWidgets",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets", 
    "PySide6.QtQml",
    "PySide6.QtQuick3D",
    "numpy"
]

for imp in critical_imports:
    try:
        module = __import__(imp, fromlist=[''])
        version = getattr(module, '__version__', 'unknown')
        print(f"   ? {imp:<25} version: {version}")
    except ImportError as e:
        print(f"   ? {imp:<25} ERROR: {e}")

print()

# 3. Qt Quick 3D specific check
print("3. QT QUICK 3D DETAILS:")
try:
    from PySide6.QtQuick3D import QQuick3DGeometry
    print("   ? QQuick3DGeometry imported")
    
    # Check methods
    methods = [m for m in dir(QQuick3DGeometry) if not m.startswith('_')]
    print(f"   ? QQuick3DGeometry methods: {len(methods)}")
    
    # Key methods
    key_methods = ['setVertexData', 'setIndexData', 'addAttribute', 'clear', 'update']
    missing = [m for m in key_methods if m not in methods]
    if missing:
        print(f"   ? Missing methods: {missing}")
    else:
        print("   ? All key methods present")
        
except Exception as e:
    print(f"   ? QtQuick3D error: {e}")

print()

# 4. Environment variables
print("4. ENVIRONMENT VARIABLES:")
qt_vars = {
    'QSG_RHI_BACKEND': os.environ.get('QSG_RHI_BACKEND', 'NOT SET'),
    'QSG_INFO': os.environ.get('QSG_INFO', 'NOT SET'),
    'QT_LOGGING_RULES': os.environ.get('QT_LOGGING_RULES', 'NOT SET'),
    'QT_QPA_PLATFORM': os.environ.get('QT_QPA_PLATFORM', 'NOT SET')
}

for var, value in qt_vars.items():
    print(f"   {var}: {value}")

print()

# 5. Test QApplication creation
print("5. QAPPLICATION TEST:")
try:
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        print("   ? QApplication created")
        
        # Test QML engine
        from PySide6.QtQml import QQmlEngine
        engine = QQmlEngine()
        print("   ? QQmlEngine created")
        
        # Test QtQuick3D import in QML
        from PySide6.QtQml import QQmlComponent
        from PySide6.QtCore import QUrl
        
        test_qml = '''
        import QtQuick
        import QtQuick3D
        Item { }
        '''
        
        component = QQmlComponent(engine)
        component.setData(test_qml.encode('utf-8'), QUrl())
        
        if component.isError():
            print("   ? QML QtQuick3D import failed:")
            for error in component.errors():
                print(f"      {error.toString()}")
        else:
            print("   ? QML QtQuick3D import successful")
            
        app.quit()
    else:
        print("   ? QApplication already exists")
        
except Exception as e:
    print(f"   ? QApplication test failed: {e}")

print()
print("="*80)
print("ENVIRONMENT CHECK COMPLETE")
print("="*80)