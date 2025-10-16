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
import logging
from typing import Any, Optional
import ctypes

# =============================================================================
# Накопление warnings/errors
# =============================================================================

_warnings_errors: list[tuple[str, str]] = []


def log_warning(msg: str) -> None:
    """Накапливает warning для вывода в конце"""
    _warnings_errors.append(("WARNING", msg))


def log_error(msg: str) -> None:
    """Накапливает error для вывода в конце"""
    _warnings_errors.append(("ERROR", msg))

# =============================================================================
# QtQuick3D Environment Setup
# =============================================================================


def setup_qtquick3d_environment() -> bool:
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


qtquick3d_setup_ok: bool = setup_qtquick3d_environment()

# =============================================================================
# Terminal Encoding
# =============================================================================


def configure_terminal_encoding() -> None:
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


def check_python_compatibility() -> None:
    """Проверка версии Python: проект таргетирует Python 3.13+
    
    Разрешаем обход проверки через переменную окружения
    `PSS_IGNORE_PYTHON_CHECK=1` (для CI/диагностики на старых окружениях).
    """
    # Позволяем обходить проверку при явном запросе
    if os.environ.get('PSS_IGNORE_PYTHON_CHECK') == '1':
        log_warning("Python version check bypassed via PSS_IGNORE_PYTHON_CHECK=1")
        return
    
    version = sys.version_info
    if version < (3, 13):
        log_error("Python 3.13+ required. Please upgrade Python.")
        sys.exit(1)


check_python_compatibility()

# =============================================================================
# Qt Configuration
# =============================================================================

os.environ.setdefault("QSG_RHI_BACKEND", "d3d11" if sys.platform == 'win32' else "opengl")
OS_QT_LOGGING_DEFAULT = "*.debug=false;*.info=false"
os.environ.setdefault("QSG_INFO", "0")
os.environ.setdefault("QT_LOGGING_RULES", OS_QT_LOGGING_DEFAULT)
os.environ.setdefault("QT_ASSUME_STDERR_HAS_CONSOLE", "1")
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

# Включаем вывод диагностики по умолчанию (можно переопределить переменной среды)
os.environ.setdefault("PSS_DIAG", "1")

# =============================================================================
# Qt Import
# =============================================================================


def safe_import_qt() -> tuple[Any, Any, Any, Any]:
    """Safely import Qt components"""
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import qInstallMessageHandler, Qt, QTimer, qVersion
        
        qt_version = qVersion()
        
        try:
            major, minor = qt_version.split('.')[:2]
            if int(major) == 6 and int(minor) < 10:
                log_warning(f"Qt {qt_version} detected. Some 6.10+ features may be unavailable")
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


def setup_logging(verbose_console: bool = False) -> Optional[logging.Logger]:
    """Настройка логирования - ВСЕГДА активно
    
    Args:
        verbose_console: Включать ли вывод логов в консоль (аргумент --verbose)
    """
    try:
        from src.common.logging_setup import init_logging, rotate_old_logs
        
        logs_dir = Path("logs")
        
        # Политика проекта: начинаем с чистых логов
        rotate_old_logs(logs_dir, keep_count=0)
        
        # Инициализируем логирование с ротацией
        logger = init_logging(
            "PneumoStabSim",
            logs_dir,
            max_bytes=10 * 1024 * 1024,  # 10 MB на файл
            backup_count=5,               # Держим 5 backup файлов
            console_output=bool(verbose_console)  # Включаем по запросу
        )
        
        logger.info("=" * 60)
        logger.info("PneumoStabSim v4.9.5 - Application Started")
        logger.info("=" * 60)
        logger.info(f"Python: {sys.version_info.major}.{sys.version_info.minor}")
        
        from PySide6.QtCore import qVersion
        logger.info(f"Qt: {qVersion()}")
        logger.info(f"Platform: {sys.platform}")
        logger.info(f"Backend: {os.environ.get('QSG_RHI_BACKEND', 'auto')}")
        
        if verbose_console:
            logger.info("Console verbose mode is ENABLED")
        
        return logger
    except Exception as e:
        print(f"WARNING: Logging setup failed: {e}")
        return None

# =============================================================================
# Project Imports
# =============================================================================

_main_window_module: Optional[Any] = None


def get_main_window_class() -> Any:
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

USE_QML_3D_SCHEMA: bool = True
app_instance: Optional[Any] = None
window_instance: Optional[Any] = None
app_logger: Optional[logging.Logger] = None


def signal_handler(signum: int, frame: Any) -> None:
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


