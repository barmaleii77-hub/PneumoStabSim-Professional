"""Menu Actions Module - Menu and toolbar action handlers

Модуль обработчиков действий меню и панели инструментов.
Содержит callback-функции для всех пунктов меню.

Russian comments / English code.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from PySide6.QtCore import Slot

if TYPE_CHECKING:
    from .main_window_refactored import MainWindow

from .signals_router import SignalsRouter


class MenuActions:
    """Обработчики действий меню и toolbar

    Содержит callback-функции для:
    - Управления файлами
    - Управления видом
    - Управления симуляцией
    - Обновления рендера

    Static methods для делегирования из MainWindow.
    """

    logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # File Menu Actions
    # ------------------------------------------------------------------
    @staticmethod
    def file_exit(window: MainWindow) -> None:
        """Exit application

        Args:
            window: MainWindow instance
        """
        window.close()

    # ------------------------------------------------------------------
    # View Menu Actions
    # ------------------------------------------------------------------
    @staticmethod
    def view_reset_layout(window: MainWindow) -> None:
        """Reset UI layout to defaults

        Args:
            window: MainWindow instance
        """
        from .state_sync import StateSync

        StateSync.reset_ui_layout(window)

    # ------------------------------------------------------------------
    # Tab Management
    # ------------------------------------------------------------------
    @staticmethod
    @Slot(int)
    def on_tab_changed(window: MainWindow, index: int) -> None:
        """Handle tab change event

        Saves selected tab index to QSettings.

        Args:
            window: MainWindow instance
            index: New tab index
        """
        from PySide6.QtCore import QSettings

        settings = QSettings(window.SETTINGS_ORG, window.SETTINGS_APP)
        settings.setValue(window.SETTINGS_LAST_TAB, index)

        tab_names = [
            "Геометрия",
            "ПневмоСистема",
            "Режимы стабилизатора",
            "Графика и визуализация",
            "Динамика движения",
        ]

        if 0 <= index < len(tab_names):
            MenuActions.logger.debug(f"Переключено на вкладку: {tab_names[index]}")

    # ------------------------------------------------------------------
    # Render Update
    # ------------------------------------------------------------------
    @staticmethod
    def update_render(window: MainWindow) -> None:
        """Периодический тик UI/анимации (~60 FPS)

        Updates:
        - QML animation time
        - Queue statistics

        Args:
            window: MainWindow instance
        """
        if not window._qml_root_object:
            return

        # Update animation time
        now = time.perf_counter()
        last_tick = getattr(window, "_last_animation_tick", None)
        window._last_animation_tick = now

        try:
            is_running = bool(window._qml_root_object.property("isRunning"))
            if is_running and last_tick is not None:
                elapsed = now - last_tick
                current = float(
                    window._qml_root_object.property("animationTime") or 0.0
                )
                window._qml_root_object.setProperty(
                    "animationTime", current + float(elapsed)
                )
        except Exception:
            pass

        # Update queue statistics
        try:
            if hasattr(window.simulation_manager, "get_queue_stats"):
                stats = window.simulation_manager.get_queue_stats()
                get_c = stats.get("get_count", 0)
                put_c = stats.get("put_count", 0)

                if hasattr(window, "queue_label") and window.queue_label:
                    window.queue_label.setText(f"Queue: {get_c}/{put_c}")
        except Exception:
            if hasattr(window, "queue_label") and window.queue_label:
                window.queue_label.setText("Queue: -/-")

        # Update snapshots
        try:
            if hasattr(window.simulation_manager, "get_snapshot_info"):
                info = window.simulation_manager.get_snapshot_info()
                if info and hasattr(window, "snapshot_label") and window.snapshot_label:
                    window.snapshot_label.setText(info)
        except Exception:
            if hasattr(window, "snapshot_label") and window.snapshot_label:
                window.snapshot_label.setText("Snapshot: None")

        # Fetch and push the latest snapshot to QML (SI units)
        latest_snapshot = None
        try:
            if (
                hasattr(window, "simulation_manager")
                and window.simulation_manager is not None
                and hasattr(window.simulation_manager, "get_latest_state")
            ):
                latest_snapshot = window.simulation_manager.get_latest_state()
        except Exception as exc:
            MenuActions.logger.debug(
                "Latest snapshot retrieval failed: %s", exc, exc_info=exc
            )

        if latest_snapshot is not None:
            window.current_snapshot = latest_snapshot

        SignalsRouter._queue_simulation_update(
            window, getattr(window, "current_snapshot", None)
        )
