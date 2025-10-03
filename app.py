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

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import qInstallMessageHandler, QtMsgType, Qt

from src.common import init_logging, log_ui_event
from src.ui.main_window import MainWindow


def qt_message_handler(mode, context, message):
    """Handle Qt log messages"""
    logger = logging.getLogger("Qt")
    
    if mode == QtMsgType.QtDebugMsg:
        logger.debug(message)
    elif mode == QtMsgType.QtWarningMsg:
        logger.warning(message)
    elif mode == QtMsgType.QtCriticalMsg:
        logger.error(message)
    elif mode == QtMsgType.QtFatalMsg:
        logger.critical(message)
    elif mode == QtMsgType.QtInfoMsg:
        logger.info(message)


def main():
    """Main application function"""
    # Initialize logging BEFORE QApplication (P11 requirement)
    logger = init_logging("PneumoStabSim", Path("logs"))
    logger.info("Application starting...")
    
    print("=== PNEUMOSTABSIM STARTING ===")
    print("Qt Quick 3D with RHI/Direct3D backend")
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
    
    # Set application properties
    app.setApplicationName("PneumoStabSim")
    app.setApplicationVersion("2.0.0")  # Qt Quick 3D version
    app.setOrganizationName("PneumoStabSim")
    app.setApplicationDisplayName("Pneumatic Stabilizer Simulator")
    
    log_ui_event("APP_CREATED", "Qt application initialized")
    
    print("Step 4: Creating MainWindow...")
    
    try:
        # Create and show main window
        window = MainWindow()
        
        print(f"Step 5: MainWindow created - Size: {window.size().width()}x{window.size().height()}")
        print(f"         Window title: {window.windowTitle()}")
        
        window.show()
        
        print(f"Step 6: Window shown - Visible: {window.isVisible()}")
        print(f"         Position: {window.pos().x()}, {window.pos().y()}")
        
        # Force window to front
        window.raise_()
        window.activateWindow()
        
        log_ui_event("WINDOW_SHOWN", "Main window displayed")
        
        print("\n" + "="*60)
        print("APPLICATION READY - Qt Quick 3D rendering active")
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