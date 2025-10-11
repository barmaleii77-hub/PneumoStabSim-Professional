# -*- coding: utf-8 -*-
"""
PneumoStabSim - Pneumatic Stabilizer Simulator
Main application entry point with enhanced encoding and terminal support
"""
import sys
import os
import locale
import logging
import signal
import argparse
import time
from pathlib import Path

# =============================================================================
# CRITICAL: QtQuick3D Environment Setup (BEFORE any Qt imports)
# =============================================================================

def setup_qtquick3d_environment():
    """Set up QtQuick3D environment variables before importing Qt"""
    try:
        # First, do a minimal import to get Qt paths
        import importlib.util
        spec = importlib.util.find_spec("PySide6.QtCore")
        if spec is None:
            print("[ERROR] PySide6 not found!")
            return False
            
        # Now import and get paths
        from PySide6.QtCore import QLibraryInfo
        
        # Get Qt paths
        qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
        plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
        
        # Set critical environment variables for QtQuick3D
        qtquick3d_env = {
            "QML2_IMPORT_PATH": str(qml_path),
            "QML_IMPORT_PATH": str(qml_path),
            "QT_PLUGIN_PATH": str(plugins_path),
            "QT_QML_IMPORT_PATH": str(qml_path),
        }
        
        for var, value in qtquick3d_env.items():
            os.environ[var] = value
        
        print("[OK] QtQuick3D environment configured:")
        print(f"   QML2_IMPORT_PATH = {qml_path}")
        print(f"   QT_PLUGIN_PATH = {plugins_path}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to setup QtQuick3D environment: {e}")
        return False

# Setup QtQuick3D environment BEFORE any other imports
print("[SETUP] Setting up QtQuick3D environment...")
qtquick3d_setup_ok = setup_qtquick3d_environment()
if qtquick3d_setup_ok:
    print("[OK] QtQuick3D environment setup completed")
else:
    print("[WARNING] QtQuick3D environment setup failed, continuing anyway...")

# =============================================================================
# CRITICAL: Terminal and Encoding Configuration
# =============================================================================

def configure_terminal_encoding():
    """Configure terminal encoding for cross-platform Unicode support"""
    
    # Set UTF-8 encoding for Python I/O
    if sys.platform == 'win32':
        try:
            # Try to set console to UTF-8 on Windows
            import subprocess
            subprocess.run(['chcp', '65001'], capture_output=True, check=False)
        except:
            pass
        
        # Force UTF-8 encoding for stdout/stderr
        try:
            import codecs
            
            # Wrap stdout/stderr with UTF-8 codec
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
            if hasattr(sys.stderr, 'buffer'):    
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')
            
            print("[OK] Windows UTF-8 encoding configured")
        except Exception as e:
            print(f"[WARNING] UTF-8 setup warning: {e}")
    
    # Set environment variables for Python encoding
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    
    # Try to set locale to UTF-8
    try:
        if sys.platform == 'win32':
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        else:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'C')
        except locale.Error:
            pass  # Use system default

# Configure encoding before any other imports
configure_terminal_encoding()

# =============================================================================
# Python Version Compatibility Check
# =============================================================================

def check_python_compatibility():
    """Check Python version and warn about potential issues"""
    version = sys.version_info
    
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 8):
        print("[ERROR] Python 3.8+ required. Please upgrade Python.")
        sys.exit(1)
    elif version >= (3, 12):
        print("[WARNING] Python 3.12+ detected. Some packages may have compatibility issues.")
        print("   Recommended: Python 3.8 - 3.11 for optimal stability")
    elif version >= (3, 11):
        print("[INFO] Python 3.11+ detected. Most packages should work correctly.")
    else:
        print("[OK] Python version is optimal for this project.")

check_python_compatibility()

# =============================================================================
# Qt and Graphics Backend Configuration  
# =============================================================================

# Set Qt Quick RHI backend before importing PySide6
os.environ.setdefault("QSG_RHI_BACKEND", "d3d11" if sys.platform == 'win32' else "opengl")
os.environ.setdefault("QSG_INFO", "1")

# Enhanced Qt debug output with encoding safety
os.environ.setdefault("QT_LOGGING_RULES", "js.debug=true;qt.qml.debug=true")
os.environ.setdefault("QT_ASSUME_STDERR_HAS_CONSOLE", "1")

# Qt High DPI and scaling settings
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

# =============================================================================
# Safe Import with Error Handling
# =============================================================================

