# -*- coding: utf-8 -*-
"""
Менеджер жизненного цикла приложения PneumoStabSim.

Координирует запуск, выполнение и корректное завершение приложения,
включая обработку сигналов, логирование и диагностику.
"""
import sys
import os
import signal
import logging
from pathlib import Path
from typing import Any, Optional
import argparse


class ApplicationRunner:
    """Менеджер жизненного цикла Qt приложения."""
    
    def __init__(
        self,
        QApplication: Any,
        qInstallMessageHandler: Any,
        Qt: Any,
        QTimer: Any
    ) -> None:
        """
        Инициализация runner'а приложения.
        
        Args:
            QApplication: Класс QApplication из PySide6
            qInstallMessageHandler: Функция установки обработчика Qt логов
            Qt: Модуль Qt из PySide6
            QTimer: Класс QTimer из PySide6
        """
        self.QApplication = QApplication
        self.qInstallMessageHandler = qInstallMessageHandler
        self.Qt = Qt
        self.QTimer = QTimer
        
        self.app_instance: Optional[Any] = None
        self.window_instance: Optional[Any] = None
        self.app_logger: Optional[logging.Logger] = None
        
        self.use_qml_3d_schema: bool = True
    
    def setup_signals(self) -> None:
        """Настройка обработчиков сигналов (Ctrl+C, SIGTERM)."""
        signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle Ctrl+C gracefully."""
        if self.app_logger:
            self.app_logger.info("Received interrupt signal - shutting down gracefully")
        
        try:
            if self.window_instance:
                self.window_instance.close()
            if self.app_instance:
                self.app_instance.quit()
        except Exception as e:
            from src.diagnostics.warnings import log_warning
            log_warning(f"Shutdown error: {e}")
    
    def _qt_message_handler(self, mode: Any, context: Any, message: str) -> None:
        """Перенаправление Qt логов в logger."""
        if self.app_logger:
            self.app_logger.debug(f"Qt: {message}")
    
    def setup_logging(self, verbose_console: bool = False) -> Optional[logging.Logger]:
        """
        Настройка логирования - ВСЕГДА активно.
        
        Args:
            verbose_console: Включать ли вывод логов в консоль
            
        Returns:
            Настроенный logger или None при ошибке
        """
        try:
            from src.common.logging_setup import init_logging, rotate_old_logs
            
            logs_dir = Path("logs")
            rotate_old_logs(logs_dir, keep_count=0)
            
            logger = init_logging(
                "PneumoStabSim",
                logs_dir,
                max_bytes=10 * 1024 * 1024,
                backup_count=5,
                console_output=bool(verbose_console)
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
    
    def setup_high_dpi(self) -> None:
        """Настройка High DPI scaling."""
        from src.diagnostics.warnings import log_warning
        
        try:
            self.QApplication.setHighDpiScaleFactorRoundingPolicy(
                self.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
        except Exception as e:
            log_warning(f"High DPI setup: {e}")
            if self.app_logger:
                self.app_logger.warning(f"High DPI setup failed: {e}")
    
    def create_application(self) -> None:
        """Создание и настройка QApplication."""
        app = self.QApplication(sys.argv)
        self.app_instance = app
        
        self.qInstallMessageHandler(self._qt_message_handler)
        
        app.setApplicationName("PneumoStabSim")
        app.setApplicationVersion("4.9.5")
        app.setOrganizationName("PneumoStabSim")
        
        if self.app_logger:
            self.app_logger.info("QApplication created and configured")
    
    def create_main_window(self) -> None:
        """Создание и отображение главного окна."""
        from src.ui.main_window import MainWindow
        
        window = MainWindow(use_qml_3d=self.use_qml_3d_schema)
        self.window_instance = window
        
        window.show()
        window.raise_()
        window.activateWindow()
        
        if self.app_logger:
            self.app_logger.info("MainWindow created and shown")
    
    def setup_test_mode(self, enabled: bool) -> None:
        """
        Настройка тестового режима (автозакрытие через 5 секунд).
        
        Args:
            enabled: Включить ли тестовый режим
        """
        if not enabled or not self.window_instance:
            return
        
        print("🧪 Test mode: auto-closing in 5 seconds...")
        if self.app_logger:
            self.app_logger.info("Test mode: auto-closing in 5 seconds")
        
        # Удерживаем QTimer в живых через атрибут window
        self.window_instance._auto_close_timer = self.QTimer(self.window_instance)
        self.window_instance._auto_close_timer.setSingleShot(True)
        self.window_instance._auto_close_timer.timeout.connect(lambda: self.window_instance.close())
        self.window_instance._auto_close_timer.start(5000)
    
    def run(self, args: argparse.Namespace) -> int:
        """
        Запуск приложения с полным lifecycle.
        
        Args:
            args: Аргументы командной строки
            
        Returns:
            Exit code приложения
        """
        from src.diagnostics.warnings import print_warnings_errors
        from src.diagnostics.logs import run_log_diagnostics
        
        try:
            # ✅ Печать заголовка
            self._print_header()
            
            # ✅ Инициализация
            self.app_logger = self.setup_logging(verbose_console=args.verbose)
            
            if self.app_logger:
                self.app_logger.info("Logging initialized successfully")
                if args.verbose:
                    self.app_logger.info("Verbose mode enabled")
            
            self.setup_high_dpi()
            self.create_application()
            self.create_main_window()
            
            print("✅ Ready!")
            print("=" * 60 + "\n")
            
            self.setup_signals()
            self.setup_test_mode(args.test_mode)
            
            # ✅ Запуск event loop
            result = self.app_instance.exec()
            
            if self.app_logger:
                self.app_logger.info(f"Application closed with code: {result}")
                self.app_logger.info("=" * 60)
            
            # ✅ Вывод warnings/errors
            print_warnings_errors()
            
            print(f"\n✅ Application closed (code: {result})\n")
            
            # ✅ Диагностика логов по запросу
            if args.diag or args.verbose or os.environ.get("PSS_DIAG") == "1":
                run_log_diagnostics()
            
            return int(result)
            
        except Exception as e:
            print(f"\n❌ FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            
            if self.app_logger:
                self.app_logger.critical(f"FATAL ERROR: {e}")
                self.app_logger.critical(traceback.format_exc())
            
            print_warnings_errors()
            
            return 1
    
    def _print_header(self) -> None:
        """Печать заголовка приложения в консоль."""
        print("=" * 60)
        print("🚀 PNEUMOSTABSIM v4.9.5")
        print("=" * 60)
        
        from PySide6.QtCore import qVersion
        qt_version = qVersion()
        
        print(f"📊 Python {sys.version_info.major}.{sys.version_info.minor} | Qt {qt_version}")
        print(f"🎨 Graphics: Qt Quick 3D | Backend: {os.environ.get('QSG_RHI_BACKEND', 'auto')}")
        print("⏳ Initializing...")
