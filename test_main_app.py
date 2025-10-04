#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick diagnostic for main app.py
"""
import sys
import os

# Set RHI backend
os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")
os.environ.setdefault("QSG_INFO", "1")

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    try:
        from PySide6.QtWidgets import QApplication
        print("? PySide6.QtWidgets")
    except Exception as e:
        print(f"? PySide6.QtWidgets: {e}")
        return False
    
    try:
        from src.common import init_logging, log_ui_event
        print("? src.common")
    except Exception as e:
        print(f"? src.common: {e}")
        return False
    
    try:
        from src.ui.main_window import MainWindow
        print("? src.ui.main_window.MainWindow")
    except Exception as e:
        print(f"? src.ui.main_window.MainWindow: {e}")
        return False
    
    try:
        from src.ui.custom_geometry import SphereGeometry, CubeGeometry
        print("? src.ui.custom_geometry")
    except Exception as e:
        print(f"? src.ui.custom_geometry: {e}")
        return False
    
    return True

def test_qml_files():
    """Check QML files exist"""
    from pathlib import Path
    
    qml_files = [
        "assets/qml/UFrameScene.qml",
        "assets/qml/components/Materials.qml", 
        "assets/qml/mech/MechCorner.qml"
    ]
    
    print("\nTesting QML files...")
    all_exist = True
    
    for qml_file in qml_files:
        path = Path(qml_file)
        if path.exists():
            print(f"? {qml_file}")
        else:
            print(f"? {qml_file} - NOT FOUND")
            all_exist = False
    
    return all_exist

def main():
    print("="*60)
    print("MAIN APP DIAGNOSTIC")
    print("="*60)
    
    # Test imports
    if not test_imports():
        print("\n? Import failures - cannot proceed")
        return 1
    
    # Test QML files  
    if not test_qml_files():
        print("\n? Missing QML files - cannot proceed")
        return 1
    
    print("\n? ALL TESTS PASSED")
    print("\nTrying to run app.py...")
    
    try:
        # Import and run main function
        import app
        print("? app.py imported successfully")
        
        # Run main function
        return app.main()
        
    except Exception as e:
        print(f"\n? ERROR running app.py: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())