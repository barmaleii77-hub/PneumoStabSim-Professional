"""State Sync Module - State synchronization and persistence

Модуль синхронизации и сохранения состояния окна.
Управляет настройками QSettings, геометрией окна, состоянием сплиттеров.

Russian comments / English code.
"""
from __future__ import annotations

import logging
from pathlib import Path
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
        
        # Мягкий сброс вида (если реализовано в QML)
        try:
            QMLBridge.invoke_qml_function(window, "fullResetView")
        except Exception:
            pass
        
        if not getattr(window, "graphics_panel", None):
            return
        
        try:
            # ✅ Берём полное состояние из публичного API панели
            full_state: Dict[str, Any] = {}
            try:
                if hasattr(window.graphics_panel, "collect_state"):
                    full_state = window.graphics_panel.collect_state() or {}
                elif hasattr(window.graphics_panel, "get_state"):
                    # Fallback: некоторые панели могут иметь get_state()
                    full_state = window.graphics_panel.get_state() or {}
            except Exception as ex:
                StateSync.logger.warning(f"GraphicsPanel state read failed: {ex}")
                full_state = {}
            
            # ✅ Инициализация окружения по умолчанию (HDR IBL и skybox)
            env = full_state.get("environment") if isinstance(full_state.get("environment"), dict) else {}
            changed_env = False
            try:
                hdr_dir = Path("assets/hdr")
                qml_dir = Path("assets/qml").resolve()
                if (not env) or (not env.get("ibl_source")):
                    # Ищем первый HDR файл
                    hdr_path: Path | None = None
                    if hdr_dir.exists():
                        for p in hdr_dir.glob("*.hdr"):
                            hdr_path = p
                            break
                    if hdr_path:
                        rel = (hdr_path.resolve().relative_to(qml_dir)).as_posix() if hdr_path.is_absolute() else ("../hdr/" + hdr_path.name)
                        env = env or {}
                        env.setdefault("background_mode", "skybox")
                        env.setdefault("skybox_enabled", True)
                        env.setdefault("ibl_enabled", True)
                        env.setdefault("ibl_intensity", 1.0)
                        env.setdefault("ibl_rotation", 0.0)
                        env["ibl_source"] = rel
                        # fallback = тот же файл (или другой, если есть)
                        env.setdefault("ibl_fallback", rel)
                        full_state["environment"] = env
                        changed_env = True
            except Exception:
                pass
            
            if not isinstance(full_state, dict) or not full_state:
                StateSync.logger.info("No graphics state to sync on startup")
                return
            
            # ✅ Пытаемся отправить одним батчем
            if QMLBridge._push_batched_updates(window, full_state):
                window._last_batched_updates = full_state
                StateSync.logger.info("Initial full sync pushed as batch" + (" (env defaults applied)" if changed_env else ""))
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
            
            StateSync.logger.info("✅ Initial full sync completed" + (" (env defaults applied)" if changed_env else ""))
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
