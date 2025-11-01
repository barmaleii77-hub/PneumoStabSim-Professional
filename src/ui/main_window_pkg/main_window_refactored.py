"""MainWindow Coordinator - Refactored modular version

Главное окно приложения - модульная версия v4.9.5.
Тонкий координатор, делегирующий работу специализированным модулям.

**Coordinator Pattern:**
- Минимум логики в главном классе
- Делегирование специализированным модулям
- Четкое разделение ответственности

**Delegation:**
- UI construction → UISetup
- Python↔QML → QMLBridge
- Signal routing → SignalsRouter
- State sync → StateSync
- Menu actions → MenuActions

Russian UI / English code.
"""

from __future__ import annotations

import copy
import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import QMainWindow, QLabel
from PySide6.QtCore import Qt, QTimer, Slot, QUrl
from PySide6.QtQuickWidgets import QQuickWidget
from pathlib import Path

# Локальные модули
from .ui_setup import UISetup
from .qml_bridge import QMLBridge
from .signals_router import SignalsRouter
from .state_sync import StateSync
from .menu_actions import MenuActions
from .profile_service import ProfileService
from ._hdr_paths import normalise_hdr_path
from src.common.settings_manager import get_settings_manager
from src.common.signal_trace import get_signal_trace_service
from src.core.settings_manager import ProfileSettingsManager


