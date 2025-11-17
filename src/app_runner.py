"""
Менеджер жизненного цикла приложения PneumoStabSim.

Координирует запуск, выполнение и корректное завершение приложения,
включая обработку сигналов, логирование и диагностику.
"""

from __future__ import annotations

from typing import Any  # moved earlier to avoid reordering impacts

# ...existing code...

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

from src.infrastructure.logging import ErrorHookManager, install_error_hooks
from src.diagnostics.logger_factory import LoggerProtocol, get_logger
from src.diagnostics.logging_presets import LoggingPreset
from src.core.settings_validation import (
    SettingsValidationError,
    determine_settings_source,
    validate_settings_file,
)
from src.core.settings_models import AppSettings, dump_settings
from src.ui.qml_registration import register_qml_types

# Безопасные импорты диагностик: в тестах или минимальных окружениях модули
# могут отсутствовать. В этом случае подставляем заглушки.
try:  # noqa: SIM105 - намеренно широкая обработка
    from src.diagnostics.warnings import print_warnings_errors  # type: ignore
except Exception:  # pragma: no cover - заглушка для минимальных окружениях

    def print_warnings_errors() -> None:  # type: ignore
        return None


# Удалён ранний импорт run_log_diagnostics, чтобы тесты могли мокаать
# src.diagnostics.logs.run_log_diagnostics и перехватывать вызов.
# Динамический импорт выполняется в методе _run_post_diagnostics().

# ...existing code...

if TYPE_CHECKING:

    class MainWindowProtocol(Protocol):
        """Protocol capturing the runtime behaviour required from main windows."""

        def show(self) -> None: ...

        def raise_(self) -> None: ...

        def activateWindow(self) -> None: ...

        def close(self) -> bool | None: ...

else:  # pragma: no cover - protocol only aids static type checking

    class MainWindowProtocol:
        """Runtime placeholder used when static typing is unavailable."""

        pass


