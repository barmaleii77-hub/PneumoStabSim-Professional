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
# ОПТИМИЗАЦИЯ: Кэширование системной информации
# =============================================================================

_system_info_cache = {}

def get_cached_system_info():
    """Получить кэшированную системню информацию"""
    global _system_info_cache
    
    if not _system_info_cache:
        # Импортируем qVersion для получения версии Qt
        try:
            from PySide6.QtCore import qVersion
            qt_version = qVersion()
        except:
            qt_version = "unknown"
            
        _system_info_cache = {
            'platform': sys.platform,
            'python_version': sys.version_info,
            'encoding': sys.getdefaultencoding(),
            'terminal_encoding': locale.getpreferredencoding(),
            'qtquick3d_setup': qtquick3d_setup_ok,
            'qt_version': qt_version
        }
    
    return _system_info_cache

# =============================================================================
# CRITICAL: QtQuick3D Environment Setup (BEFORE any Qt imports) - ОПТИМИЗИРОВАННАЯ
# =============================================================================

def setup_qtquick3d_environment():
    """Set up QtQuick3D environment variables before importing Qt - ОПТИМИЗИРОВАННАЯ"""
    
    # Проверяем кэш переменных окружения
    required_vars = ["QML2_IMPORT_PATH", "QML_IMPORT_PATH", "QT_PLUGIN_PATH", "QT_QML_IMPORT_PATH"]
    if all(var in os.environ for var in required_vars):
        print("[CACHE] QtQuick3D environment already configured")
        return True
    
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
        from PySide6.QtCore import qInstallMessageHandler, QtMsgType, Qt, QTimer, qVersion
        
        qt_version = qVersion()
        
        print(f"[OK] PySide6 imported successfully")
        print(f"[INFO] ✅ Qt runtime version: {qt_version}")
        
        # Проверяем версию для ditheringEnabled
        try:
            major, minor = qt_version.split('.')[:2]
            qt_major = int(major)
            qt_minor = int(minor)
            
            if qt_major == 6 and qt_minor >= 10:
                print(f"[INFO] ✅ Qt 6.10+ detected - ditheringEnabled should be available")
            elif qt_major == 6 and qt_minor >= 8:
                print(f"[WARNING] ⚠️ Qt 6.8-6.9 detected - ditheringEnabled may not be available")
            else:
                print(f"[WARNING] ⚠️ Qt version < 6.8 - ExtendedSceneEnvironment features may be limited")
        except (ValueError, IndexError):
            print(f"[WARNING] Could not parse Qt version: {qt_version}")
        
        return QApplication, qInstallMessageHandler, QtMsgType, Qt, QTimer
    except ImportError as e:
        print(f"[ERROR] PySide6 import failed: {e}")
        print("[TIP] Try: pip install --upgrade PySide6")
        
        # Try alternative Qt bindings
        try:
            print("[RETRY] Trying PyQt6 as fallback...")
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import qInstallMessageHandler, QtMsgType, Qt, QTimer, qVersion
            print("[OK] PyQt6 imported as fallback")
            return QApplication, qInstallMessageHandler, QtMsgType, Qt, QTimer
        except ImportError:
            print("[ERROR] No Qt framework available")
            sys.exit(1)

# Import Qt components
QApplication, qInstallMessageHandler, QtMsgType, Qt, QTimer = safe_import_qt()

# =============================================================================
# Project Imports with Error Handling - ОПТИМИЗИРОВАННЫЕ
# =============================================================================

# Критические импорты загружаем сразу
try:
    from src.common import init_logging, log_ui_event
    print("[OK] Core modules imported successfully")
except ImportError as e:
    print(f"[ERROR] Core import error: {e}")
    print("[TIP] Make sure you're running from the project root directory")
    print("[TIP] Check that PYTHONPATH includes the current directory and src/")
    sys.exit(1)

# Опциональный импорт монитора производительности
try:
    from performance_monitor import start_global_monitoring, stop_global_monitoring, print_performance_status, record_frame
    _performance_monitoring_available = True
    print("[OK] Performance monitoring available")
except ImportError:
    _performance_monitoring_available = False
    print("[INFO] Performance monitoring not available (optional)")
    # Создаем пустые функции-заглушки
    def start_global_monitoring(): pass
    def stop_global_monitoring(): pass
    def print_performance_status(): pass
    def record_frame(): pass

# Ленивая загрузка тяжелых модулей
_main_window_module = None
_custom_geometry_module = None

def get_main_window_class():
    """Ленивая загрузка MainWindow класса"""
    global _main_window_module
    if _main_window_module is None:
        try:
            from src.ui.main_window import MainWindow
            _main_window_module = MainWindow
            print("[OK] MainWindow loaded on demand")
        except ImportError as e:
            print(f"[ERROR] MainWindow import error: {e}")
            sys.exit(1)
    return _main_window_module

