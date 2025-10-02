"""
PneumoStabSim - Pneumatic Stabilizer Simulator
Main application entry point with integrated simulation
"""
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import qInstallMessageHandler, QtMsgType

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
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Install Qt message handler
    qInstallMessageHandler(qt_message_handler)
    
    # Set application properties
    app.setApplicationName("PneumoStabSim")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PneumoStabSim")
    app.setApplicationDisplayName("Pneumatic Stabilizer Simulator")
    
    # Enable high DPI support
    app.setAttribute(app.AA_UseHighDpiPixmaps, True)
    
    log_ui_event("APP_CREATED", "Qt application initialized")
    
    try:
        # Create and show main window
        window = MainWindow()
        window.show()
        
        log_ui_event("WINDOW_SHOWN", "Main window displayed")
        
        # Start event loop
        result = app.exec()
        
        logger.info(f"Application event loop finished with code: {result}")
        return result
        
    except Exception as e:
        logger.critical(f"Fatal error during application execution: {e}")
        import traceback
        logger.critical(traceback.format_exc())
        return 1
    
    finally:
        # Cleanup logging happens automatically via atexit
        pass


if __name__ == "__main__":
    sys.exit(main())