# -*- coding: utf-8 -*-
"""
PneumoStabSim - Pneumatic Stabilizer Simulator
Main application entry point with Qt Quick 3D rendering (RHI/Direct3D)
"""
import sys
import os
import logging
import signal
import argparse
import time
from pathlib import Path

# CRITICAL: Force UTF-8 encoding for stdout to handle emoji in Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

# ========== VISUALIZATION BACKEND SWITCH ==========
USE_QML_3D_SCHEMA = True  # True: Qt Quick 3D U-Frame, False: legacy OpenGL widget

# CRITICAL: Set Qt Quick RHI backend to Direct3D BEFORE importing PySide6
# This forces Qt to use D3D11 instead of OpenGL on Windows
os.environ.setdefault("QSG_RHI_BACKEND", "d3d11")
os.environ.setdefault("QSG_INFO", "1")  # Print RHI backend info on startup

# DIAGNOSTIC: Enable QML console.log and debug output
os.environ.setdefault("QT_LOGGING_RULES", "js.debug=true;qt.qml.debug=true")
os.environ.setdefault("QT_ASSUME_STDERR_HAS_CONSOLE", "1")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import qInstallMessageHandler, QtMsgType, Qt, QTimer

from src.common import init_logging, log_ui_event
from src.ui.main_window import MainWindow

# Import custom 3D geometry types (will auto-register via @QmlElement)
from src.ui.custom_geometry import SphereGeometry, CubeGeometry

# Global reference for signal handling
app_instance = None
window_instance = None


def signal_handler(signum, frame):
    """Handle Ctrl+C and other signals gracefully"""
    global app_instance, window_instance
    
    print(f"\n🛑 Получен сигнал {signum}, закрываем приложение...")
    
    if window_instance:
        print("   Закрываем главное окно...")
        window_instance.close()
    
    if app_instance:
        print("   Завершаем Qt event loop...")
        app_instance.quit()
    
    print("✅ Приложение завершено gracefully")