def get_custom_geometry():
    """Ленивая загрузка кастомных 3D геометрий (опционально)"""
    global _custom_geometry_module
    if _custom_geometry_module is None:
        try:
            from src.ui.custom_geometry import SphereGeometry, CubeGeometry
            _custom_geometry_module = {'SphereGeometry': SphereGeometry, 'CubeGeometry': CubeGeometry}
            print("[OK] Custom 3D geometry types loaded on demand")
        except ImportError:
            print("[INFO] Custom 3D geometry types not available (optional feature)")
            _custom_geometry_module = {}
    return _custom_geometry_module

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
    """Handle Qt log messages with encoding safety - ОПТИМИЗИРОВАННАЯ версия"""
    try:
        # Быстрая проверка на None
        if not message:
            return
            
        # Кэшируем logger для повторного использования
        if not hasattr(qt_message_handler, '_logger'):
            qt_message_handler._logger = logging.getLogger("Qt")
        
        logger = qt_message_handler._logger
        
        # Конвертируем в строку только если необходимо
        msg_str = str(message)
        msg_lower = msg_str.lower()  # Кэшируем lowercase версию
        
        # Оптимизированная проверка QML индикаторов
        if not hasattr(qt_message_handler, '_qml_indicators'):
            qt_message_handler._qml_indicators = {"qml:", "custom sphere", "geometry:", "spheregeometry"}
        
        # Быстрая проверка через множество
        if any(indicator in msg_lower for indicator in qt_message_handler._qml_indicators):
            print(f"[QML DEBUG] {msg_str}")
        elif "js" in msg_lower:
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
        # Fallback для проблем с кодировкой
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
  py app.py --monitor-perf     # Enable performance monitoring
        """
    )
    
    parser.add_argument('--no-block', action='store_true', help='Non-blocking mode')
    parser.add_argument('--test-mode', action='store_true', help='Test mode (auto-close 5s)')
    parser.add_argument('--legacy', action='store_true', help='Use legacy OpenGL')
    parser.add_argument('--debug', action='store_true', help='Enable debug messages')
    parser.add_argument('--safe-mode', action='store_true', help='Safe mode (basic features only)')
    parser.add_argument('--monitor-perf', action='store_true', help='Enable performance monitoring')
    
    return parser.parse_args()

def main():
    """Main application function with enhanced error handling - ОПТИМИЗИРОВАННАЯ версия"""
    global app_instance, window_instance
    
    args = None  # Инициализируем args в начале
    
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Запускаем мониторинг производительности если запрашено
        if args.monitor_perf and _performance_monitoring_available:
            start_global_monitoring()
            print("[PERF] Performance monitoring enabled")
        
        # Получаем кэшированную системную информацию
        sys_info = get_cached_system_info()
        
        # Initialize logging BEFORE QApplication
        logger = init_logging("PneumoStabSim", Path("logs"))
        logger.info("Application starting with enhanced encoding support...")
        
        # Override backend if legacy requested
        use_qml_3d = USE_QML_3D_SCHEMA and not args.legacy and not args.safe_mode
        
        # Определяем версию QML для отображения
        backend_name = "Qt Quick 3D (main.qml v4.9.4 SKYBOX FIX)" if use_qml_3d else "Legacy OpenGL"
        
        # Проверяем версию для ditheringEnabled
        from PySide6.QtCore import qVersion
        qt_version = qVersion()
        major, minor = qt_version.split('.')[:2]
        qt_major = int(major)
        qt_minor = int(minor)
        supports_dithering = qt_major == 6 and qt_minor >= 10
        
        # Оптимизированный вывод информации о запуске
        startup_info = [
            "=" * 60,
            "PNEUMOSTABSIM STARTING - main.qml v4.9.4 SKYBOX FIX",
            "=" * 60,
            f"Visualization backend: {backend_name}",
            f"QML file: main.qml v4.9.4 (SKYBOX FIX - Continuous angle accumulation)",
            f"Qt version: {sys_info['qt_version']} ({qt_major}.{qt_minor})",
            "",
            "🎨 GRAPHICS ARCHITECTURE:",
            f"   ✅ ExtendedSceneEnvironment: Built-in from QtQuick3D.Helpers",
            f"   ✅ Fog: Через объект Fog (Qt 6.10+ API)",
            f"   ✅ Skybox: FIXED v4.9.4 - continuous angle accumulation!",
            f"   ✅ Separate IBL controls: lighting/background/rotation",
            f"   ✅ Procedural geometry quality: segments/rings",
            f"   ✅ All properties verified against Qt Quick 3D docs",
            f"   ✅ Import: import QtQuick3D.Helpers",
            "",
            f"⚙️ RENDERING:",
            f"   Qt RHI Backend: {os.environ.get('QSG_RHI_BACKEND', 'auto')}",
            f"   Dithering support: {'✅ YES (Qt 6.10+)' if supports_dithering else '⚠️ NO (Qt < 6.10)'}",
            f"   Fog support: ✅ YES (Fog object)",
            f"   Python encoding: {sys_info['encoding']}",
            f"   Terminal encoding: {sys_info['terminal_encoding']}",
            f"   QtQuick3D setup: {'[OK]' if sys_info['qtquick3d_setup'] else '[WARNING]'}",
            "",
            "🔧 CRITICAL FIXES v4.9.4:",
            "   ✅ Skybox rotation: COMPLETELY INDEPENDENT from camera",
            "   ✅ probeOrientation uses ONLY iblRotationDeg (user control)",
            "   ✅ Camera yaw does NOT affect skybox orientation AT ALL",
            "   ✅ Skybox and camera are FULLY DECOUPLED",
            "   ✅ REMOVED automatic angle normalization (was causing flips!)",
            "   ✅ Qt interpolates angles correctly without manual clamping",
            "   ✅ Only iblRotationDeg rotates the skybox (any value)",
            "   ✅ emissiveVector typo FIXED → emissiveVector",
            "   ✅ Separate IBL lighting/background controls",
            "   ✅ IBL rotation support (unrestricted angles)",
            "   ✅ Procedural geometry quality (cylinderSegments/Rings)",
            "   ✅ Proper scene hierarchy (worldRoot node)",
            "   ✅ Enhanced environment property mappings",
            "",
            "🎨 VISUAL EFFECTS (ExtendedSceneEnvironment):",
            "   ✅ Fog - through Fog object",
            "   ✅ Bloom/Glow - bright area glow",
            "   ✅ SSAO - ambient occlusion",
            "   ✅ Tonemap - cinematic color grading",
            "   ✅ Lens Flare - light source halos",
            "   ✅ Vignette - edge darkening",
            "   ✅ Depth of Field - depth blur",
            "   ✅ IBL - HDR environment lighting",
            ""
        ]
        
        if supports_dithering:
            startup_info.append("   ✅ Dithering - gradient banding elimination (Qt 6.10+)")
        else:
            startup_info.append("   ⚠️ Dithering not available (requires Qt 6.10+)")
        
        startup_info.extend([
            "",
            "🆕 NEW FEATURES v4.9.4:",
            "   • FIXED: Skybox is NOW COMPLETELY INDEPENDENT from camera!",
            "   • FIXED: Removed automatic angle normalization (was causing 180° flips!)",
            "   • FIXED: probeOrientation now uses ONLY iblRotationDeg",
            "   • FIXED: Qt handles angle interpolation correctly without clamping",
            "   • RESULT: Skybox stays FIXED in world space, camera moves freely",
            "   • USER CONTROL: iblRotationDeg can be any value (Qt wraps it internally)",
            ""
        ])
        
        # Единоразовый вывод всей информации
        print('\n'.join(startup_info))

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
        
        # Set application properties (ASCII-safe) - батч операция
        app_properties = {
            'ApplicationName': "PneumoStabSim",
            'ApplicationVersion': "4.9.4",
            'OrganizationName': "PneumoStabSim",
            'ApplicationDisplayName': "Pneumatic Stabilizer Simulator (v4.9.4 SKYBOX FIX)"
        }
        
        for prop, value in app_properties.items():
            getattr(app, f'set{prop}')(value)
        
        log_ui_event("APP_CREATED", "Qt application initialized with enhanced encoding")
        
        print(f"Step 4: Creating MainWindow (backend: {backend_name})...")
        
        # Ленивая загрузка MainWindow класса
        MainWindow = get_main_window_class()
        window = MainWindow(use_qml_3d=use_qml_3d)
        window_instance = window
        
        print(f"Step 5: MainWindow created - Size: {window.size().width()}x{window.size().height()}")
        
        # Батч операции с окном
        window.show()
        window.raise_()
        window.activateWindow()
        
        log_ui_event("WINDOW_SHOWN", f"Main window displayed ({backend_name})")
        
        # Оптимизированный финальный вывод
        final_info = [
            "\n" + "=" * 60,
            f"APPLICATION READY - {backend_name}",
        ]
        
        if use_qml_3d and not args.safe_mode:
            final_info.append("[FEATURES] 3D visualization, Enhanced IBL, Geometry quality, Full physics simulation")
        else:
            final_info.append("[SAFE MODE] Basic functionality only")
            
        final_info.extend([
            "[ENHANCED] Better encoding, terminal, and compatibility support",
            "[QML] main.qml v4.9.4 (SKYBOX FIX - Continuous angle accumulation)",
            "[QTQUICK3D] Environment variables configured for plugin loading",
            "[FIXES] ✅ Skybox FIXED v4.9.4 ✅ No 180° flip ✅ Continuous rotation",
            "=" * 60 + "\n"
        ])
        
        print('\n'.join(final_info))
        
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
        
        # Handle non-blocking mode - оптимизированный
        if args.no_block:
            print("[NON-BLOCKING] Application starting in background...")
            # Более эффективная инициализация
            for _ in range(125):  # 2 секунды при 16ms интервалах
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
        # Останавлием мониторинг производительности
        if args and hasattr(args, 'monitor_perf') and args.monitor_perf and _performance_monitoring_available:
            print_performance_status()  # Показываем финальную статистику
            stop_global_monitoring()
        print("[CLEANUP] Completed")

if __name__ == "__main__":
    sys.exit(main())
