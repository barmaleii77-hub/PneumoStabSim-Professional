"""
PneumoStabSim - Pneumatic Stabilizer Simulator
Main application entry point with integrated simulation
"""
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import qInstallMessageHandler, QtMsgType, Qt
from PySide6.QtGui import QSurfaceFormat

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


def setup_opengl_format():
    """Setup default OpenGL surface format for maximum compatibility"""
    format = QSurfaceFormat()
    
    # Use OpenGL 3.3 with Compatibility Profile for better driver support
    format.setVersion(3, 3)
    format.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
    
    # Buffers
    format.setDepthBufferSize(24)
    format.setStencilBufferSize(8)
    format.setSamples(4)  # MSAA 4x
    
    # Additional settings for stability
    format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
    format.setSwapInterval(1)  # V-sync
    
    # Set as default BEFORE creating QApplication
    QSurfaceFormat.setDefaultFormat(format)
    
    print(f"OpenGL format set: {format.majorVersion()}.{format.minorVersion()} {format.profile()}")


def main():
    """Main application function"""
    # Initialize logging BEFORE QApplication (P11 requirement)
    logger = init_logging("PneumoStabSim", Path("logs"))
    logger.info("Application starting...")
    
    print("=== PNEUMOSTABSIM STARTING ===")
    
    # CRITICAL: Setup OpenGL format BEFORE QApplication
    print("Step 1: Setting up OpenGL surface format...")
    setup_opengl_format()
    
    print("Step 2: Setting High DPI policy...")
    
    # Enable high DPI support (must be before QApplication)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    print("Step 3: Creating QApplication...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    print("Step 4: Installing Qt message handler...")
    
    # Install Qt message handler
    qInstallMessageHandler(qt_message_handler)
    
    print("Step 5: Setting application properties...")
    
    # Set application properties
    app.setApplicationName("PneumoStabSim")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PneumoStabSim")
    app.setApplicationDisplayName("Pneumatic Stabilizer Simulator")
    
    log_ui_event("APP_CREATED", "Qt application initialized")
    
    print("Step 6: Creating MainWindow...")
    
    try:
        # Create and show main window
        window = MainWindow()
        
        print(f"Step 7: MainWindow created - Size: {window.size().width()}x{window.size().height()}")
        print(f"         Window title: {window.windowTitle()}")
        
        window.show()
        
        print(f"Step 8: Window shown - Visible: {window.isVisible()}")
        print(f"         Position: {window.pos().x()}, {window.pos().y()}")
        
        # Force window to front
        window.raise_()
        window.activateWindow()
        
        log_ui_event("WINDOW_SHOWN", "Main window displayed")
        
        print("\n" + "="*60)
        print("APPLICATION READY - Close window to exit")
        print("Check taskbar or press Alt+Tab if window is not visible")
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