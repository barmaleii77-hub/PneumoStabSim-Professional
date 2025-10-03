"""Check if PySide6-Addons (Qt Quick 3D) is installed"""
try:
    from PySide6 import QtQuick, QtQml
    print("? QtQuick available")
    print("? QtQml available")
    
    try:
        from PySide6.QtQuick3D import QQuick3D
        print("? QtQuick3D available")
        print("\n? ALL Qt Quick 3D dependencies satisfied!")
    except ImportError:
        print("? QtQuick3D NOT available")
        print("\nInstall: pip install PySide6-Addons")
        
except ImportError as e:
    print(f"? Qt Quick modules not available: {e}")
    print("\nInstall: pip install PySide6 PySide6-Addons")
