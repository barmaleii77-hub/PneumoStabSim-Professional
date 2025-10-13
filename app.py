# -*- coding: utf-8 -*-
"""
PneumoStabSim - Pneumatic Stabilizer Simulator
Main application entry point - CLEAN TERMINAL VERSION
"""
import sys
import os
import locale
import signal
import argparse
import subprocess
from pathlib import Path

# =============================================================================
# Накопление warnings/errors
# =============================================================================

_warnings_errors = []

def log_warning(msg: str):
    """Накапливает warning для вывода в конце"""
    _warnings_errors.append(("WARNING", msg))


def log_error(msg: str):
    """Накапливает error для вывода в конце"""
    _warnings_errors.append(("ERROR", msg))

# =============================================================================
# QtQuick3D Environment Setup
# =============================================================================


def setup_qtquick3d_environment():
    """Set up QtQuick3D environment variables before importing Qt"""
    required_vars = ["QML2_IMPORT_PATH", "QML_IMPORT_PATH", "QT_PLUGIN_PATH", "QT_QML_IMPORT_PATH"]
    if all(var in os.environ for var in required_vars):
        return True
    
    try:
        import importlib.util
        spec = importlib.util.find_spec("PySide6.QtCore")
        if spec is None:
            log_error("PySide6 not found!")
            return False
            
        from PySide6.QtCore import QLibraryInfo
        
        qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
        plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
        
        qtquick3d_env = {
            "QML2_IMPORT_PATH": str(qml_path),
            "QML_IMPORT_PATH": str(qml_path),
            "QT_PLUGIN_PATH": str(plugins_path),
            "QT_QML_IMPORT_PATH": str(qml_path),
        }
        
        for var, value in qtquick3d_env.items():
            os.environ[var] = value
        
        return True
        
    except Exception as e:
        log_error(f"QtQuick3D setup failed: {e}")
        return False


qtquick3d_setup_ok = setup_qtquick3d_environment()

# =============================================================================
# Terminal Encoding
# =============================================================================


def configure_terminal_encoding():
    """Configure terminal encoding for cross-platform Unicode support"""
    if sys.platform == 'win32':
        try:
            subprocess.run(['chcp', '65001'], capture_output=True, check=False)
        except Exception:
            pass
        
        # На Windows не меняем locale на несуществующий 'C.UTF-8'
        # Достаточно PYTHONIOENCODING и перевода консоли в UTF-8
        try:
            import codecs
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')
        except Exception as e:
            log_warning(f"UTF-8 setup: {e}")
    
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    
    # На Unix-системах пытаемся установить UTF-8 локаль
    if sys.platform != 'win32':
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            except locale.Error:
                # В крайнем случае остаёмся на системной локали
                pass


configure_terminal_encoding()

# =============================================================================
# Python Version Check
# =============================================================================


def check_python_compatibility():
    """Check Python version and warn about potential issues"""
    version = sys.version_info
    
    if version < (3, 8):
        log_error("Python 3.8+ required. Please upgrade Python.")
        sys.exit(1)
    elif version >= (3, 12):
        log_warning("Python 3.12+ detected. Some packages may have compatibility issues.")


check_python_compatibility()

# =============================================================================
# Qt Configuration
# =============================================================================

os.environ.setdefault("QSG_RHI_BACKEND", "d3d11" if sys.platform == 'win32' else "opengl")
os.environ.setdefault("QSG_INFO", "0")
os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;*.info=false")
os.environ.setdefault("QT_ASSUME_STDERR_HAS_CONSOLE", "1")
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

# =============================================================================
# Qt Import
# =============================================================================


def safe_import_qt():
    """Safely import Qt components"""
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import qInstallMessageHandler, Qt, QTimer, qVersion
        
        qt_version = qVersion()
        
        try:
            major, minor = qt_version.split('.')[:2]
            if int(major) == 6 and int(minor) < 8:
                log_warning(f"Qt {qt_version} - ExtendedSceneEnvironment may be limited")
        except (ValueError, IndexError):
            log_warning(f"Could not parse Qt version: {qt_version}")
        
        return QApplication, qInstallMessageHandler, Qt, QTimer
    except ImportError as e:
        log_error(f"PySide6 import failed: {e}")
        sys.exit(1)


QApplication, qInstallMessageHandler, Qt, QTimer = safe_import_qt()

# =============================================================================
# Logging Setup - ВСЕГДА ВКЛЮЧЕНО
# =============================================================================


