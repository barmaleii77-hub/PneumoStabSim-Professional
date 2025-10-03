#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test main app with QML logging enabled
"""
import sys
import os
from pathlib import Path

# Enable QML console.log output
os.environ["QSG_RHI_BACKEND"] = "d3d11"
os.environ["QSG_INFO"] = "1"
os.environ["QT_LOGGING_RULES"] = "*.debug=true"
os.environ["QT_ASSUME_STDERR_HAS_CONSOLE"] = "1"

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import qInstallMessageHandler, QtMsgType

from src.common import init_logging, log_ui_event
from src.ui.main_window import MainWindow

# Import custom geometry types
from src.ui.custom_geometry import SphereGeometry, CubeGeometry

def qt_message_handler(mode, context, message):
    """Handle Qt log messages - print all to console"""
    if "Custom sphere" in message or "Geometry:" in message:
        print(f"?? QML: {message}")
    elif "console" in message.lower():
        print(f"?? Console: {message}")
    else:
        # Standard logging
        logger = logging.getLogger("Qt")
        if mode == QtMsgType.QtDebugMsg:
            print(f"DEBUG: {message}")
        elif mode == QtMsgType.QtInfoMsg:
            print(f"INFO: {message}")

def main():
    logger = init_logging("PneumoStabSim", Path("logs"))
    
    print("=== MAIN APP TEST WITH QML LOGGING ===")
    print("Looking for QML console.log messages...")
    print()
    
    app = QApplication(sys.argv)
    qInstallMessageHandler(qt_message_handler)
    
    app.setApplicationName("PneumoStabSim")
    
    try:
        window = MainWindow()
        window.show()
        
        print("\n" + "="*60)
        print("APP RUNNING - Check for QML messages above")
        print("Expected:")
        print("  ?? QML: Custom sphere created")
        print("  ?? QML: Geometry: SphereGeometry(...)")
        print("="*60)
        
        # Run for a few seconds then exit
        import time
        time.sleep(2)
        
        print("\nClosing after 2 seconds...")
        window.close()
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())