def qt_message_handler(mode, context, message):
    """Handle Qt log messages"""
    logger = logging.getLogger("Qt")
    
    # DIAGNOSTIC: Show QML console.log messages directly
    if "qml:" in message.lower() or "custom sphere" in message.lower() or "geometry:" in message.lower():
        print(f"🔍 QML DEBUG: {message}")
    elif "spheregeometry" in message.lower():
        print(f"🔍 GEOMETRY: {message}")
    elif mode == QtMsgType.QtDebugMsg:
        if "js" in message.lower():
            print(f"🔍 JS: {message}")
        else:
            logger.debug(message)
    elif mode == QtMsgType.QtWarningMsg:
        print(f"⚠️ WARNING: {message}")
        logger.warning(message)
    elif mode == QtMsgType.QtCriticalMsg:
        print(f"❌ CRITICAL: {message}")
        logger.error(message)
    elif mode == QtMsgType.QtFatalMsg:
        print(f"💀 FATAL: {message}")
        logger.critical(message)
    elif mode == QtMsgType.QtInfoMsg:
        logger.info(message)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="PneumoStabSim - Pneumatic Stabilizer Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python app.py                    # Обычный запуск (блокирует терминал)
  python app.py --no-block         # Неблокирующий запуск (не блокирует терминал)
  python app.py --test-mode        # Тестовый режим (автозакрытие через 5 сек)
  python app.py --legacy           # Использовать legacy OpenGL вместо Qt Quick 3D
  python app.py --debug            # Включить отладочные сообщения
        """
    )
    
    parser.add_argument(
        '--no-block', 
        action='store_true',
        help='Запустить в неблокирующем режиме (не блокирует терминал)'
    )
    
    parser.add_argument(
        '--test-mode',
        action='store_true', 
        help='Тестовый режим (автозакрытие через 5 секунд)'
    )
    
    parser.add_argument(
        '--legacy',
        action='store_true',
        help='Использовать legacy OpenGL вместо Qt Quick 3D'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Включить отладочные сообщения'
    )
    
    return parser.parse_args()


def main():
    """Main application function"""
    global app_instance, window_instance
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Initialize logging BEFORE QApplication (P11 requirement)
    logger = init_logging("PneumoStabSim", Path("logs"))
    logger.info("Application starting...")
    
    # Override backend if legacy requested
    use_qml_3d = USE_QML_3D_SCHEMA and not args.legacy
    backend_name = "Qt Quick 3D (U-Frame PBR)" if use_qml_3d else "Legacy OpenGL"
    
    print("=== PNEUMOSTABSIM STARTING (Russian UI) ===")
    print(f"Visualization backend: {backend_name}")
    print("Qt Quick RHI: Direct3D 11")
    print("Custom 3D Geometry enabled")
    
    if args.no_block:
        print("🔓 НЕБЛОКИРУЮЩИЙ РЕЖИМ: Терминал не заблокируется")
    elif args.test_mode:
        print("🧪 ТЕСТОВЫЙ РЕЖИМ: Автозакрытие через 5 секунд")
    else:
        print("🔒 БЛОКИРУЮЩИЙ РЕЖИМ: Терминал заблокируется до закрытия окна")
        print("    Используйте Ctrl+C для принудительного завершения")
        print("    Или добавьте флаг --no-block для неблокирующего режима")
    
    print()
    print("💡 IMPORTANT: Look for 'rhi: backend:' line in console output")
    print("    Should show 'D3D11' (not OpenGL)")
    print()
    
    # Enable high DPI support (must be before QApplication)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    print("Step 1: Creating QApplication...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app_instance = app  # Store global reference
    
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
    
    print(f"Step 5: Creating MainWindow (backend: {backend_name})...")
    
    try:
        # Create and show main window with 3D visualization
        window = MainWindow(use_qml_3d=use_qml_3d)
        window_instance = window  # Store global reference
        
        print(f"Step 6: MainWindow created - Size: {window.size().width()}x{window.size().height()}")
        print(f"         Window title: {window.windowTitle()}")
        
        window.show()
        
        print(f"Step 7: Window shown - Visible: {window.isVisible()}")
        print(f"         Position: {window.pos().x()}, {window.pos().y()}")
        
        # Force window to front
        window.raise_()
        window.activateWindow()
        
        log_ui_event("WINDOW_SHOWN", f"Main window displayed ({backend_name})")
        
        print("\n" + "="*60)
        print(f"APPLICATION READY - {backend_name} active (Russian UI)")
        if use_qml_3d:
            print("🎮 U-Frame: PBR metallic red, orbit camera, auto-fit")
            print("🎮 Controls: LMB-rotate, Wheel-zoom, F-autofit, R-reset, DoubleClick-fit")
            print("🎮 Features: 4 corners with cylinders, levers, masses")
        else:
            print("⚙️ Legacy OpenGL rendering")
        print("🔍 DIAGNOSTIC: Looking for QML console.log messages...")
        print("Expected: Russian labels in UI panels and 3D scene")
        print("Check console for 'rhi: backend: D3D11' confirmation")
        
        if args.no_block:
            print("🔓 НЕБЛОКИРУЮЩИЙ РЕЖИМ: Терминал свободен для других команд")
            print("    Окно приложения работает независимо")
        elif args.test_mode:
            print("🧪 ТЕСТОВЫЙ РЕЖИМ: Автозакрытие через 5 секунд...")
        else:
            print("🔒 Окно приложения блокирует терминал - закройте окно для продолжения")
            print("    Или нажмите Ctrl+C для принудительного завершения")
        
        print("="*60 + "\n")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
        
        # Setup test mode auto-close timer
        if args.test_mode:
            close_timer = QTimer()
            close_timer.setSingleShot(True)
            close_timer.timeout.connect(lambda: [
                print("🧪 Тестовый режим: Автозакрытие..."),
                window.close()
            ])
            close_timer.start(5000)  # 5 seconds
        
        # Setup non-blocking mode
        if args.no_block:
            print("🔓 ВНИМАНИЕ: Неблокирующий режим лучше запускать через launch.py")
            print("    Текущий режим может работать нестабильно")
            print("    Рекомендуется: python launch.py --no-block")
            print()
            
            # In non-blocking mode, we still need to run the event loop
            # but we'll set up a way to detect if user wants to continue
            print("🔓 Запуск в условно-неблокирующем режиме...")
            print("    Приложение запустится, но Python скрипт продолжит работу")
            print("    Нажмите Ctrl+C когда приложение будет готово к работе")
            
            # Start the event loop but with a timeout mechanism
            try:
                # Run for a short time to let the window show
                start_time = time.time()
                while time.time() - start_time < 2.0:  # 2 seconds
                    app.processEvents()
                    time.sleep(0.016)  # ~60 FPS
                
                print("✅ Приложение запущено и готово к работе")
                print("    Окно должно быть видимо")
                print("    Скрипт завершается, но окно остается открытым")
                print("    ВНИМАНИЕ: Для корректной работы используйте:")
                print("              python launch.py --no-block")
                
                return 0
                
            except KeyboardInterrupt:
                print("\n🛑 Получен Ctrl+C, переключаемся в стандартный режим...")
                # Fall through to standard blocking mode
        
        # Standard blocking mode
        print("🔒 Запуск в стандартном режиме (блокирует терминал)...")
        result = app.exec()
        
        logger.info(f"Application event loop finished with code: {result}")
        print(f"\n=== APPLICATION CLOSED (code: {result}) ===")
        return result
        
    except Exception as e:
        logger.critical(f"Fatal error during application execution: {e}")
        import traceback
        logger.critical(traceback.format_exc())
        print(f"\n💀 FATAL ERROR: {e}")
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup logging happens automatically via atexit
        pass


if __name__ == "__main__":
    sys.exit(main())
