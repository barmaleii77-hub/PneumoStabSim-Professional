# -*- coding: utf-8 -*-
"""
Менеджер жизненного цикла приложения PneumoStabSim.

Координирует запуск, выполнение и корректное завершение приложения,
включая обработку сигналов, логирование и диагностику.
"""

import asyncio
import sys
import os
import signal
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import argparse
import json
import subprocess

from pneumostabsim.logging import ErrorHookManager, install_error_hooks

from src.ui.qml_registration import register_qml_types


class ApplicationRunner:
    """Менеджер жизненного цикла Qt приложения."""

    def __init__(
        self, QApplication: Any, qInstallMessageHandler: Any, Qt: Any, QTimer: Any
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
        self.error_hook_manager: Optional[ErrorHookManager] = None

        self.use_qml_3d_schema: bool = True

    def setup_signals(self) -> None:
        """Настройка обработчиков сигналов (Ctrl+C, SIGTERM)."""
        signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, "SIGTERM"):
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
                console_output=bool(verbose_console),
            )

            logger.info("=" * 60)
            logger.info("PneumoStabSim v4.9.5 - Application Started")
            logger.info("=" * 60)
            logger.info(f"Python: {sys.version_info.major}.{sys.version_info.minor}")

            # Глобальные хуки ошибок: sys.excepthook, asyncio и Qt
            try:
                loop = self._ensure_asyncio_loop()
                error_log_json = (
                    logs_dir
                    / "errors"
                    / f"errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
                )
                self.error_hook_manager = install_error_hooks(
                    logger,
                    error_log_json,
                    loop=loop,
                    qt_install_message_handler=self.qInstallMessageHandler,
                )
                logger.info(f"Global error hooks enabled (JSON log: {error_log_json})")
            except Exception as hook_error:
                logger.warning(f"Error hook installation failed: {hook_error}")

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

    def _ensure_asyncio_loop(self) -> asyncio.AbstractEventLoop:
        """Гарантирует наличие активного asyncio event loop и возвращает его."""
        try:
            return asyncio.get_event_loop_policy().get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

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

        # Если глобальные хуки не установлены (например, ошибка на этапе логгирования),
        # подключаем локальный перехватчик Qt сообщений как fallback.
        if not self.error_hook_manager:
            self.qInstallMessageHandler(self._qt_message_handler)

        app.setApplicationName("PneumoStabSim")
        app.setApplicationVersion("4.9.5")
        app.setOrganizationName("PneumoStabSim")

        if self.app_logger:
            self.app_logger.info("QApplication created and configured")

    def create_main_window(self) -> None:
        """Создание и отображение главного окна."""
        # Предпочитаем модульную рефакторенную версию, чтобы избежать конфликта имён
        MW = None
        try:
            from src.ui.main_window.main_window_refactored import MainWindow as MW

            if self.app_logger:
                self.app_logger.info(
                    "MainWindow: using refactored version (package module)"
                )
        except Exception:
            from src.ui.main_window import MainWindow as MW

            if self.app_logger:
                self.app_logger.warning(
                    "MainWindow: refactored import failed, using default import"
                )

        register_qml_types()

        window = MW(use_qml_3d=self.use_qml_3d_schema)
        self.window_instance = window

        window.show()
        window.raise_()
        window.activateWindow()

        if self.app_logger:
            self.app_logger.info("MainWindow created and shown")

    def _run_schema_validation(self, cfg_path: Path) -> None:
        """Запускает CLI-валидатор JSON схемы для файла настроек."""
        # Определяем корень проекта (src/..)
        project_root = Path(__file__).resolve().parents[1]
        tools_dir = project_root / "tools"
        validator = tools_dir / "validate_settings.py"
        schema_path = project_root / "config" / "app_settings.schema.json"

        if not validator.exists():
            if self.app_logger:
                self.app_logger.debug(
                    "Settings validator script is missing; skipping schema check"
                )
            return

        command = [
            sys.executable,
            str(validator),
            "--settings-file",
            str(cfg_path),
            "--schema-file",
            str(schema_path),
            "--quiet",
        ]

        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            output = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(
                f"Validation script failed with exit code {result.returncode}: {output}"
            )

        if self.app_logger:
            self.app_logger.debug("Settings schema validation passed")

    def _validate_settings_file(self) -> None:
        """Строгая валидация конфигурации до создания MainWindow.

        Проверяем:
        - Путь к файлу и источник (ENV/CWD/PROJECT)
        - Наличие файла и корректность JSON
        - Обязательные ключи graphics.materials
        - Права на запись в каталог config (создание temp-файла)
        """
        from PySide6.QtWidgets import QMessageBox
        from src.common.settings_manager import get_settings_manager
        from src.common.settings_requirements import (
            BOOL_PNEUMATIC_KEYS,
            NUMERIC_PNEUMATIC_KEYS,
            NUMERIC_SIMULATION_KEYS,
            RECEIVER_VOLUME_LIMIT_KEYS,
            REQUIRED_CURRENT_SECTIONS,
            STRING_PNEUMATIC_KEYS,
        )
        import os

        sm = get_settings_manager()
        cfg_path = Path(sm.settings_file).absolute()

        def _fail(message: str, exc_type: type[Exception] = ValueError) -> None:
            if self.app_logger:
                self.app_logger.critical(message)
            QMessageBox.critical(None, "Ошибка конфигурации", message)
            raise exc_type(message)

        # Схемная валидация (если доступна)
        try:
            self._run_schema_validation(cfg_path)
        except RuntimeError as exc:
            _fail(str(exc))

        # Определяем источник пути
        src = "CWD"
        if os.environ.get("PSS_SETTINGS_FILE"):
            src = "ENV"
        else:
            # Попробуем угадать project path
            try:
                project_candidate = (
                    Path(__file__).resolve().parents[1] / "config" / "app_settings.json"
                )
                if cfg_path.samefile(project_candidate):
                    src = "PROJECT"
            except Exception:
                pass

        msg_base = f"Settings file: {cfg_path} [source={src}]"
        print(msg_base)
        if self.app_logger:
            self.app_logger.info(msg_base)

        # 1) Существование
        if not cfg_path.exists():
            _fail(f"Файл настроек не найден: {cfg_path}")

        # 2) Чтение и JSON
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as ex:
            _fail(f"Некорректный JSON в файле настроек: {cfg_path}\n{ex}")

        if not isinstance(data, dict):
            _fail("Файл настроек должен содержать JSON-объект на верхнем уровне")

        current = data.get("current")
        if not isinstance(current, dict):
            _fail("Отсутствует секция current с текущими настройками")

        def _get_path(payload: dict, path: str) -> Any:
            node: Any = payload
            for part in path.split("."):
                if not isinstance(node, dict) or part not in node:
                    raise KeyError(path)
                node = node[part]
            return node

        def _require_dict(path: str) -> dict:
            try:
                value = _get_path(data, path)
            except KeyError:
                _fail(f"Отсутствует обязательная секция {path}")
            if not isinstance(value, dict):
                _fail(f"Секция {path} должна быть объектом")
            return value

        def _require_number(path: str) -> float:
            try:
                value = _get_path(data, path)
            except KeyError:
                _fail(f"Отсутствует обязательный числовой параметр {path}")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                _fail(f"Параметр {path} должен быть числом")
            return float(value)

        def _require_string(path: str) -> str:
            try:
                value = _get_path(data, path)
            except KeyError:
                _fail(f"Отсутствует обязательный текстовый параметр {path}")
            if not isinstance(value, str) or not value.strip():
                _fail(f"Параметр {path} должен быть непустой строкой")
            return value

        def _require_bool(path: str) -> bool:
            try:
                value = _get_path(data, path)
            except KeyError:
                _fail(f"Отсутствует обязательный логический параметр {path}")
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return bool(value)
            _fail(f"Параметр {path} должен быть логическим значением (true/false)")

        # 3) Обязательные секции current.*
        for section in REQUIRED_CURRENT_SECTIONS:
            _require_dict(section)

        # 4) Обязательные числовые параметры
        for key in NUMERIC_SIMULATION_KEYS:
            _require_number(f"current.simulation.{key}")

        for key in NUMERIC_PNEUMATIC_KEYS:
            _require_number(f"current.pneumatic.{key}")

        for key in RECEIVER_VOLUME_LIMIT_KEYS:
            _require_number(f"current.pneumatic.receiver_volume_limits.{key}")

        # 5) Обязательные текстовые и логические параметры
        for key in STRING_PNEUMATIC_KEYS:
            _require_string(f"current.pneumatic.{key}")

        for key in BOOL_PNEUMATIC_KEYS:
            _require_bool(f"current.pneumatic.{key}")

        # 6) Обязательные ключи материалов
        try:
            current = data.get("current", {}) if isinstance(data, dict) else {}
            graphics = current.get("graphics", {}) if isinstance(current, dict) else {}
            materials = (
                graphics.get("materials", {}) if isinstance(graphics, dict) else {}
            )
            required_keys = {
                "frame",
                "lever",
                "tail",
                "cylinder",
                "piston_body",
                "piston_rod",
                "joint_tail",
                "joint_arm",
                "joint_rod",
            }
            present = set(materials.keys()) if isinstance(materials, dict) else set()
            missing = sorted(list(required_keys - present))
            if missing:
                _fail(
                    "Отсутствуют обязательные материалы в current.graphics.materials: "
                    + ", ".join(missing)
                )
        except Exception:
            raise

        # 4) Проверка записи в каталог
        try:
            tmp = cfg_path.parent / "~pss_write_test.tmp"
            with open(tmp, "w", encoding="utf-8") as tf:
                tf.write("ok")
            tmp.unlink(missing_ok=True)
        except Exception as ex:
            _fail(f"Нет прав на запись в каталог конфигурации: {cfg_path.parent}\n{ex}")

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
        self.window_instance._auto_close_timer.timeout.connect(
            lambda: self.window_instance.close()
        )
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
            # Строгая валидация конфигурации до создания окна
            self._validate_settings_file()
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

        print(
            f"📊 Python {sys.version_info.major}.{sys.version_info.minor} | Qt {qt_version}"
        )
        print(
            f"🎨 Graphics: Qt Quick 3D | Backend: {os.environ.get('QSG_RHI_BACKEND', 'auto')}"
        )
        print("⏳ Initializing...")