def setup_logging():
    """Настройка логирования - ВСЕГДА активно"""
    try:
        from src.common.logging_setup import init_logging, rotate_old_logs
        
        logs_dir = Path("logs")
        
        # ✅ НОВОЕ: Ротация старых логов (оставляем только 10 последних)
        rotate_old_logs(logs_dir, keep_count=10)
        
        # Инициализируем логирование с ротацией
        logger = init_logging(
            "PneumoStabSim",
            logs_dir,
            max_bytes=10 * 1024 * 1024,  # 10 MB на файл
            backup_count=5,               # Держим 5 backup файлов
            console_output=False          # НЕ выводим в консоль
        )
        
        logger.info("=" * 60)
        logger.info("PneumoStabSim v4.9.5 - Application Started")
        logger.info("=" * 60)
        logger.info(f"Python: {sys.version_info.major}.{sys.version_info.minor}")
        
        from PySide6.QtCore import qVersion
        logger.info(f"Qt: {qVersion()}")
        logger.info(f"Platform: {sys.platform}")
        logger.info(f"Backend: {os.environ.get('QSG_RHI_BACKEND', 'auto')}")
        
        return logger
    except Exception as e:
        print(f"WARNING: Logging setup failed: {e}")
        return None

# =============================================================================
# Project Imports
# =============================================================================

_main_window_module = None


def get_main_window_class():
    """Ленивая загрузка MainWindow класса"""
    global _main_window_module
    if _main_window_module is None:
        try:
            from src.ui.main_window import MainWindow
            _main_window_module = MainWindow
        except ImportError as e:
            log_error(f"MainWindow import error: {e}")
            sys.exit(1)
    return _main_window_module

# =============================================================================
# Application Logic
# =============================================================================

USE_QML_3D_SCHEMA = True
app_instance = None
window_instance = None
app_logger = None


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global app_instance, window_instance, app_logger
    
    if app_logger:
        app_logger.info("Received interrupt signal - shutting down gracefully")
    
    try:
        if window_instance:
            window_instance.close()
        if app_instance:
            app_instance.quit()
    except Exception as e:
        log_warning(f"Shutdown error: {e}")