def safe_import_qt():
    """Safely import Qt components with fallback options"""
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import qInstallMessageHandler, QtMsgType, Qt, QTimer
        print("[OK] PySide6 imported successfully")
        return QApplication, qInstallMessageHandler, QtMsgType, Qt, QTimer
    except ImportError as e:
        print(f"[ERROR] PySide6 import failed: {e}")
        print("[TIP] Try: pip install --upgrade PySide6")
        
        # Try alternative Qt bindings
        try:
            print("[RETRY] Trying PyQt6 as fallback...")
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import qInstallMessageHandler, QtMsgType, Qt, QTimer
            print("[OK] PyQt6 imported as fallback")
            return QApplication, qInstallMessageHandler, QtMsgType, Qt, QTimer
        except ImportError:
            print("[ERROR] No Qt framework available")
            sys.exit(1)

# Import Qt components
QApplication, qInstallMessageHandler, QtMsgType, Qt, QTimer = safe_import_qt()

# =============================================================================
# Project Imports with Error Handling
# =============================================================================

try:
    from src.common import init_logging, log_ui_event
    from src.ui.main_window import MainWindow
    print("[OK] Project modules imported successfully")
except ImportError as e:
    print(f"[ERROR] Project import error: {e}")
    print("[TIP] Make sure you're running from the project root directory")
    print("[TIP] Check that PYTHONPATH includes the current directory and src/")
    sys.exit(1)

# Try to import custom 3D geometry types (optional)
try:
    from src.ui.custom_geometry import SphereGeometry, CubeGeometry
    print("[OK] Custom 3D geometry types imported")
except ImportError:
    print("[INFO] Custom 3D geometry types not available (optional feature)")

# =============================================================================
# Application Logic
# =============================================================================

USE_QML_3D_SCHEMA = True
app_instance = None
window_instance = None

def signal_handler(signum, frame):
    """Handle Ctrl+C and other signals gracefully"""
    global app_instance, window_instance
    
    try:
        print(f"\n[SIGNAL] Signal {signum} received, shutting down gracefully...")
        
        if window_instance:
            print("   Closing main window...")
            window_instance.close()
        
        if app_instance:
            print("   Terminating Qt event loop...")
            app_instance.quit()
        
        print("[OK] Application terminated gracefully")
    except Exception as e:
        print(f"[WARNING] Error during shutdown: {e}")

