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
        settings = QSettings(window.SETTINGS_ORG, window.SETTINGS_APP)
        settings.setValue(window.SETTINGS_GEOMETRY, window.saveGeometry())
        settings.setValue(window.SETTINGS_STATE, window.saveState())
        
        if window.main_splitter:
            settings.setValue(
                window.SETTINGS_SPLITTER,
                window.main_splitter.saveState()
            )
        
        if window.main_horizontal_splitter:
            settings.setValue(
                window.SETTINGS_HORIZONTAL_SPLITTER,
                window.main_horizontal_splitter.saveState()
            )
        
        StateSync.logger.debug("✅ Settings saved")
    
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
        
        # Reset QML defaults first
        try:
            QMLBridge.invoke_qml_function(window, "fullResetView")
        except Exception:
            pass
        
        if not window.graphics_panel:
            return
        
        try:
            pending: Dict[str, Any] = {}
            
            # Gather all graphics settings
            pending["lighting"] = window.graphics_panel._prepare_lighting_payload()
            pending["environment"] = window.graphics_panel._prepare_environment_payload()
            pending["materials"] = window.graphics_panel._prepare_materials_payload()
            pending["quality"] = window.graphics_panel._prepare_quality_payload()
            pending["camera"] = window.graphics_panel._prepare_camera_payload()
            pending["effects"] = window.graphics_panel._prepare_effects_payload()
            
            # Send as batch
            if not QMLBridge._push_batched_updates(window, pending):
                # Fallback: individual calls
                for cat, payload in pending.items():
                    methods = QMLBridge.QML_UPDATE_METHODS.get(cat, ())
                    sent = False
                    for m in methods:
                        if QMLBridge.invoke_qml_function(window, m, payload):
                            sent = True
                            break
                    QMLBridge._log_graphics_change(window, cat, payload, applied=sent)
            else:
                # Wait for ACK
                window._last_batched_updates = pending
            
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