def qt_message_handler(mode: Any, context: Any, message: str) -> None:
    """Handle Qt log messages - redirect to logger"""
    global app_logger
    if app_logger:
        app_logger.debug(f"Qt: {message}")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="PneumoStabSim - Pneumatic Stabilizer Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py app.py                    # Main Qt Quick 3D version
  py app.py --test-mode        # Test mode (auto-close 5s)
  py app.py --verbose          # Verbose console output
  py app.py --diag             # Run post-run diagnostics to console
        """
    )
    
    parser.add_argument('--test-mode', action='store_true', help='Test mode (auto-close 5s)')
    parser.add_argument('--verbose', action='store_true', help='Enable console logging')
    parser.add_argument('--diag', action='store_true', help='Run post-run diagnostics to console')
    
    return parser.parse_args()


def print_warnings_errors() -> None:
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


def run_log_diagnostics() -> None:
    """Запускает ВСТРОЕННУЮ диагностику логов после закрытия приложения"""
    # Дублируем вывод в окно Output Visual Studio (через OutputDebugString)
    class _VSOutputTee:
        def __init__(self, real):
            self._real = real
        def write(self, s: str) -> int:
            try:
                if sys.platform == 'win32' and s:
                    ctypes.windll.kernel32.OutputDebugStringW(str(s))
            except Exception:
                pass
            return self._real.write(s)
        def flush(self) -> None:
            try:
                self._real.flush()
            except Exception:
                pass

    _orig_stdout = sys.stdout
    _orig_stderr = sys.stderr
    try:
        # Включаем tee в VS Output
        sys.stdout = _VSOutputTee(_orig_stdout)
        sys.stderr = _VSOutputTee(_orig_stderr)

        print("\n" + "="*60)
        print("🔍 ДИАГНОСТИКА ЛОГОВ И СОБЫТИЙ")
        print("="*60)

        # ✅ НОВОЕ: Используем унифицированный анализатор
        from src.common.log_analyzer import run_full_diagnostics, quick_diagnostics
        
        # Запускаем комплексный анализ
        diag_result = run_full_diagnostics(Path("logs"))
        diagnostics_ok = bool(diag_result) if not isinstance(diag_result, dict) else bool(diag_result.get("ok", True))
        
        # Результат анализа
        print("\n" + "="*60)
        
        if diagnostics_ok:
            print("✅ Диагностика завершена - критических проблем не обнаружено")
        else:
            print("⚠️  Диагностика завершена - обнаружены проблемы")
            print("💡 См. детали выше")
        
        print("="*60)

        # Дополнительный раздел: несоответствия анализа (EVENTS vs GRAPHICS)
        try:
            q = quick_diagnostics(Path("logs")) or {}
            metrics = q.get("metrics", {}) or {}
            events_sync = None
            graphics_sync = None
            # Достаём метрики из summary.metrics (prefix category_)
            for key, val in metrics.items():
                if key.endswith("event_sync_rate") and key.startswith("events_"):
                    events_sync = float(val)
                if key.endswith("graphics_sync_rate") and key.startswith("graphics_"):
                    graphics_sync = float(val)
            if events_sync is not None and graphics_sync is not None and abs(events_sync - graphics_sync) >= 5.0:
                print("\n—— Несоответствия анализа ————————")
                print(f"EVENTS sync_rate: {events_sync:.1f}% vs GRAPHICS sync_rate: {graphics_sync:.1f}%")
                reason_hint = "QML-функции вызываются (EVENTS=OK), но часть графических обновлений не применяется или не подтверждается в graphics-логах (дубль/батч/валидация)."
                if events_sync < graphics_sync:
                    reason_hint = "Графические метрики выше событийных — возможно, не все SIGNAL_EMIT/INVOKE логируются в EventLogger."
                print(f"Причина (гипотеза): {reason_hint}")
                # Детальная расшифровка по запросу
                if os.environ.get("PSS_DIAG_DETAILS") == "1":
                    try:
                        from src.common.event_logger import get_event_logger
                        evlog = get_event_logger()
                        analysis = evlog.analyze_sync()
                        pairs = analysis.get("pairs", [])
                        missing = [p for p in pairs if p.get("status") != "synced"]
                        if missing:
                            print("\nНесинхронизированные пары (последние 10):")
                            for p in missing[-10:]:
                                py = p.get("python_event", {})
                                ts = py.get("timestamp", "?")
                                action = py.get("action", "?")
                                print(f"  • {ts} — {action} → missing in QML")
                        else:
                            print("\nEVENTS: все пары синхронизированы (нет missing)")
                    except Exception:
                        pass
                print("——————————————\n")
        except Exception:
            # Никогда не ломаем диагностику из‑за раздела несоответствий
            pass
        
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
                event_types: dict[str, int] = {}
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
    finally:
        # Восстанавливаем стандартные потоки
        sys.stdout = _orig_stdout
        sys.stderr = _orig_stderr


def main() -> int:
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
        
        # ✅ ЛОГИРОВАНИЕ ВСЕГДА ВКЛЮЧЕНО (с поддержкой --verbose)
        app_logger = setup_logging(verbose_console=args.verbose)
        
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
            
            # ✅ ФИКС: удерживаем QTimer в живых и задаём родителя
            window._auto_close_timer = QTimer(window)
            window._auto_close_timer.setSingleShot(True)
            window._auto_close_timer.timeout.connect(lambda: window.close())
            window._auto_close_timer.start(5000)
        
        result = app.exec()
        
        if app_logger:
            app_logger.info(f"Application closed with code: {result}")
            app_logger.info("=" * 60)
        
        # ✅ Вывод warnings/errors в конце
        print_warnings_errors()
        
        print(f"\n✅ Application closed (code: {result})\n")
        
        # ✅ ВСТРОЕННУЮ диагностику логов запускаем только по запросу
        if args.diag or args.verbose or os.environ.get("PSS_DIAG") == "1":
            run_log_diagnostics()
        
        return int(result)
        
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
