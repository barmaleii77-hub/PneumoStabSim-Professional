# -*- coding: utf-8 -*-
"""
PneumoStabSim - Pneumatic Stabilizer Simulator
Main application entry point with Qt Quick 3D rendering (RHI/Direct3D)
"""
import sys
import os
import logging
from pathlib import Path

# CRITICAL: Set Qt Quick RHI backend to Direct3D BEFORE importing PySide6
# This forces Qt to use D3D11 instead of OpenGL on Windows
os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")
os.environ.setdefault("QSG_INFO", "1")  # Print RHI backend info on startup

# DIAGNOSTIC: Enable QML console.log and debug output
os.environ.setdefault("QT_LOGGING_RULES", "js.debug=true;qt.qml.debug=true")
os.environ.setdefault("QT_ASSUME_STDERR_HAS_CONSOLE", "1")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import qInstallMessageHandler, QtMsgType, Qt

from src.common import init_logging, log_ui_event
from src.ui.main_window import MainWindow

# Import custom 3D geometry types (will auto-register via @QmlElement)
from src.ui.custom_geometry import SphereGeometry, CubeGeometry


def qt_message_handler(mode, context, message):
    """Handle Qt log messages"""
    logger = logging.getLogger("Qt")
    
    # DIAGNOSTIC: Show QML console.log messages directly
    if "qml:" in message.lower() or "custom sphere" in message.lower() or "geometry:" in message.lower():
        print(f"?? QML DEBUG: {message}")
    elif "spheregeometry" in message.lower():
        print(f"?? GEOMETRY: {message}")
    elif mode == QtMsgType.QtDebugMsg:
        if "js" in message.lower():
            print(f"?? JS: {message}")
        else:
            logger.debug(message)
    elif mode == QtMsgType.QtWarningMsg:
        print(f"?? WARNING: {message}")
        logger.warning(message)
    elif mode == QtMsgType.QtCriticalMsg:
        print(f"? CRITICAL: {message}")
        logger.error(message)
    elif mode == QtMsgType.QtFatalMsg:
        print(f"?? FATAL: {message}")
        logger.critical(message)
    elif mode == QtMsgType.QtInfoMsg:
        logger.info(message)


def main():
    """Main application function"""
    # Initialize logging BEFORE QApplication (P11 requirement)
    logger = init_logging("PneumoStabSim", Path("logs"))
    logger.info("Application starting...")
    
    print("=== PNEUMOSTABSIM STARTING (Russian UI) ===")
    print("Qt Quick 3D with RHI/Direct3D backend")
    print("Custom 3D Geometry enabled")
    print()
    print("??  IMPORTANT: Look for 'rhi: backend:' line in console output")
    print("    Should show 'D3D11' (not OpenGL)")
    print()
    
    # Enable high DPI support (must be before QApplication)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    print("Step 1: Creating QApplication...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    print("Step 2: Installing Qt message handler...")
    
    # Install Qt message handler
    qInstallMessageHandler(qt_message_handler)
    
    print("Step 3: Setting application properties...")
    
    # Set application properties - using ASCII-safe names
    app.setApplicationName("PneumoStabSim")
    app.setApplicationVersion("2.0.0")  # Qt Quick 3D version
    app.setOrganizationName("PneumoStabSim")
    app.setApplicationDisplayName("Pneumatic Stabilizer Simulator (Russian UI)")
    
    log_ui_event("APP_CREATED", "Qt application initialized")
    
    print("Step 4: Registering custom QML types...")
    print("  - CustomGeometry.SphereGeometry (auto-registered)")
    print("  - CustomGeometry.CubeGeometry (auto-registered)")  
    
    print("Step 5: Creating MainWindow...")
    
    try:
        # Create and show main window
        window = MainWindow()
        
        print(f"Step 6: MainWindow created - Size: {window.size().width()}x{window.size().height()}")
        print(f"         Window title: {window.windowTitle()}")
        
        window.show()
        
        print(f"Step 7: Window shown - Visible: {window.isVisible()}")
        print(f"         Position: {window.pos().x()}, {window.pos().y()}")
        
        # Force window to front
        window.raise_()
        window.activateWindow()
        
        log_ui_event("WINDOW_SHOWN", "Main window displayed")
        
        print("\n" + "="*60)
        print("APPLICATION READY - Qt Quick 3D rendering active (Russian UI)")
        print("?? DIAGNOSTIC: Looking for QML console.log messages...")
        print("Expected: Russian labels in UI panels and 3D scene")
        print("Check console for 'rhi: backend: D3D11' confirmation")
        print("Close window to exit")
        print("="*60 + "\n")
        
        # Start event loop
        result = app.exec()
        
        logger.info(f"Application event loop finished with code: {result}")
        print(f"\n=== APPLICATION CLOSED (code: {result}) ===")
        return result
        
    except Exception as e:
        logger.critical(f"Fatal error during application execution: {e}")
        import traceback
        logger.critical(traceback.format_exc())
        print(f"\n? FATAL ERROR: {e}")
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup logging happens automatically via atexit
        pass


if __name__ == "__main__":
    sys.exit(main())