def qt_message_handler(mode, context, message):
    """Handle Qt log messages with encoding safety"""
    try:
        logger = logging.getLogger("Qt")
        
        # Safe string conversion
        msg_str = str(message) if message else ""
        
        # Enhanced QML debug output detection
        qml_indicators = ["qml:", "custom sphere", "geometry:", "spheregeometry"]
        if any(indicator in msg_str.lower() for indicator in qml_indicators):
            print(f"[QML DEBUG] {msg_str}")
        elif "js" in msg_str.lower():
            print(f"[JS] {msg_str}")
        elif mode == QtMsgType.QtDebugMsg:
            logger.debug(msg_str)
        elif mode == QtMsgType.QtWarningMsg:
            print(f"[WARNING] {msg_str}")
            logger.warning(msg_str)
        elif mode == QtMsgType.QtCriticalMsg:
            print(f"[CRITICAL] {msg_str}")
            logger.error(msg_str)
        elif mode == QtMsgType.QtFatalMsg:
            print(f"[FATAL] {msg_str}")
            logger.critical(msg_str)
        elif mode == QtMsgType.QtInfoMsg:
            logger.info(msg_str)
            
    except Exception as e:
        # Fallback for encoding issues
        print(f"Qt message handler error: {e}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="PneumoStabSim - Pneumatic Stabilizer Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py app.py                    # Main Qt Quick 3D version (main.qml)
  py app.py --no-block         # Non-blocking mode
  py app.py --test-mode        # Test mode (auto-close 5s)
  py app.py --legacy           # Use legacy OpenGL
  py app.py --debug            # Debug mode
  py app.py --safe-mode        # Safe mode (minimal features)
        """
    )
    
    parser.add_argument('--no-block', action='store_true', help='Non-blocking mode')
    parser.add_argument('--test-mode', action='store_true', help='Test mode (auto-close 5s)')
    parser.add_argument('--legacy', action='store_true', help='Use legacy OpenGL')
    parser.add_argument('--debug', action='store_true', help='Enable debug messages')
    parser.add_argument('--safe-mode', action='store_true', help='Safe mode (basic features only)')
    
    return parser.parse_args()

def main():
    """Main application function with enhanced error handling"""
    global app_instance, window_instance
    
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Initialize logging BEFORE QApplication
        logger = init_logging("PneumoStabSim", Path("logs"))
        logger.info("Application starting with enhanced encoding support...")
        
        # Override backend if legacy requested
        use_qml_3d = USE_QML_3D_SCHEMA and not args.legacy and not args.safe_mode
        
        # Определяем версию QML для отображения
        backend_name = "Qt Quick 3D (main.qml v4.6)" if use_qml_3d else "Legacy OpenGL"
        
        print("=" * 60)
        print("PNEUMOSTABSIM STARTING (IBL SkyBox Background v4.8)")
        print("=" * 60)
        print(f"Visualization backend: {backend_name}")
        print(f"QML file: main.qml (единый файл с IBL окружением v4.8)")
        print(f"Qt RHI Backend: {os.environ.get('QSG_RHI_BACKEND', 'auto')}")
        print(f"Python encoding: {sys.getdefaultencoding()}")
        print(f"Terminal encoding: {locale.getpreferredencoding()}")
        print(f"QtQuick3D setup: {'[OK]' if qtquick3d_setup_ok else '[WARNING]'}")
        print()
        print("🎨 IBL ОКРУЖЕНИЕ:")
        print("   ✅ SkyBox фон из HDR файла")
        print("   ✅ IBL освещение от HDR")
        print("   ✅ Фон вращается с камерой (SkyBox)")
        print("   ✅ Плавные переходы при загрузке")
        print("   ✅ Fallback к простому цвету если HDR не загружен")
        print()

        # Enable high DPI support (must be called BEFORE QApplication)
        try:
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
        except Exception as e:
            print(f"[WARNING] High DPI setup warning: {e}")
        
        print("Step 1: Creating QApplication...")
        
        # Create Qt application
        app = QApplication(sys.argv)
        app_instance = app
        
        print("Step 2: Installing Qt message handler...")
        qInstallMessageHandler(qt_message_handler)
        
        print("Step 3: Setting application properties...")
        
        # Set application properties (ASCII-safe)
        app.setApplicationName("PneumoStabSim")
        app.setApplicationVersion("4.3.0")
        app.setOrganizationName("PneumoStabSim")
        app.setApplicationDisplayName("Pneumatic Stabilizer Simulator (v4.3)")
        
        log_ui_event("APP_CREATED", "Qt application initialized with enhanced encoding")
        
        print(f"Step 4: Creating MainWindow (backend: {backend_name})...")
        
        # Create and show main window - убираем force_optimized параметр
        window = MainWindow(use_qml_3d=use_qml_3d)
        window_instance = window
        
        print(f"Step 5: MainWindow created - Size: {window.size().width()}x{window.size().height()}")
        
        window.show()
        window.raise_()
        window.activateWindow()
        
        log_ui_event("WINDOW_SHOWN", f"Main window displayed ({backend_name})")
        
        print("\n" + "=" * 60)
        print(f"APPLICATION READY - {backend_name}")
        if use_qml_3d and not args.safe_mode:
            print("[FEATURES] 3D visualization, IBL support, full parameter control, physics simulation")
        else:
            print("[SAFE MODE] Basic functionality only")
        print("[ENHANCED] Better encoding, terminal, and compatibility support")
        print("[QML] main.qml (единый файл с полной функциональностью v4.3)")
        print("[QTQUICK3D] Environment variables configured for plugin loading")
        print("=" * 60 + "\n")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
        
        # Setup auto-close for test mode
        if args.test_mode:
            close_timer = QTimer()
            close_timer.setSingleShot(True)
            close_timer.timeout.connect(lambda: [
                print("[TEST MODE] Auto-closing..."),
                window.close()
            ])
            close_timer.start(5000)
        
        # Handle non-blocking mode
        if args.no_block:
            print("[NON-BLOCKING] Application starting in background...")
            # Brief initialization period
            start_time = time.time()
            while time.time() - start_time < 2.0:
                app.processEvents()
                time.sleep(0.016)
            
            print("[OK] Application running in background")
            print("    Window should be visible and responsive")
            return 0
        
        # Standard event loop
        print("[STARTING] Application event loop...")
        result = app.exec()
        
        logger.info(f"Application event loop finished with code: {result}")
        print(f"\n=== APPLICATION CLOSED (code: {result}) ===")
        return result
        
    except Exception as e:
        error_msg = f"Fatal error during application execution: {e}"
        if 'logger' in locals():
            logger.critical(error_msg)
        
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        print("[CLEANUP] Completed")

if __name__ == "__main__":
    sys.exit(main())
