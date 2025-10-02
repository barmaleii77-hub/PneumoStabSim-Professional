"""
PneumoStabSim - Pneumatic Stabilizer Simulator
Main application entry point with integrated simulation
"""
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import qInstallMessageHandler, QtMsgType, QLoggingCategory

from src.ui.main_window import MainWindow


def setup_logging():
    """Setup application logging"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "pneumostabsim.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Get application logger
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    
    return logger


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
    # Setup logging first
    logger = setup_logging()
    logger.info("PneumoStabSim starting...")
    
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
    
    logger.info("Qt application created")
    
    try:
        # Create and show main window
        window = MainWindow()
        window.show()
        
        logger.info("Main window created and shown")
        
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
        logger.info("PneumoStabSim shutting down")


if __name__ == "__main__":
    sys.exit(main())