class MainWindow(QMainWindow):
    """Главное окно приложения - REFACTORED v4.9.5

    Координатор с минимальной логикой, делегирует работу модулям.

    **Модули:**
    - UISetup: Построение UI
    - QMLBridge: Python↔QML
    - SignalsRouter: Сигналы
    - StateSync: Синхронизация состояния
    - MenuActions: Обработчики меню
    """

    # QSettings keys
    SETTINGS_ORG = "PneumoStabSim"
    SETTINGS_APP = "PneumoStabSimApp"
    SETTINGS_GEOMETRY = "MainWindow/Geometry"
    SETTINGS_STATE = "MainWindow/State"
    SETTINGS_SPLITTER = "MainWindow/Splitter"
    SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"
    SETTINGS_LAST_TAB = "MainWindow/LastTab"
    SETTINGS_LAST_PRESET = "Presets/LastPath"

    # QML update methods (for QMLBridge)
    QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
        "geometry": ("applyGeometryUpdates", "updateGeometry"),
        "animation": (
            "applyAnimationUpdates",
            "updateAnimation",
            "applyAnimParamsUpdates",
            "updateAnimParams",
        ),
        "lighting": ("applyLightingUpdates", "updateLighting"),
        "materials": ("applyMaterialUpdates", "updateMaterials"),
        "environment": ("applyEnvironmentUpdates", "updateEnvironment"),
        "quality": ("applyQualityUpdates", "updateQuality"),
        "camera": ("applyCameraUpdates", "updateCamera"),
        "effects": ("applyEffectsUpdates", "updateEffects"),
    }

    # Wheel key mapping
    WHEEL_KEY_MAP = {
        "LP": "fl",
        "PP": "fr",
        "LZ": "rl",
        "PZ": "rr",
    }

    def __init__(self, use_qml_3d: bool = True) -> None:
        """Инициализация главного окна

        Args:
            use_qml_3d: Use Qt Quick 3D backend (True) or legacy OpenGL
        """
        super().__init__()

        # Store config
        self.use_qml_3d = use_qml_3d

        # Window setup
        backend_name = "Qt Quick 3D (main.qml v4.3)" if use_qml_3d else "Legacy OpenGL"
        self.setWindowTitle(f"PneumoStabSim - {backend_name}")
        self.resize(1400, 900)
        self.setMinimumSize(1200, 800)
        self.setWindowState(Qt.WindowState.WindowNoState)

        # Logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"MainWindow init: {backend_name}")

        # Settings manager
        self.settings_manager = get_settings_manager()
        self.logger.info("SettingsManager initialized")

        self.profile_manager = ProfileSettingsManager(
            self.settings_manager,
            apply_callback=self._apply_settings_update,
        )
        self.logger.info("ProfileSettingsManager initialized")

        self.profile_service = ProfileService(self.profile_manager)
        try:
            self.profile_service.refresh()
        except Exception as profile_exc:
            self.logger.debug(
                "ProfileService initial refresh failed: %s",
                profile_exc,
                exc_info=profile_exc,
            )

        self.signal_trace_service = None
        try:
            self.signal_trace_service = get_signal_trace_service()
            try:
                initial_signal_trace = (
                    self.settings_manager.get("diagnostics.signal_trace", {}) or {}
                )
            except Exception:
                initial_signal_trace = {}
            self.signal_trace_service.update_from_settings(initial_signal_trace)
            self.logger.debug("SignalTraceService configured from settings")
        except Exception as exc:
            self.signal_trace_service = None
            self.logger.debug("SignalTraceService unavailable: %s", exc, exc_info=exc)

        # IBL Logger
        from ..ibl_logger import get_ibl_logger, log_ibl_event

        self.ibl_logger = get_ibl_logger()
        log_ibl_event("INFO", "MainWindow", "IBL Logger initialized")

        # Event Logger (Python↔QML)
        from src.common.event_logger import get_event_logger

        self.event_logger = get_event_logger()
        self.logger.info("EventLogger initialized")

        # Simulation Manager
        from ...runtime import SimulationManager

        try:
            self.simulation_manager = SimulationManager(self)
            self.logger.info("✅ SimulationManager created")
        except Exception as e:
            self.logger.exception(f"❌ SimulationManager creation failed: {e}")
            raise

        # QML update system
        self._suppress_qml_feedback = False
        self._qml_update_queue: Dict[str, Dict[str, Any]] = {}
        self._qml_method_support: Dict[tuple[str, bool], bool] = {}
        self._qml_flush_timer = QTimer()
        self._qml_flush_timer.setSingleShot(True)
        self._qml_flush_timer.timeout.connect(self._flush_qml_updates)
        self._qml_pending_property_supported: Optional[bool] = None
        self._last_batched_updates: Optional[Dict[str, Any]] = None
        self._last_camera_payload: Dict[str, Any] = {}

        # State tracking
        from ...runtime import StateSnapshot

        self.current_snapshot: Optional[StateSnapshot] = None
        self.is_simulation_running = False
        self._sim_started = False

        # Geometry converter
        from ..geometry_bridge import create_geometry_converter

        self.geometry_converter = create_geometry_converter()
        self.logger.info("✅ GeometryBridge created")

        # UI references (initialized by UISetup)
        self.geometry_panel = None
        self.pneumo_panel = None
        self.modes_panel = None
        self.road_panel = None
        self.graphics_panel = None
        self._graphics_panel = None  # Alias
        self.chart_widget = None
        self.tab_widget = None
        self.main_splitter = None
        self.main_horizontal_splitter = None
        self._qquick_widget: Optional[QQuickWidget] = None
        self._qml_root_object = None
        self._qml_base_dir: Optional[Path] = None

        # Status bar labels (initialized by UISetup)
        self.sim_time_label: Optional[QLabel] = None
        self.step_count_label: Optional[QLabel] = None
        self.fps_label: Optional[QLabel] = None
        self.queue_label: Optional[QLabel] = None
        self.status_bar = None

        # ====== BUILD UI ======
        self.logger.info("Building UI...")

        UISetup.setup_central(self)
        self.logger.info("  ✅ Central view setup")

        UISetup.setup_tabs(self)
        self.logger.info("  ✅ Tabs setup")

        UISetup.setup_menus(self)
        self.logger.info("  ✅ Menus setup")

        UISetup.setup_toolbar(self)
        self.logger.info("  ✅ Toolbar setup")

        UISetup.setup_status_bar(self)
        self.logger.info("  ✅ Status bar setup")

        # ====== CONNECT SIGNALS ======
        SignalsRouter.connect_all_signals(self)
        self.logger.info("  ✅ Signals connected")

        # ====== RENDER TIMER ======
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self._update_render)
        self.render_timer.start(16)  # ~60 FPS
        self.logger.info("  ✅ Render timer started")

        # ====== RESTORE SETTINGS ======
        StateSync.restore_settings(self)
        self.logger.info("  ✅ Settings restored")

        # ====== INITIAL SYNC ======
        StateSync.initial_full_sync(self)
        self.logger.info("  ✅ Initial sync completed")

        self.logger.info("✅ MainWindow initialization complete")

    # ------------------------------------------------------------------
    # QML Event Logging (exposed to QML)
    # ------------------------------------------------------------------
    @Slot(str, str)
    def logQmlEvent(self, event_type: str, name: str) -> None:
        """Логирование QML событий через EventLogger

        Args:
            event_type: Event type (signal_received, function_called, etc.)
            name: Signal/function name
        """
        try:
            from src.common.event_logger import EventType

            etype_norm = (event_type or "").strip().lower()
            if etype_norm == "signal_received":
                etype = EventType.SIGNAL_RECEIVED
            elif etype_norm == "function_called":
                etype = EventType.FUNCTION_CALLED
            elif etype_norm == "property_changed":
                etype = EventType.PROPERTY_CHANGED
            else:
                etype = EventType.FUNCTION_CALLED

            self.event_logger.log_event(
                event_type=etype,
                component="main.qml",
                action=name,
                source="qml",
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Settings synchronization helpers
    # ------------------------------------------------------------------
    def _apply_settings_update(
        self, category_path: str, updates: Dict[str, Any]
    ) -> None:
        """Merge updates into SettingsManager and log diffs."""

        if not updates:
            return

        sm = getattr(self, "settings_manager", None)
        if sm is None or not isinstance(updates, dict):
            return

        try:
            current_state = sm.get(category_path, {}) or {}
        except Exception:
            current_state = {}

        if not isinstance(current_state, dict):
            current_state = {}

        before = copy.deepcopy(current_state)
        merged = copy.deepcopy(before)
        self._deep_merge_dicts(merged, updates)

        if merged == before:
            return

        sm.set(category_path, merged, auto_save=False)

        if self.signal_trace_service is not None and category_path.startswith(
            "diagnostics"
        ):
            try:
                config_payload = sm.get("diagnostics.signal_trace", {}) or {}
                self.signal_trace_service.update_from_settings(config_payload)
            except Exception as exc:
                self.logger.debug(
                    "Failed to push diagnostics settings to SignalTraceService: %s",
                    exc,
                )

        try:
            for path, old_value, new_value in self._iter_diff(before, merged):
                self.event_logger.log_state_change(
                    category_path,
                    path,
                    old_value,
                    new_value,
                )
        except Exception:
            self.logger.debug(
                "Failed to log state change for %s", category_path, exc_info=True
            )

        try:
            sm.save()
        except Exception as exc:  # pragma: no cover - disk errors
            self.logger.error("Failed to save settings for %s: %s", category_path, exc)

    @staticmethod
    def _deep_merge_dicts(target: Dict[str, Any], updates: Dict[str, Any]) -> None:
        for key, value in updates.items():
            if isinstance(value, dict):
                base = target.get(key)
                if not isinstance(base, dict):
                    base = {}
                target[key] = base
                MainWindow._deep_merge_dicts(base, value)
            else:
                target[key] = copy.deepcopy(value)

    @staticmethod
    def _iter_diff(
        old: Any, new: Any, prefix: str = ""
    ) -> "list[tuple[str, Any, Any]]":
        diffs: list[tuple[str, Any, Any]] = []
        if isinstance(old, dict) and isinstance(new, dict):
            keys = set(old) | set(new)
            for key in keys:
                child_prefix = f"{prefix}.{key}" if prefix else str(key)
                diffs.extend(
                    MainWindow._iter_diff(old.get(key), new.get(key), child_prefix)
                )
            return diffs

        if old != new:
            diffs.append((prefix, old, new))
        return diffs

    @Slot(str, dict)
    def applyQmlConfigChange(self, category: str, payload: Dict[str, Any]) -> None:
        """Приём изменений конфигурации из QML."""

        if not isinstance(payload, dict):
            return

        category_path = (category or "").strip()
        if not category_path:
            return

        if not category_path.startswith("graphics"):
            if category_path in {"animation", "scene", "materials"}:
                category_path = f"graphics.{category_path}"

        self._apply_settings_update(category_path, payload)

    @Slot(result=bool)
    def isQmlFeedbackSuppressed(self) -> bool:
        """Expose suppression flag to QML side."""

        return bool(getattr(self, "_suppress_qml_feedback", False))

    # ------------------------------------------------------------------
    # QML Update System (delegation to QMLBridge)
    # ------------------------------------------------------------------
    def _flush_qml_updates(self) -> None:
        """Flush queued QML updates → QMLBridge"""
        QMLBridge.flush_updates(self)

    def _queue_qml_update(self, key: str, params: Dict[str, Any]) -> None:
        """Queue QML update → QMLBridge"""
        QMLBridge.queue_update(self, key, params)

    # ------------------------------------------------------------------
    # Signal Handlers (delegation to SignalsRouter)
    # ------------------------------------------------------------------
    @Slot(dict)
    def _on_geometry_changed_qml(self, params: Dict[str, Any]) -> None:
        """Geometry changed → direct QML call"""
        if not isinstance(params, dict):
            return

        self.logger.info(f"Geometry update: {len(params)} keys")

        if not QMLBridge.invoke_qml_function(self, "applyGeometryUpdates", params):
            QMLBridge.queue_update(self, "geometry", params)

        if hasattr(self, "status_bar") and self.status_bar:
            self.status_bar.showMessage("Геометрия обновлена", 2000)

    @Slot(dict)
    def _on_lighting_changed(self, params: Dict[str, Any]) -> None:
        """Lighting changed → SignalsRouter"""
        SignalsRouter.handle_lighting_changed(self, params)

    @Slot(dict)
    def _on_material_changed(self, params: Dict[str, Any]) -> None:
        """Material changed → SignalsRouter"""
        SignalsRouter.handle_material_changed(self, params)

    @Slot(dict)
    def _on_environment_changed(self, params: Dict[str, Any]) -> None:
        """Environment changed → SignalsRouter"""
        SignalsRouter.handle_environment_changed(self, params)

    @Slot(dict)
    def _on_quality_changed(self, params: Dict[str, Any]) -> None:
        """Quality changed → SignalsRouter"""
        SignalsRouter.handle_quality_changed(self, params)

    @Slot(dict)
    def _on_camera_changed(self, params: Dict[str, Any]) -> None:
        """Camera changed → SignalsRouter"""
        SignalsRouter.handle_camera_changed(self, params)

    @Slot(dict)
    def _on_effects_changed(self, params: Dict[str, Any]) -> None:
        """Effects changed → SignalsRouter"""
        SignalsRouter.handle_effects_changed(self, params)

    @Slot(bool)
    def _on_animation_toggled(self, running: bool) -> None:
        """Animation toggled in QML → persist settings"""
        SignalsRouter.handle_animation_toggled(self, bool(running))

    @Slot(dict)
    def _on_preset_applied(self, full_state: Dict[str, Any]) -> None:
        """Preset applied → SignalsRouter"""
        SignalsRouter.handle_preset_applied(self, full_state)

    @Slot(dict)
    def _on_animation_changed(self, params: Dict[str, Any]) -> None:
        """Animation changed → SignalsRouter"""
        SignalsRouter.handle_animation_changed(self, params)

    @Slot(str)
    def _on_sim_control(self, command: str) -> None:
        """Simulation control → SignalsRouter"""
        SignalsRouter.handle_sim_control(self, command)

    @Slot(object)
    def _on_state_update(self, snapshot) -> None:
        """State update → SignalsRouter"""
        SignalsRouter.handle_state_update(self, snapshot)

    @Slot(str)
    def _on_physics_error(self, message: str) -> None:
        """Physics error → SignalsRouter"""
        SignalsRouter.handle_physics_error(self, message)

    @Slot(str)
    def logIblEvent(self, message: str) -> None:
        """Expose QML logging hook for IBL loader components."""
        try:
            if hasattr(self, "ibl_logger") and self.ibl_logger:
                self.ibl_logger.info(message)
            else:
                self.logger.info("IBL:%s", message)
        except Exception:
            self.logger.debug("Failed to log IBL event", exc_info=True)

    @Slot(str, result=str)
    def normalizeHdrPath(self, value: str) -> str:
        """Normalise HDR paths received from QML into absolute file URLs."""

        raw_value = (value or "").strip()
        if not raw_value:
            return ""

        try:
            url_candidate = QUrl(raw_value)
            if url_candidate.isValid():
                scheme = url_candidate.scheme()
                if scheme and scheme not in ("file", ""):
                    return url_candidate.toString()
                if url_candidate.isLocalFile():
                    return url_candidate.toString()
        except Exception:
            self.logger.debug("normalizeHdrPath: invalid URL candidate", exc_info=True)

        try:
            project_root = Path(__file__).resolve().parents[3]
        except Exception:
            project_root = Path.cwd()

        try:
            return normalise_hdr_path(
                raw_value,
                qml_base_dir=self._qml_base_dir,
                project_root=project_root,
                logger=self.logger,
            )
        except Exception:
            self.logger.debug(
                "normalizeHdrPath: failed to normalise path %s",
                raw_value,
                exc_info=True,
            )
            return raw_value

    @Slot(dict)
    def _on_qml_batch_ack(self, summary: Dict[str, Any]) -> None:
        """QML batch ACK → QMLBridge"""
        QMLBridge.handle_qml_ack(self, summary)

    @Slot(int)
    def _on_tab_changed(self, index: int) -> None:
        """Tab changed → MenuActions"""
        MenuActions.on_tab_changed(self, index)

    # ------------------------------------------------------------------
    # Render Update
    # ------------------------------------------------------------------
    def _update_render(self) -> None:
        """Render tick → MenuActions"""
        MenuActions.update_render(self)

    # ------------------------------------------------------------------
    # Menu Actions
    # ------------------------------------------------------------------
    def _reset_ui_layout(self) -> None:
        """Reset UI layout → StateSync"""
        StateSync.reset_ui_layout(self)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Close event → save settings"""
        try:
            StateSync.save_settings(self)
        except Exception as e:
            try:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.critical(
                    self,
                    "Ошибка сохранения настроек",
                    f"Не удалось сохранить config/app_settings.json:\n{e}",
                )
            except Exception:
                pass
            # Прерываем закрытие, чтобы не терять состояние молча
            try:
                event.ignore()
                return
            except Exception:
                pass
        super().closeEvent(event)
