"""State Sync Module - State synchronization and persistence

Модуль синхронизации и сохранения состояния окна.
Управляет настройками QSettings, геометрией окна, состоянием сплиттеров.

Russian comments / English code.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict

from PySide6.QtCore import QByteArray, QSettings

if TYPE_CHECKING:
    from .main_window import MainWindow


class StateSync:
    """Синхронизация состояния главного окна

    Управляет:
    - Сохранением/восстановлением геометрии
    - Состоянием сплиттеров
    - Выбранной вкладкой
    - Начальной синхронизацией Python→QML

    Static methods для делегирования из MainWindow.
    """

    logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Settings Persistence
    # ------------------------------------------------------------------
    @staticmethod
    def restore_settings(window: MainWindow) -> None:
        """Восстановить настройки окна из QSettings

        Restores:
        - Window geometry
        - Window state
        - Splitter sizes
        - Last selected tab

        Args:
            window: MainWindow instance
        """
        settings = QSettings(window.SETTINGS_ORG, window.SETTINGS_APP)

        # Restore geometry
        geom = settings.value(window.SETTINGS_GEOMETRY)
        if isinstance(geom, QByteArray):
            window.restoreGeometry(geom)
        elif isinstance(geom, (bytes, bytearray)):
            window.restoreGeometry(QByteArray(geom))

        # Restore state
        state = settings.value(window.SETTINGS_STATE)
        if isinstance(state, QByteArray):
            window.restoreState(state)
        elif isinstance(state, (bytes, bytearray)):
            window.restoreState(QByteArray(state))

        # Restore vertical splitter
        split = settings.value(window.SETTINGS_SPLITTER)
        if window.main_splitter and isinstance(split, QByteArray):
            window.main_splitter.restoreState(split)
        elif window.main_splitter and isinstance(split, (bytes, bytearray)):
            window.main_splitter.restoreState(QByteArray(split))

        # Restore horizontal splitter
        hsplit = settings.value(window.SETTINGS_HORIZONTAL_SPLITTER)
        if window.main_horizontal_splitter and isinstance(hsplit, QByteArray):
            window.main_horizontal_splitter.restoreState(hsplit)
        elif window.main_horizontal_splitter and isinstance(hsplit, (bytes, bytearray)):
            window.main_horizontal_splitter.restoreState(QByteArray(hsplit))

        StateSync.logger.debug("✅ Settings restored")

    @staticmethod
    def save_settings(window: MainWindow) -> None:
        """Сохранить настройки окна в QSettings

        Saves:
        - Window geometry
        - Window state
        - Splitter sizes

        Args:
            window: MainWindow instance
        """
        # 1) Сохраняем UI-состояние (QSettings)
        settings = QSettings(window.SETTINGS_ORG, window.SETTINGS_APP)
        settings.setValue(window.SETTINGS_GEOMETRY, window.saveGeometry())
        settings.setValue(window.SETTINGS_STATE, window.saveState())
        if window.main_splitter:
            settings.setValue(
                window.SETTINGS_SPLITTER, window.main_splitter.saveState()
            )
        if window.main_horizontal_splitter:
            settings.setValue(
                window.SETTINGS_HORIZONTAL_SPLITTER,
                window.main_horizontal_splitter.saveState(),
            )

        # 2) Сохраняем JSON-конфиг через SettingsManager (без заглушек)
        try:
            from src.common.settings_manager import get_settings_manager

            sm = get_settings_manager()

            # Собираем состояния панелей при наличии публичного API
            if getattr(window, "graphics_panel", None) and hasattr(
                window.graphics_panel, "collect_state"
            ):
                g = window.graphics_panel.collect_state()
                sm.set_category("graphics", g, auto_save=False)
            if getattr(window, "geometry_panel", None) and hasattr(
                window.geometry_panel, "collect_state"
            ):
                geo = window.geometry_panel.collect_state()
                sm.set_category("geometry", geo, auto_save=False)
            if getattr(window, "pneumo_panel", None) and hasattr(
                window.pneumo_panel, "collect_state"
            ):
                pneu = window.pneumo_panel.collect_state()
                sm.set_category("pneumatic", pneu, auto_save=False)
            if getattr(window, "modes_panel", None) and hasattr(
                window.modes_panel, "collect_state"
            ):
                modes = window.modes_panel.collect_state()
                sm.set_category("modes", modes, auto_save=False)

            # Пишем один раз
            sm.save()
            StateSync.logger.info("✅ app_settings.json saved on exit")
        except Exception as e:
            # Не скрываем ошибку — поднимаем дальше
            StateSync.logger.critical(f"❌ Failed to save app_settings.json: {e}")
            raise

    # ------------------------------------------------------------------
    # Initial Synchronization
    # ------------------------------------------------------------------
    @staticmethod
    def initial_full_sync(window: MainWindow) -> None:
        """Полная начальная синхронизация Python→QML

        Sends all graphics settings to QML to override any defaults.
        Prevents hidden QML defaults from affecting visualization.

        Args:
            window: MainWindow instance
        """
        from .qml_bridge import QMLBridge

        # Мягкий сброс вида (если реализовано в QML)
        try:
            QMLBridge.invoke_qml_function(window, "fullResetView")
        except Exception:
            pass

        if not getattr(window, "graphics_panel", None):
            return

        try:
            # ✅ Берём полное состояние из публичного API панели (без автодефолтов)
            full_state: Dict[str, Any] = {}
            try:
                if hasattr(window.graphics_panel, "collect_state"):
                    full_state = window.graphics_panel.collect_state() or {}
                elif hasattr(window.graphics_panel, "get_state"):
                    full_state = window.graphics_panel.get_state() or {}
            except Exception as ex:
                StateSync.logger.warning(f"GraphicsPanel state read failed: {ex}")
                full_state = {}

            if not isinstance(full_state, dict) or not full_state:
                StateSync.logger.info("No graphics state to sync on startup")
                return

            # ✅ Пытаемся отправить одним батчем
            if QMLBridge._push_batched_updates(window, full_state):
                window._last_batched_updates = full_state
                StateSync.logger.info("Initial full sync pushed as batch")
                return

            # 🔁 Fallback: по категориям
            for cat, payload in full_state.items():
                if not isinstance(payload, dict):
                    continue
                methods = QMLBridge.QML_UPDATE_METHODS.get(str(cat), ())
                sent = False
                for m in methods:
                    if QMLBridge.invoke_qml_function(window, m, payload):
                        sent = True
                        break
                # Лог в GraphicsLogger (если доступен)
                QMLBridge._log_graphics_change(window, str(cat), payload, applied=sent)

            StateSync.logger.info("✅ Initial full sync completed")
        except Exception as e:
            StateSync.logger.error(f"Initial full sync failed: {e}")

    # ------------------------------------------------------------------
    # UI Layout Reset
    # ------------------------------------------------------------------
    @staticmethod
    def reset_ui_layout(window: MainWindow) -> None:
        """Сбросить расположение UI к дефолтным значениям

        Resets:
        - Vertical splitter (3D:Charts = 3:2)
        - Horizontal splitter (Scene:Panels = 3:1)

        Args:
            window: MainWindow instance
        """
        if window.main_splitter:
            window.main_splitter.setSizes([3, 2])

        if window.main_horizontal_splitter:
            window.main_horizontal_splitter.setSizes([3, 1])

        if hasattr(window, "status_bar") and window.status_bar:
            window.status_bar.showMessage("Макет интерфейса сброшен", 2000)

        StateSync.logger.info("UI layout reset to defaults")