def qt_message_handler(mode, context, message):
    """Handle Qt log messages - redirect to logger"""
    global app_logger
    if app_logger:
        app_logger.debug(f"Qt: {message}")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="PneumoStabSim - Pneumatic Stabilizer Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py app.py                    # Main Qt Quick 3D version
  py app.py --test-mode        # Test mode (auto-close 5s)
  py app.py --verbose          # Verbose console output
        """
    )
    
    parser.add_argument('--test-mode', action='store_true', help='Test mode (auto-close 5s)')
    parser.add_argument('--verbose', action='store_true', help='Enable console logging')
    
    return parser.parse_args()


def print_warnings_errors():
    """Вывод всех warnings/errors в конце"""
    if not _warnings_errors:
        return
    
    print("\n" + "=" * 60)
    print("⚠️  WARNINGS & ERRORS:")
    print("=" * 60)
    
    warnings = [msg for level, msg in _warnings_errors if level == "WARNING"]
    errors = [msg for level, msg in _warnings_errors if level == "ERROR"]
    
    if warnings:
        print("\n⚠️  Warnings:")
        for w in warnings:
            print(f"  • {w}")
    
    if errors:
        print("\n❌ Errors:")
        for e in errors:
            print(f"  • {e}")
    
    print("=" * 60 + "\n")


def run_log_diagnostics():
    """Запускает ВСТРОЕННУЮ диагностику логов после закрытия приложения"""
    print("\n" + "="*60)
    print("🔍 ДИАГНОСТИКА ЛОГОВ И СОБЫТИЙ")
    print("="*60)
    
    try:
        # ✅ НОВОЕ: Используем унифицированный анализатор
        from src.common.log_analyzer import run_full_diagnostics
        
        # Запускаем комплексный анализ
        diagnostics_ok = run_full_diagnostics(Path("logs"))
        
        # Результат анализа
        print("\n" + "="*60)
        
        if diagnostics_ok:
            print("✅ Диагностика завершена - критических проблем не обнаружено")
        else:
            print("⚠️  Диагностика завершена - обнаружены проблемы")
            print("💡 См. детали выше")
        
        print("="*60)
        
    except ImportError as e:
        print(f"⚠️  Модуль анализа не найден: {e}")
        print("💡 Используйте устаревшую версию analyze_logs.py")
        
        # Fallback на старую версию
        try:
            # ✅ ИСПРАВЛЕНО: Все функции импортируются из analyze_logs
            from analyze_logs import (
                analyze_all_logs,
                analyze_graphics_sync,
                analyze_user_session
            )
            
            # Запускаем анализ логов
            print("\n📊 Анализ всех логов...")
            logs_result = analyze_all_logs()
            
            print("\n🎨 Анализ синхронизации графики...")
            graphics_result = analyze_graphics_sync()
            
            print("\n👤 Анализ пользовательской сессии...")
            session_result = analyze_user_session()
            
            # ✅ НОВОЕ: Анализ событий Python↔QML
            print("\n🔗 Анализ событий Python↔QML...")
            try:
                from src.common.event_logger import get_event_logger
                
                event_logger = get_event_logger()
                
                # Экспортируем события
                events_file = event_logger.export_events()
                print(f"   📁 События экспортированы: {events_file}")
                
                # Анализируем синхронизацию
                analysis = event_logger.analyze_sync()
                
                total = analysis.get('total_signals', 0)
                synced = analysis.get('synced', 0)
                missing = analysis.get('missing_qml', 0)
                
                if total > 0:
                    sync_rate = (synced / total) * 100
                    print(f"   Всего сигналов: {total}")
                    print(f"   Синхронизировано: {synced}")
                    print(f"   Пропущено QML: {missing}")
                    print(f"   Процент синхронизации: {sync_rate:.1f}%")
                    
                    if missing > 0:
                        print(f"   ⚠️  Обнаружены несинхронизированные события!")
                    else:
                        print(f"   ✅ Все события успешно синхронизированы")
                else:
                    print(f"   ℹ️  Сигналов не обнаружено (событий не было)")
                
                # Статистика по типам событий
                event_types = {}
                for event in event_logger.events:
                    event_type = event.get('event_type', 'UNKNOWN')
                    event_types[event_type] = event_types.get(event_type, 0) + 1
                
                if event_types:
                    print(f"\n   📈 События по типам:")
                    for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
                        print(f"      {event_type}: {count}")
                
            except ImportError:
                print(f"   ⚠️  EventLogger не доступен")
            except Exception as e:
                print(f"   ❌ Ошибка анализа событий: {e}")
            
            # Итоговый статус
            print("\n" + "="*60)
            
            all_ok = all([logs_result, graphics_result, session_result])
            
            if all_ok:
                print("✅ Диагностика завершена - проблем не обнаружено")
            else:
                print("⚠️  Диагностика завершена - обнаружены проблемы")
                print("💡 См. детали выше")
            
            print("="*60)
            
        except ImportError:
            print("⚠️  Модули анализа не доступны")
        except Exception as e:
            print(f"❌ Ошибка fallback диагностики: {e}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Ошибка диагностики: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main application function - CLEAN OUTPUT"""
    global app_instance, window_instance, app_logger
    
    try:
        args = parse_arguments()
        
        # ✅ КРАТКАЯ диагностика в терминал
        print("=" * 60)
        print("🚀 PNEUMOSTABSIM v4.9.5")
        print("=" * 60)
        
        from PySide6.QtCore import qVersion
        qt_version = qVersion()
        
        print(f"📊 Python {sys.version_info.major}.{sys.version_info.minor} | Qt {qt_version}")
        print(f"🎨 Graphics: Qt Quick 3D | Backend: {os.environ.get('QSG_RHI_BACKEND', 'auto')}")
        print("⏳ Initializing...")
        
        # ✅ ЛОГИРОВАНИЕ ВСЕГДА ВКЛЮЧЕНО
        app_logger = setup_logging()
        
        if app_logger:
            app_logger.info("Logging initialized successfully")
            if args.verbose:
                app_logger.info("Verbose mode enabled")
        
        try:
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
        except Exception as e:
            log_warning(f"High DPI setup: {e}")
            if app_logger:
                app_logger.warning(f"High DPI setup failed: {e}")
        
        app = QApplication(sys.argv)
        app_instance = app
        
        qInstallMessageHandler(qt_message_handler)
        
        app.setApplicationName("PneumoStabSim")
        app.setApplicationVersion("4.9.5")
        app.setOrganizationName("PneumoStabSim")
        
        if app_logger:
            app_logger.info("QApplication created and configured")
        
        MainWindow = get_main_window_class()
        window = MainWindow(use_qml_3d=USE_QML_3D_SCHEMA)
        window_instance = window
        
        window.show()
        window.raise_()
        window.activateWindow()
        
        if app_logger:
            app_logger.info("MainWindow created and shown")
        
        print("✅ Ready!")
        print("=" * 60 + "\n")
        
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
        
        if args.test_mode:
            print("🧪 Test mode: auto-closing in 5 seconds...")
            if app_logger:
                app_logger.info("Test mode: auto-closing in 5 seconds")
            
            close_timer = QTimer()
            close_timer.setSingleShot(True)
            close_timer.timeout.connect(lambda: window.close())
            close_timer.start(5000)
        
        result = app.exec()
        
        if app_logger:
            app_logger.info(f"Application closed with code: {result}")
            app_logger.info("=" * 60)
        
        # ✅ Вывод warnings/errors в конце
        print_warnings_errors()
        
        print(f"\n✅ Application closed (code: {result})\n")
        
        # ✅ ВСЕГДА запускаем ВСТРОЕННУЮ диагностику логов после выхода
        run_log_diagnostics()
        
        return result
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        if app_logger:
            app_logger.critical(f"FATAL ERROR: {e}")
            app_logger.critical(traceback.format_exc())
        
        print_warnings_errors()
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