class ApplicationRunner:
    """Менеджер жизненного цикла Qt приложения."""

    def __init__(
        self,
        QApplication: Any,
        qInstallMessageHandler: Any,
        Qt: Any,
        QTimer: Any,
        *,
        logging_preset: LoggingPreset | None = None,
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
        self.logging_preset = logging_preset

        self.app_instance: Any | None = None
        self.window_instance: MainWindowProtocol | None = None
        self.app_logger: logging.Logger | None = None
        self.error_hook_manager: ErrorHookManager | None = None
        self.logger: LoggerProtocol = get_logger("app.runner").bind(
            component="ApplicationRunner"
        )

        self.use_qml_3d_schema: bool = True
        self.use_legacy_ui: bool = False
        self.safe_mode_requested: bool = False
        self.safe_runtime_requested: bool = False
        self.safe_cli_mode: bool = False
        self._is_headless: bool = False
        self._headless_reason: str | None = None
        self._surface_format_configured: bool = False
        self._safe_exit_timer: Any | None = None

    @staticmethod
    def _gather_startup_environment_snapshot() -> dict[str, str]:
        """Collect key environment details for diagnostics."""

        qt_qpa = os.environ.get("QT_QPA_PLATFORM", "<unset>")
        qsg_backend = os.environ.get("QSG_RHI_BACKEND", "<unset>")
        qt_plugin_path = os.environ.get("QT_PLUGIN_PATH", "<unset>")

        try:
            import PySide6

            pyside_version = getattr(PySide6, "__version__", "unknown")
        except Exception:  # pragma: no cover - PySide6 may be unavailable in CI
            pyside_version = "unavailable"

        return {
            "platform": sys.platform,
            "QT_QPA_PLATFORM": qt_qpa or "<empty>",
            "QSG_RHI_BACKEND": qsg_backend or "<empty>",
            "QT_PLUGIN_PATH": qt_plugin_path or "<empty>",
            "PySide6": pyside_version,
        }

    @staticmethod
    def _format_startup_environment_message(snapshot: dict[str, str]) -> str:
        """Create a single-line startup diagnostics message."""

        ordered_keys = [
            "platform",
            "QT_QPA_PLATFORM",
            "QSG_RHI_BACKEND",
            "QT_PLUGIN_PATH",
            "PySide6",
        ]
        parts = ["STARTUP_ENVIRONMENT"]
        for key in ordered_keys:
            value = snapshot.get(key, "<missing>")
            parts.append(f"{key}={value}")
        return " | ".join(parts)

    def _log_with_fallback(self, level: str, message: str, **kwargs: Any) -> None:
        """Emit a log message using the configured logger or structlog fallback."""

        logger_obj: Any = self.app_logger if self.app_logger else self.logger
        log_method = getattr(logger_obj, level, None)
        if callable(log_method):
            log_method(message, **kwargs)

    def _log_startup_environment(self) -> None:
        """Emit startup environment diagnostics to file, logger, and stdout."""

        snapshot = self._gather_startup_environment_snapshot()
        message = self._format_startup_environment_message(snapshot)

        print(message, flush=True)

        try:
            logs_dir = Path("logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            startup_log = logs_dir / "startup.log"
            with startup_log.open("a", encoding="utf-8") as handle:
                handle.write(message + "\n")
        except Exception as exc:  # pragma: no cover - log persistence is best effort
            if self.app_logger:
                self.app_logger.warning(
                    "Failed to write startup environment log: %s", exc
                )

        if self.app_logger:
            self.app_logger.info(message, extra={"startup_environment": snapshot})

    def _configure_default_surface_format(self) -> None:
        """Force the OpenGL RHI backend with depth/stencil buffers before QApplication.

        Qt Quick 3D effects such as FogEffect and Depth of Field depend on depth
        textures and full-featured shader pipelines. Without explicitly
        requesting the OpenGL RHI backend and a depth/stencil buffer pair
        (24/8), Qt may fall back to reduced-feature profiles that disable these
        effects. To keep startup deterministic we always configure the RHI
        backend here prior to creating ``QApplication``.
        """

        if self._surface_format_configured:
            return

        if self.safe_mode_requested:
            if self.app_logger:
                self.app_logger.info(
                    "Safe mode active — skipping forced OpenGL surface format"
                )
            else:
                self._log_with_fallback(
                    "info",
                    "INFO: safe mode active — relying on Qt runtime to choose the scene graph backend",
                )
            return

        if self.safe_cli_mode:
            if self.app_logger:
                self.app_logger.info(
                    "Safe CLI mode active — skipping forced OpenGL surface format",
                    extra={"reason": "cli-safe"},
                )
            else:
                self._log_with_fallback(
                    "info",
                    "INFO: safe CLI mode active — relying on Qt runtime to choose the scene graph backend",
                )
            return

        if self.safe_runtime_requested:
            if self.app_logger:
                self.app_logger.info(
                    "Safe runtime requested — leaving surface format selection to Qt"
                )
            else:
                self._log_with_fallback(
                    "info",
                    "INFO: safe runtime requested — surface format will not be forced",
                )
            return

        try:
            from PySide6.QtGui import QSurfaceFormat
            from PySide6.QtQuick import QQuickWindow, QSGRendererInterface
        except Exception as exc:  # pragma: no cover - Qt bindings may be missing in CI
            if self.app_logger:
                self.app_logger.debug(
                    "Skipping surface configuration (Qt modules unavailable): %s",
                    exc,
                )
            return

        try:
            format_ = QSurfaceFormat()
            format_.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
            format_.setVersion(3, 3)
            format_.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
            format_.setDepthBufferSize(24)
            format_.setStencilBufferSize(8)
            format_.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
            format_.setSwapInterval(1)

            QSurfaceFormat.setDefaultFormat(format_)
            QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.OpenGLRhi)

            self._surface_format_configured = True

            if self.app_logger:
                self.app_logger.info(
                    "Configured OpenGL RHI surface (OpenGL 3.3 Core, depth 24 / stencil 8)"
                )
        except Exception as exc:  # pragma: no cover - defensive guard around Qt APIs
            if self.app_logger:
                self.app_logger.warning(
                    "Failed to configure OpenGL surface format: %s",
                    exc,
                )

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

    def _persist_settings_on_exit(self) -> None:
        """Persist runtime settings when the Qt event loop is about to exit."""

        logger = self.app_logger

        # Flush SettingsManager (used by the UI panels) to disk first.
        try:
            from src.common.settings_manager import get_settings_manager
        except Exception as exc:  # pragma: no cover - defensive import guard
            if logger:
                logger.debug("SettingsManager import failed: %s", exc, exc_info=True)
        else:
            try:
                manager = get_settings_manager()
                save_if_dirty = getattr(manager, "save_if_dirty", None)
                if callable(save_if_dirty):
                    pending = bool(getattr(manager, "is_dirty", False))
                    save_if_dirty()
                    if logger:
                        if pending:
                            logger.info("SettingsManager state saved on exit")
                        else:
                            logger.debug(
                                "SettingsManager had no pending changes on exit"
                            )
                elif hasattr(manager, "save"):
                    manager.save()
                    if logger:
                        logger.info("SettingsManager state saved on exit")
            except Exception as exc:  # pragma: no cover - persistence issues are rare
                if logger:
                    logger.error(
                        "Failed to persist settings via SettingsManager: %s",
                        exc,
                        exc_info=True,
                    )

        # Ensure the lightweight SettingsService cache mirrors the latest file.
        try:
            from src.core.settings_service import SETTINGS_SERVICE_TOKEN
            from src.infrastructure.container import get_default_container
        except Exception as exc:  # pragma: no cover - optional dependency at runtime
            if logger:
                logger.debug("SettingsService import failed: %s", exc, exc_info=True)
            return

        def _promote_animation_in_memory(payload: dict[str, Any]) -> bool:
            changed = False
            try:
                current = payload.get("current")
                if isinstance(current, dict):
                    graphics = current.get("graphics")
                    if isinstance(graphics, dict) and "animation" in graphics:
                        anim = graphics.pop("animation")
                        if not isinstance(current.get("animation"), dict):
                            current["animation"] = anim
                        changed = True
                defaults = payload.get("defaults_snapshot")
                if isinstance(defaults, dict):
                    graphics = defaults.get("graphics")
                    if isinstance(graphics, dict) and "animation" in graphics:
                        anim = graphics.pop("animation")
                        if not isinstance(defaults.get("animation"), dict):
                            defaults["animation"] = anim
                        changed = True
            except Exception:
                return False
            return changed

        try:
            service = get_default_container().resolve(SETTINGS_SERVICE_TOKEN)
            payload_model: Any
            try:
                payload_model = service.load(use_cache=False)
            except Exception as load_exc:
                # Попробуем починить файл настроек и повторить
                try:
                    from src.common.settings_manager import get_settings_manager

                    sm2 = get_settings_manager()
                    settings_path = Path(getattr(sm2, "settings_file"))
                    self._auto_migrate_legacy_animation(settings_path)
                except Exception as fix_exc:  # pragma: no cover
                    if logger:
                        logger.warning(
                            "SettingsService load failed (%s); auto-migration attempt failed: %s",
                            load_exc,
                            fix_exc,
                        )
                    raise
                else:
                    # Retry after migration
                    payload_model = service.load(use_cache=False)

            payload_dict = self._coerce_settings_payload(payload_model)

            # Дополнительная защита: если за сессию кто-то снова записал legacy поле
            if _promote_animation_in_memory(payload_dict):
                if logger:
                    logger.info(
                        "Normalized in-memory settings payload (promoted graphics.animation) before final save"
                    )
            service.save(payload_dict)
            if logger:
                logger.info("SettingsService payload persisted on exit")
        except Exception as exc:  # pragma: no cover - avoid raising during shutdown
            if logger:
                logger.error(
                    "Failed to flush SettingsService cache: %s", exc, exc_info=True
                )

    def _qt_message_handler(self, mode: Any, context: Any, message: str) -> None:
        """Перенаправление Qt логов в logger."""
        if self.app_logger:
            self.app_logger.debug(f"Qt: {message}")

    def setup_logging(self, verbose_console: bool = False) -> logging.Logger | None:
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

            level = (
                self.logging_preset.python_level
                if self.logging_preset is not None
                else logging.DEBUG
            )

            logger = init_logging(
                "PneumoStabSim",
                logs_dir,
                max_bytes=10 * 1024 * 1024,
                backup_count=5,
                console_output=bool(verbose_console),
                level=level,
            )

            logger.info("=" * 60)
            logger.info("PneumoStabSim v5.0.0 - Application Started")
            logger.info("=" * 60)
            logger.info(f"Python: {sys.version_info.major}.{sys.version_info.minor}")
            if self.logging_preset is not None:
                logger.info(
                    "Logging preset selected",
                    extra={
                        "preset": self.logging_preset.name,
                        "qt_logging_rules": self.logging_preset.qt_logging_rules,
                        "qsg_info": self.logging_preset.qsg_info,
                    },
                )

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

            try:
                from PySide6.QtCore import qVersion
            except Exception:  # pragma: no cover - headless environments
                qt_version = "unavailable"
            else:
                qt_version = qVersion()

            logger.info(f"Qt: {qt_version}")
            logger.info(f"Platform: {sys.platform}")
            logger.info(f"Backend: {os.environ.get('QSG_RHI_BACKEND', 'auto')}")

            if verbose_console:
                logger.info("Console verbose mode is ENABLED")

            return logger
        except Exception as e:
            logging.getLogger("app.runner").warning(
                "WARNING: Logging setup failed: %s",
                e,
                exc_info=True,
            )
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

        if not hasattr(self.QApplication, "setHighDpiScaleFactorRoundingPolicy"):
            log_warning("High DPI setup: Qt runtime does not expose DPI controls")
            return

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
        self._configure_default_surface_format()

        app = self.QApplication(sys.argv)
        self.app_instance = app

        self._is_headless = bool(
            getattr(app, "is_headless", False) or getattr(self.Qt, "is_headless", False)
        )
        self._headless_reason = getattr(app, "headless_reason", None) or getattr(
            self.Qt, "headless_reason", None
        )

        # Если глобальные хуки не установлены (например, ошибка на этапе логгирования),
        # подключаем локальный перехватчик Qt сообщений как fallback.
        if not self.error_hook_manager:
            self.qInstallMessageHandler(self._qt_message_handler)

        if hasattr(app, "aboutToQuit"):
            try:
                app.aboutToQuit.connect(self._persist_settings_on_exit)
            except Exception as exc:  # pragma: no cover - Qt connection errors are rare
                if self.app_logger:
                    self.app_logger.debug(
                        "Failed to connect aboutToQuit handler: %s", exc, exc_info=True
                    )

        app.setApplicationName("PneumoStabSim")
        app.setApplicationVersion("5.0.0")
        app.setOrganizationName("PneumoStabSim")

        if self.app_logger:
            self.app_logger.info("QApplication created and configured")
            if self._is_headless:
                reason = self._headless_reason or "PySide6 is unavailable"
                self.app_logger.warning(
                    "Running without a Qt GUI (headless diagnostics mode). Reason: %s",
                    reason,
                )
        elif self._is_headless:
            reason = self._headless_reason or "PySide6 is unavailable"
            self._log_with_fallback(
                "warning",
                f"WARNING: headless diagnostics mode enabled (Qt GUI unavailable). Reason: {reason}",
            )

    def create_main_window(self) -> None:
        """Создание и отображение главного окна."""
        if self.safe_runtime_requested and self.safe_cli_mode:
            if self.app_logger:
                self.app_logger.info(
                    "Safe CLI mode active — skipping MainWindow instantiation",
                    extra={"reason": "cli-safe"},
                )
            else:
                self._log_with_fallback(
                    "info",
                    "INFO: safe CLI mode — skipping MainWindow creation; exiting shortly",
                )
            self.window_instance = None
            return

        if self.safe_runtime_requested:
            if self.app_logger:
                self.app_logger.info(
                    "Safe runtime mode active — skipping MainWindow instantiation"
                )
            else:
                self._log_with_fallback(
                    "info",
                    "INFO: safe runtime mode — skipping MainWindow creation; exiting shortly",
                )
            self.window_instance = None
            return

        if self._is_headless:
            if self.app_logger:
                self.app_logger.info(
                    "Headless mode active — skipping MainWindow instantiation"
                )
            else:
                self._log_with_fallback(
                    "warning",
                    "WARNING: headless mode — skipping MainWindow creation; diagnostics only",
                )
            self.window_instance = None
            return

        try:
            main_window = self._instantiate_main_window(
                use_qml_3d=self.use_qml_3d_schema
            )
        except Exception as exc:
            # Переводим причину в пост-диагностику
            self._append_post_diag_trace(f"qml-create-window-failed:{exc}")
            if self.app_logger:
                self.app_logger.error(
                    "MainWindow creation failed: %s", exc, exc_info=True
                )
            else:
                self._log_with_fallback(
                    "warning",
                    f"WARNING: fallback window due to startup error: {exc}",
                )

            main_window = self._create_diagnostics_main_window(str(exc))

        self.window_instance = main_window

        main_window.show()
        main_window.raise_()
        main_window.activateWindow()

        if self.app_logger:
            self.app_logger.info("MainWindow created and shown")

        self._log_runtime_scenegraph_backend()

    def _instantiate_main_window(self, *, use_qml_3d: bool) -> MainWindowProtocol:
        """Create a :class:`MainWindow` instance with the preferred backend."""

        if self.use_legacy_ui:
            from src.ui.main_window_legacy import MainWindow as LegacyMainWindow

            if use_qml_3d:
                # Legacy mode renders with QWidget-based scenegraph; enforce consistency
                self.use_qml_3d_schema = False
                use_qml_3d = False
                if self.app_logger:
                    self.app_logger.debug(
                        "Legacy UI requested — overriding Qt Quick 3D usage"
                    )
                else:
                    self._log_with_fallback(
                        "debug",
                        "DEBUG: legacy UI requested — overriding Qt Quick 3D usage",
                    )

            window = LegacyMainWindow(use_qml_3d=use_qml_3d)
            if self.app_logger:
                self.app_logger.info(
                    "Legacy UI mode enabled — QML scene initialisation skipped"
                )
            else:
                self._log_with_fallback(
                    "info",
                    "INFO: legacy UI mode enabled — QML scene initialisation skipped",
                )
            return cast(MainWindowProtocol, window)

        from src.ui.main_window import MainWindow as ModernMainWindow

        register_qml_types()

        window_instance = ModernMainWindow(use_qml_3d=use_qml_3d)
        self._check_qml_initialization(window_instance)
        return cast(MainWindowProtocol, window_instance)

    def _create_diagnostics_main_window(
        self, failure_reason: str
    ) -> MainWindowProtocol:
        """Instantiate a diagnostics-aware main window after a startup failure."""

        try:
            diagnostics_window = self._instantiate_main_window(use_qml_3d=False)
        except Exception as diag_exc:  # pragma: no cover - defensive fallback
            self._append_post_diag_trace(f"diagnostics-window-fallback:{diag_exc}")
            from src.ui.main_window_backup import MainWindow as BackupMainWindow

            diagnostics_window = cast(
                MainWindowProtocol, BackupMainWindow(use_qml_3d=False)
            )

        self._schedule_diagnostics_banner(diagnostics_window, failure_reason)
        if hasattr(diagnostics_window, "setWindowTitle"):
            try:
                diagnostics_window.setWindowTitle(
                    "PneumoStabSim (diagnostics mode — QML disabled)"
                )
            except Exception:
                pass
        return diagnostics_window

    def _schedule_diagnostics_banner(
        self, window: MainWindowProtocol, failure_reason: str
    ) -> None:
        """Show a deferred diagnostics notification with retry guidance."""

        QMessageBoxType: Any | None
        try:
            from PySide6.QtWidgets import QMessageBox as QMessageBoxImported
        except Exception:
            QMessageBoxType = None
        else:
            QMessageBoxType = cast(Any, QMessageBoxImported)

        message = (
            "Main window initialisation failed."
            "\nDiagnostics mode is running with the Qt Quick scene disabled."
            "\n\nПричина: "
            f"{failure_reason}"
        )

        if QMessageBoxType is not None:
            try:

                def _show_dialog() -> None:
                    dialog = QMessageBoxType(window)
                    exec_method = getattr(dialog, "exec", None)
                    if not callable(exec_method):
                        self._log_with_fallback(
                            "warning",
                            "WARNING: diagnostics dialog type does not expose exec()",
                        )
                        return
                    dialog.setIcon(QMessageBoxType.Icon.Warning)
                    dialog.setWindowTitle("Диагностика запуска")
                    dialog.setText(message)
                    dialog.setStandardButtons(
                        QMessageBoxType.StandardButton.Retry
                        | QMessageBoxType.StandardButton.Close
                    )
                    result = exec_method()
                    if result == int(QMessageBoxType.StandardButton.Retry):
                        self._retry_main_window_from_banner(window)

                self.QTimer.singleShot(0, _show_dialog)
                return
            except Exception:
                pass

        self._log_with_fallback("warning", f"WARNING: {message}")

    def _retry_main_window_from_banner(
        self, previous_window: MainWindowProtocol
    ) -> None:
        """Retry loading the main window after a diagnostics warning."""

        try:
            new_window = self._instantiate_main_window(
                use_qml_3d=self.use_qml_3d_schema
            )
        except Exception as retry_exc:  # pragma: no cover - diagnostics only
            self._append_post_diag_trace(f"diagnostics-retry-failed:{retry_exc}")
            if self.app_logger:
                self.app_logger.error("Retry failed: %s", retry_exc, exc_info=True)
            else:
                self._log_with_fallback(
                    "error",
                    f"ERROR: retry failed while creating main window: {retry_exc}",
                )
            return

        try:
            previous_window.close()
        except Exception:
            pass

        self.window_instance = new_window
        new_window.show()
        new_window.raise_()
        new_window.activateWindow()

    def _coerce_settings_payload(self, payload: Any) -> dict[str, Any]:
        """Convert settings payload objects into mutable dictionaries."""

        if isinstance(payload, AppSettings):
            return dump_settings(payload)

        raw_dump = getattr(payload, "model_dump", None)
        if callable(raw_dump):
            candidate = raw_dump()
            if isinstance(candidate, dict):
                return candidate

        if isinstance(payload, dict):
            return cast(dict[str, Any], json.loads(json.dumps(payload)))

        return {}

    def _log_runtime_scenegraph_backend(self) -> None:
        """Report the runtime Qt Quick Scene Graph backend selection."""

        if self._is_headless:
            return

        if self.use_legacy_ui:
            if self.app_logger:
                self.app_logger.info(
                    "Legacy UI mode active — no Qt Quick scene graph backend in use"
                )
            else:
                self._log_with_fallback(
                    "info",
                    "INFO: legacy UI mode active — no Qt Quick scene graph backend in use",
                )
            return

        try:
            from PySide6.QtQuick import QQuickWindow, QSGRendererInterface
        except Exception as exc:  # pragma: no cover - optional diagnostic
            if self.app_logger:
                self.app_logger.debug(
                    "Runtime backend log skipped (Qt Quick unavailable): %s", exc
                )
            return

        try:
            backend_value = QQuickWindow.graphicsApi()
            backend_enum = QSGRendererInterface.GraphicsApi(backend_value)
            backend_label = getattr(backend_enum, "name", str(backend_enum))
        except Exception as exc:  # pragma: no cover - defensive guard
            if self.app_logger:
                self.app_logger.debug(
                    "Runtime backend log failed: %s", exc, exc_info=True
                )
            return

        message = f"Qt Quick runtime backend: {backend_label}"
        if self.safe_mode_requested:
            message += " [safe mode]"

        if self.app_logger:
            self.app_logger.info(message)
        else:
            self._log_with_fallback("info", f"INFO: {message}")

    def _resolve_schema_path(self) -> Path:
        return (
            Path(__file__).resolve().parents[1]
            / "schemas"
            / "settings"
            / "app_settings.schema.json"
        )

    def _ensure_schema_integrity(self, schema_path: Path) -> None:
        try:
            with schema_path.open("r", encoding="utf-8") as stream:
                json.load(stream)
        except FileNotFoundError as exc:
            raise SettingsValidationError(
                f"Схема настроек не найдена: {schema_path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise SettingsValidationError(
                f"Схема настроек повреждена: {schema_path} — {exc}"
            ) from exc

        if self.app_logger:
            self.app_logger.debug("Settings schema JSON parsed successfully")

    # ---------------------- Settings auto-migrations ----------------------
    def _auto_migrate_legacy_animation(self, cfg_path: Path) -> None:
        """Перемостить legacy 'graphics.animation' в 'current.animation' и
        'defaults_snapshot.animation' при необходимости.

        Выполняется до строгой валидации. Любые ошибки чтения/записи
        пробрасываются дальше, чтобы не маскировать реальные проблемы.
        """
        try:
            content = cfg_path.read_text(encoding="utf-8")
            data = json.loads(content)
        except Exception:
            return  # Пусть строгая валидация обработает проблему

        changed = False

        def _promote(root_key: str) -> None:
            nonlocal changed
            root = data.get(root_key)
            if not isinstance(root, dict):
                return
            graphics = root.get("graphics")
            if not isinstance(graphics, dict):
                return
            legacy = graphics.pop("animation", None)
            if isinstance(legacy, dict):
                # Не перетираем существующую правильную секцию
                if not isinstance(root.get("animation"), dict):
                    root["animation"] = legacy
                changed = True

        _promote("current")
        _promote("defaults_snapshot")

        if changed:
            tmp = cfg_path.with_suffix(cfg_path.suffix + ".tmp")
            tmp.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            tmp.replace(cfg_path)
            if self.app_logger:
                self.app_logger.info(
                    "Auto-migrated graphics.animation → top-level animation in settings file"
                )

    def _run_schema_validation(self, cfg_path: Path) -> None:
        """Запускает CLI-валидатор JSON схемы для файла настроек."""
        # Определяем корень проекта (src/..)
        project_root = Path(__file__).resolve().parents[1]
        tools_dir = project_root / "tools"
        validator = tools_dir / "validate_settings.py"
        schema_path = self._resolve_schema_path()

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

        try:
            result = subprocess.run(
                command, capture_output=True, text=True, check=False
            )
        except OSError as exc:
            raise RuntimeError(f"Failed to execute settings validator: {exc}") from exc
        if result.returncode != 0:
            output = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(
                f"Validation script failed with exit code {result.returncode}: {output}"
            )

        if self.app_logger:
            self.app_logger.debug("Settings schema validation passed")

    def _validate_settings_file(self) -> None:
        """Строгая валидация конфигурации до создания MainWindow."""
        from src.common.settings_manager import get_settings_manager

        QMessageBoxType: Any | None
        try:
            from PySide6.QtWidgets import QMessageBox as QMessageBoxImported
        except Exception:  # pragma: no cover - headless environments
            QMessageBoxType = None
        else:
            QMessageBoxType = cast(Any, QMessageBoxImported)

        def _fail(
            message: str,
            exc_type: type[Exception] = SettingsValidationError,
        ) -> None:
            if self.app_logger:
                self.app_logger.critical(message)
            if QMessageBoxType is not None:
                QMessageBoxType.critical(None, "Ошибка конфигурации", message)
            else:
                print(f"❌ {message}")
            raise exc_type(message)

        schema_path = self._resolve_schema_path()
        try:
            self._ensure_schema_integrity(schema_path)
        except SettingsValidationError as exc:
            _fail(str(exc))

        sm = get_settings_manager()
        cfg_path = Path(sm.settings_file).absolute()
        project_root = Path(__file__).resolve().parents[1]
        project_cfg = project_root / "config" / "app_settings.json"

        src = determine_settings_source(cfg_path, project_default=project_cfg)
        msg_base = f"Settings file: {cfg_path} [source={src}]"
        print(msg_base)
        if self.app_logger:
            self.app_logger.info(msg_base)

        # Авто-миграции (безопасные и идемпотентные)
        self._auto_migrate_legacy_animation(cfg_path)

        # Основная проверка — всегда строгая
        try:
            validate_settings_file(cfg_path)
        except SettingsValidationError as exc:
            _fail(str(exc), SettingsValidationError)

        # Дополнительная JSON Schema проверка — всегда строгая
        try:
            self._run_schema_validation(cfg_path)
        except RuntimeError as exc:
            _fail(str(exc), SettingsValidationError)

        if self.app_logger:
            self.app_logger.debug("Settings schema and structure validated")

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

        auto_close_timer = self.QTimer(self.window_instance)
        auto_close_timer.setSingleShot(True)
        auto_close_timer.timeout.connect(lambda: self.window_instance.close())
        auto_close_timer.start(5000)
        setattr(self.window_instance, "_auto_close_timer", auto_close_timer)

    def _schedule_safe_exit(
        self,
        *,
        reason: str,
        log_message: str,
        console_message: str,
        timer_ms: int = 0,
    ) -> None:
        """Schedule a graceful Qt shutdown without showing the main window."""

        app_instance = getattr(self, "app_instance", None)
        if app_instance is None:
            return

        if self.app_logger:
            self.app_logger.info(log_message, extra={"reason": reason})
        else:
            print(console_message)

        timer = self.QTimer(app_instance)
        timer.setSingleShot(True)

        def _quit_app() -> None:
            if self.app_logger:
                self.app_logger.info(
                    "Safe shutdown timer triggered", extra={"reason": reason}
                )
            core_app = getattr(self.Qt, "QCoreApplication", None)
            target = None
            if core_app is not None:
                try:
                    target = core_app.instance()
                except Exception:  # pragma: no cover - defensive guard
                    target = None
            if target is None:
                target = app_instance
            if target is not None:
                exit_method = getattr(target, "exit", None)
                if callable(exit_method):
                    exit_method(0)
                    return
                quit_method = getattr(target, "quit", None)
                if callable(quit_method):
                    quit_method()
                    return
            fallback_quit = getattr(app_instance, "quit", None)
            if callable(fallback_quit):
                fallback_quit()

        timer.timeout.connect(_quit_app)
        timer.start(timer_ms)
        self._safe_exit_timer = timer

    def _activate_safe_runtime_mode(self) -> None:
        """Schedule a graceful exit when safe runtime mode is requested."""

        self._schedule_safe_exit(
            reason="safe-runtime",
            log_message="Safe runtime mode: exiting without showing UI (offscreen/headless)",
            console_message="ℹ️ Safe runtime mode: exiting without creating GUI components",
            timer_ms=0,
        )

    def _run_post_diagnostics(self) -> None:
        """Выполнить пост-диагностику логов, импортируя реализацию динамически.

        Динамический импорт позволяет тестам мокаать
        ``src.diagnostics.logs.run_log_diagnostics`` и отслеживать вызов.
        """
        try:
            from src.diagnostics.logs import run_log_diagnostics as _run  # type: ignore
        except Exception:
            return
        try:
            _run()
        except Exception:
            # Никогда не падаем из-за диагностики
            if self.app_logger:
                self.app_logger.warning("Post-diagnostics failed", exc_info=True)

    def run(self, args: Any) -> int:
        """Запустить приложение согласно аргументам CLI."""
        diagnostics_context: list[str] = []
        run_post_diagnostics: bool = False
        env_trace = (os.environ.get("PSS_POST_DIAG_TRACE", "") or "").strip().lower()
        force_post_diag: bool = bool(getattr(args, "diag", False)) or env_trace in {
            "auto",
            "always",
            "1",
            "true",
            "yes",
            "on",
        }
        try:
            # Логирование
            try:
                self.app_logger = self.setup_logging(
                    verbose_console=bool(getattr(args, "verbose", False))
                )
            except TypeError:
                self.app_logger = self.setup_logging(
                    bool(getattr(args, "verbose", False))
                )

            # Заголовок
            self._print_header()

            # Флаги режимов
            self.safe_mode_requested = bool(getattr(args, "safe_mode", False))
            self.safe_cli_mode = bool(getattr(args, "safe_cli_mode", False))
            self.safe_runtime_requested = bool(
                getattr(args, "safe_runtime", False) or getattr(args, "safe", False)
            )
            self.use_legacy_ui = bool(getattr(args, "legacy", False))
            no_qml_requested = bool(getattr(args, "no_qml", False))

            # Применяем --no-qml отдельно от safe
            if self.use_legacy_ui or no_qml_requested:
                self.use_qml_3d_schema = False

            if self.app_logger:
                self.app_logger.info("Logging initialized successfully")
                if getattr(args, "verbose", False):
                    self.app_logger.info("Verbose mode enabled")
                if self.safe_mode_requested:
                    self.app_logger.info(
                        "Safe mode enabled — Qt backend auto-selection active"
                    )
                if self.safe_runtime_requested:
                    if self.safe_cli_mode and not getattr(args, "safe", False):
                        self.app_logger.info(
                            "Safe CLI mode enabled — UI will not be shown",
                            extra={"reason": "cli-safe"},
                        )
                    else:
                        self.app_logger.info(
                            "Safe runtime mode enabled — UI will not be shown"
                        )
                if self.use_legacy_ui:
                    self.app_logger.info("Legacy UI mode requested from CLI")
                if no_qml_requested and not self.use_legacy_ui:
                    self.app_logger.warning(
                        "Qt Quick 3D disabled by --no-qml",
                        extra={"reasons": ["cli:no-qml"]},
                    )

            self._log_startup_environment()

            self.setup_high_dpi()
            self.create_application()
            # Валидация конфига
            self._validate_settings_file()

            if not self.safe_runtime_requested:
                self.create_main_window()
            else:
                if self.safe_cli_mode and not getattr(args, "safe", False):
                    self._schedule_safe_exit(
                        reason="cli-safe",
                        log_message=(
                            "Safe CLI mode: exiting after bootstrap without loading main.qml"
                        ),
                        console_message=(
                            "ℹ️ Safe CLI mode: exiting without loading main.qml"
                        ),
                        timer_ms=0,
                    )
                else:
                    self._activate_safe_runtime_mode()

            print("✅ Ready!")
            print("=" * 60 + "\n")

            self.setup_signals()
            if not self.safe_runtime_requested:
                self.setup_test_mode(args.test_mode)

            if self.app_instance is None:
                raise RuntimeError("QApplication instance is not initialised.")

            result = self.app_instance.exec()

            if self.app_logger:
                self.app_logger.info(f"Application closed with code: {result}")
                self.app_logger.info("=" * 60)

            # Warnings/Errors
            from src.diagnostics.warnings import print_warnings_errors

            print_warnings_errors()
            print(f"\n✅ Application closed (code: {result})\n")
            return int(result)

        except Exception as e:
            print(f"\n❌ FATAL ERROR: {e}")
            import traceback

            traceback.print_exc()
            if self.app_logger:
                self.app_logger.critical(f"FATAL ERROR: {e}")
                self.app_logger.critical(traceback.format_exc())

            from src.diagnostics.warnings import print_warnings_errors

            print_warnings_errors()
            diagnostics_context.append("fatal-error")
            run_post_diagnostics = True
            return 1
        finally:
            try:
                diagnostics_context.append("exit")
                if run_post_diagnostics or force_post_diag:
                    printable_reasons = [
                        reason for reason in diagnostics_context if reason != "exit"
                    ]
                    if printable_reasons:
                        print("📄 Причины запуска пост-диагностики:")
                        for entry in printable_reasons:
                            print(f"   • {entry}")
                    print("\n🔁 Запуск обязательной пост-диагностики логов...\n")
                    self._run_post_diagnostics()
            except Exception as diag_exc:
                self._log_with_fallback(
                    "warning",
                    f"WARNING: не удалось выполнить пост-диагностику логов: {diag_exc}",
                )

    def _print_header(self) -> None:
        """Печать заголовка приложения в консоль."""
        print("=" * 60)
        print("🚀 PNEUMOSTABSIM v5.0.0")
        print("=" * 60)

        try:
            from PySide6.QtCore import qVersion
        except Exception:  # pragma: no cover - headless or PySide6 missing
            qt_version = "unavailable"
        else:
            try:
                qt_version = qVersion()
            except Exception:  # pragma: no cover - defensive branch
                qt_version = "unavailable"

        print(
            f"📊 Python {sys.version_info.major}.{sys.version_info.minor} | Qt {qt_version}"
        )
        print(
            f"🎨 Graphics: Qt Quick 3D | Backend: {os.environ.get('QSG_RHI_BACKEND', 'auto')}"
        )
        print("⏳ Initializing...")

    # ------------------------------------------------------------------
    # QML startup diagnostics
    # ------------------------------------------------------------------
    def _append_post_diag_trace(self, reason: str) -> None:
        """Добавить причину в переменную окружения пост-диагностики."""

        normalized = (reason or "").strip()
        if not normalized:
            return

        existing = os.environ.get("PSS_POST_DIAG_TRACE", "")
        entries = [item for item in existing.split("|") if item]
        if normalized not in entries:
            entries.append(normalized)
            os.environ["PSS_POST_DIAG_TRACE"] = "|".join(entries)

    def _report_qml_issue(self, reason: str, details: str) -> None:
        """Зафиксировать проблему и инициировать пост-диагностику."""

        message = f"QML initialisation issue ({reason}): {details}"
        if self.app_logger:
            self.app_logger.error(message)
        else:
            self._log_with_fallback("warning", f"WARNING: {message}")

        self._append_post_diag_trace(f"qml-check:{reason}")

    @staticmethod
    def _status_matches(widget: Any, status: Any, member: str) -> bool:
        """Сопоставить значение статуса с именованным элементом перечисления."""

        if status is None:
            return False

        member_lower = member.lower()
        name = getattr(status, "name", None)
        if isinstance(name, str) and name.lower() == member_lower:
            return True

        enum_type = getattr(widget, "Status", None)
        if enum_type is not None:
            candidate = getattr(enum_type, member, None)
            if candidate is not None:
                try:
                    if status == candidate:
                        return True
                except Exception:
                    pass
                try:
                    if int(status) == int(candidate):
                        return True
                except Exception:
                    pass

        try:
            status_text = str(status)
        except Exception:
            status_text = None

        if isinstance(status_text, str) and member_lower in status_text.lower():
            return True

        return False

    @staticmethod
    def _format_qml_errors(widget: Any) -> str:
        """Возвращает человеко-читаемое описание ошибок QML."""

        errors_fn = getattr(widget, "errors", None)
        if callable(errors_fn):
            try:
                errors = errors_fn()
            except Exception as exc:  # pragma: no cover - защитный путь
                return f"unable to retrieve errors ({exc})"

            if errors:
                return "; ".join(str(err) for err in errors)

        return "QML engine reported an error without details."

    def _check_qml_initialization(self, window: Any) -> None:
        """Проверяет корректность инициализации QML сцены.

        Поддерживает несколько вариантов контейнера:
        - QQuickWidget (имеет status()/errors())
        - QWidget.createWindowContainer(QQuickView) — проксируемые status()/errors()
        - Диагностические фолбеки (QLabel) — пытаемся найти исходный виджет.
        """

        # Предпочтительно используем явно заданные поля современного окна
        widget = getattr(window, "_qquick_widget", None)
        # Если контейнер отсутствует, но есть QQuickView — используем его
        if (widget is None or not hasattr(widget, "status")) and hasattr(
            window, "_qquick_view"
        ):
            widget = getattr(window, "_qquick_view")

        # Если всё ещё нет контейнера — это явный сбой инициализации
        if widget is None:
            self._report_qml_issue(
                "missing-widget",
                "MainWindow does not expose _qquick_widget/_qquick_view; QML scene is unavailable.",
            )
            return

        # Если это QLabel или любой виджет без status() — пробуем извлечь первопричину
        status_fn = getattr(widget, "status", None)
        if not callable(status_fn):
            # Попробуем найти спрятанный QQuickWidget в центральном виджете
            try:
                central = getattr(window, "centralWidget", None)
                central = central() if callable(central) else central
                if (
                    central is not None
                    and central is not widget
                    and hasattr(central, "findChildren")
                ):
                    candidates = central.findChildren(type(widget))  # type: ignore[arg-type]
                    for c in candidates:
                        if callable(getattr(c, "status", None)):
                            widget = c
                            status_fn = getattr(widget, "status")
                            break
            except Exception:
                pass

        if not callable(status_fn):
            self._report_qml_issue(
                "status-missing",
                f"_qquick_widget of type {type(widget).__name__} does not expose status(); a fallback widget is active.",
            )
            return

        # Нормальный путь: получаем статус и при ошибке логируем детали и import paths
        try:
            status_value = status_fn()
        except Exception as exc:  # pragma: no cover - защитный путь
            self._report_qml_issue(
                "status-query-failed",
                f"Unable to query QML widget status: {exc}",
            )
            return

        if self._status_matches(widget, status_value, "Error"):
            details = self._format_qml_errors(widget)
            # Попробуем дописать import paths из движка
            try:
                engine = None
                if hasattr(widget, "engine"):
                    engine = widget.engine()  # QQuickWidget
                elif hasattr(widget, "qmlEngine"):
                    engine = widget.qmlEngine()  # QQuickView
                if engine is not None and hasattr(engine, "importPathList"):
                    paths = [str(p) for p in engine.importPathList()]
                    details += f" | importPaths={paths}"
            except Exception:
                pass

            self._report_qml_issue("qml-engine-error", details)
            return

        if self._status_matches(widget, status_value, "Null"):
            self._report_qml_issue(
                "qml-null-status",
                "QML view returned a Null status after initialisation.",
            )
            return

        if not self._status_matches(widget, status_value, "Ready"):
            # Для статусов Loading/Nullish ждём финальное состояние без предупреждений.
            return

        root_object = getattr(window, "_qml_root_object", None)
        if root_object is None:
            self._report_qml_issue(
                "root-missing",
                "QML root object was not created; interactive scene is unavailable.",
            )
