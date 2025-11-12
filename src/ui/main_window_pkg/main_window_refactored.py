"""MainWindow Coordinator - Refactored modular version

Главное окно приложения - модульная версия v4.9.9.
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
import json
import logging
from datetime import datetime, timezone
from typing import Any

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
from src.services import FeedbackService
from src.ui.feedback import FeedbackController
from src.ui.bridge.telemetry_bridge import TelemetryDataBridge

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SHADER_STATUS_LOG_PATH = (
    PROJECT_ROOT / "reports" / "graphics" / "shader_status_dump.json"
)


class MainWindow(QMainWindow):
    """Главное окно приложения - REFACTORED v4.9.9

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
    QML_UPDATE_METHODS: dict[str, tuple[str, ...]] = {
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

        # Geometry payload cache for dependency corrections
        self._last_geometry_payload: dict[str, float] = {}

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

        self.telemetry_bridge = None
        try:
            self.telemetry_bridge = TelemetryDataBridge()
            self.logger.info("TelemetryDataBridge initialized")
        except Exception as telemetry_exc:
            self.telemetry_bridge = None
            self.logger.warning(
                "TelemetryDataBridge unavailable: %s",
                telemetry_exc,
                exc_info=telemetry_exc,
            )

        # IBL Logger
        from ..ibl_logger import get_ibl_logger, log_ibl_event

        self.ibl_logger = get_ibl_logger()
        log_ibl_event("INFO", "MainWindow", "IBL Logger initialized")

        # Event Logger (Python↔QML)
        from src.common.event_logger import get_event_logger

        self.event_logger = get_event_logger()
        self.logger.info("EventLogger initialized")

        self.feedback_service = FeedbackService()
        try:
            self.feedback_controller = FeedbackController(
                service=self.feedback_service,
                parent=self,
            )
            self.logger.info("FeedbackService initialized")
        except Exception as feedback_exc:
            self.feedback_controller = None
            self.logger.warning(
                "Feedback controller unavailable: %s",
                feedback_exc,
                exc_info=feedback_exc,
            )

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
        self._qml_update_queue: dict[str, dict[str, Any]] = {}
        self._qml_method_support: dict[tuple[str, bool], bool] = {}
        self._qml_flush_timer = QTimer()
        self._qml_flush_timer.setSingleShot(True)
        self._qml_flush_timer.timeout.connect(self._flush_qml_updates)
        self._qml_pending_property_supported: bool | None = None
        self._last_batched_updates: dict[str, Any] | None = None
        self._last_camera_payload: dict[str, Any] = {}

        # State tracking
        from ...runtime import StateSnapshot

        self.current_snapshot: StateSnapshot | None = None
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
        self.feedback_panel = None
        self.graphics_panel = None
        self._graphics_panel = None  # Alias
        self.chart_widget = None
        self.tab_widget = None
        self.main_splitter = None
        self.main_horizontal_splitter = None
        self._qquick_widget: QQuickWidget | None = None
        self._qml_root_object = None
        self._qml_base_dir: Path | None = None

        # Status bar labels (initialized by UISetup)
        self.sim_time_label: QLabel | None = None
        self.step_count_label: QLabel | None = None
        self.fps_label: QLabel | None = None
        self.queue_label: QLabel | None = None
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

    @Slot(str, str)
    def registerShaderWarning(self, effect_id: str, error_log: str) -> None:
        """Receive shader compilation warnings emitted from QML."""

        normalized_id = (effect_id or "").strip() or "unknown"
        message = (error_log or "").strip() or "Shader compilation failed"

        self.logger.warning("⚠️ Shader warning [%s]: %s", normalized_id, message)

        try:
            if getattr(self, "event_logger", None) is None:
                return
            from src.common.event_logger import EventType

            self.event_logger.log_event(  # type: ignore[union-attr]
                event_type=EventType.QML_ERROR,
                component="SimulationRoot",
                action="shader_warning",
                new_value=message,
                metadata={"effectId": normalized_id},
                source="qml",
            )
        except Exception as exc:
            self.logger.debug(
                "EventLogger failed to record shader warning: %s", exc, exc_info=exc
            )

    @Slot(str)
    def clearShaderWarning(self, effect_id: str) -> None:
        """Reset shader warning state once compilation succeeds."""

        normalized_id = (effect_id or "").strip() or "unknown"
        self.logger.info("✅ Shader warning cleared [%s]", normalized_id)

        try:
            if getattr(self, "event_logger", None) is None:
                return
            from src.common.event_logger import EventType

            self.event_logger.log_event(  # type: ignore[union-attr]
                event_type=EventType.FUNCTION_CALLED,
                component="SimulationRoot",
                action="shader_warning_cleared",
                new_value=normalized_id,
                metadata={"effectId": normalized_id},
                source="qml",
            )
        except Exception as exc:
            self.logger.debug(
                "EventLogger failed to record shader warning clear: %s",
                exc,
                exc_info=exc,
            )

    def _persist_shader_status_dump(self, payload: dict[str, Any]) -> None:
        try:
            SHADER_STATUS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with SHADER_STATUS_LOG_PATH.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover - best-effort diagnostics
            self.logger.debug(
                "Failed to persist shader status dump: %s",
                exc,
                exc_info=exc,
            )

    @Slot("QVariantMap")
    def _on_shader_status_dump(self, payload: dict[str, Any]) -> None:
        """Persist shader diagnostics emitted from the QML scene."""

        snapshot = dict(payload) if isinstance(payload, dict) else {}
        snapshot.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        reason = str(
            snapshot.get("effectsBypassReason") or snapshot.get("reason") or "unknown"
        )
        self.logger.warning("⚠️ Shader diagnostics dump recorded (%s)", reason)
        self._persist_shader_status_dump(snapshot)

    # ------------------------------------------------------------------
    # Settings synchronization helpers
    # ------------------------------------------------------------------
    def _apply_settings_update(
        self, category_path: str, updates: dict[str, Any]
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
    def _deep_merge_dicts(target: dict[str, Any], updates: dict[str, Any]) -> None:
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
    def _iter_diff(old: Any, new: Any, prefix: str = "") -> list[tuple[str, Any, Any]]:
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
    def applyQmlConfigChange(self, category: str, payload: dict[str, Any]) -> None:
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

    def _queue_qml_update(self, key: str, params: dict[str, Any]) -> None:
        """Queue QML update → QMLBridge"""
        QMLBridge.queue_update(self, key, params)

    def _sanitize_geometry_payload(
        self, params: dict[str, Any]
    ) -> tuple[dict[str, Any], list[str]]:
        """Clamp geometry payload to maintain internal dependencies."""

        sanitized: dict[str, Any] = dict(params)
        adjustments: list[str] = []

        def _float(value: Any, fallback: float | None = None) -> float | None:
            try:
                if value is None:
                    return fallback
                return float(value)
            except (TypeError, ValueError):
                return fallback

        prev = self._last_geometry_payload

        track_width = _float(
            sanitized.get("trackWidth"), _float(prev.get("trackWidth"))
        )
        frame_to_pivot = _float(
            sanitized.get("frameToPivot"), _float(prev.get("frameToPivot"))
        )
        lever_length = _float(
            sanitized.get("leverLength"), _float(prev.get("leverLength"))
        )
        rod_position = _float(
            sanitized.get("rodPosition"), _float(prev.get("rodPosition"))
        )
        stroke = _float(sanitized.get("strokeM"), _float(prev.get("strokeM")))
        cyl_body = _float(
            sanitized.get("cylinderBodyLength"), _float(prev.get("cylinderBodyLength"))
        )
        rod_length = _float(
            sanitized.get("pistonRodLengthM"), _float(prev.get("pistonRodLengthM"))
        )
        pressure_min = _float(
            sanitized.get("pressureScaleMin"), _float(prev.get("pressureScaleMin"))
        )
        pressure_max = _float(
            sanitized.get("pressureScaleMax"), _float(prev.get("pressureScaleMax"))
        )

        input_track = _float(params.get("trackWidth"))
        input_frame = _float(params.get("frameToPivot"))
        input_lever = _float(params.get("leverLength"))
        input_max_travel = _float(params.get("maxSuspTravel"))

        prev_track = _float(prev.get("trackWidth"))
        prev_frame = _float(prev.get("frameToPivot"))
        prev_lever = _float(prev.get("leverLength"))
        prev_max_travel = _float(prev.get("maxSuspTravel"))

        tolerance = 1e-6

        track_half = None
        if track_width is not None:
            corrected_track = abs(track_width)
            if corrected_track <= tolerance:
                fallback_track = (
                    prev_track
                    if prev_track is not None and prev_track > tolerance
                    else None
                )
                corrected_track = (
                    fallback_track if fallback_track is not None else tolerance
                )
            if (
                input_track is not None
                and abs(corrected_track - input_track) > tolerance
            ):
                adjustments.append(
                    f"WARNING: trackWidth clamped to {corrected_track:.3f} m"
                )
            track_width = corrected_track
            if track_width > tolerance:
                track_half = track_width / 2.0
        elif prev_track is not None and prev_track > tolerance:
            track_width = prev_track
            track_half = track_width / 2.0

        if track_width is not None:
            sanitized["trackWidth"] = track_width

        if track_half is not None:
            if frame_to_pivot is None:
                base_frame = prev_frame if prev_frame is not None else track_half / 2.0
                frame_to_pivot = max(0.0, min(track_half, base_frame))
            if lever_length is None:
                base_lever = prev_lever if prev_lever is not None else track_half / 2.0
                lever_length = max(0.0, min(track_half, base_lever))

            changed_track = input_track is not None and (
                prev_track is None or abs(input_track - prev_track) > tolerance
            )
            changed_frame = input_frame is not None and (
                prev_frame is None or abs(input_frame - prev_frame) > tolerance
            )
            changed_lever = input_lever is not None and (
                prev_lever is None or abs(input_lever - prev_lever) > tolerance
            )

            if changed_track and not changed_frame and not changed_lever:
                base_frame = prev_frame if prev_frame is not None else frame_to_pivot
                base_lever = prev_lever if prev_lever is not None else lever_length
                total = (base_frame or 0.0) + (base_lever or 0.0)
                if total <= tolerance:
                    base_frame = base_lever = track_half / 2.0
                    total = base_frame + base_lever
                frame_ratio = max(0.0, min(1.0, (base_frame or 0.0) / total))
                new_frame = max(0.0, min(track_half * frame_ratio, track_half))
                new_lever = max(0.0, track_half - new_frame)
                if abs(new_frame - frame_to_pivot) > tolerance:
                    adjustments.append(
                        f"WARNING: frameToPivot rescaled to {new_frame:.3f} m for track"
                    )
                if abs(new_lever - lever_length) > tolerance:
                    adjustments.append(
                        f"WARNING: leverLength rescaled to {new_lever:.3f} m for track"
                    )
                frame_to_pivot = new_frame
                lever_length = new_lever
            elif changed_frame:
                original = frame_to_pivot
                frame_to_pivot = max(0.0, min(frame_to_pivot, track_half))
                if abs(original - frame_to_pivot) > tolerance:
                    adjustments.append(
                        f"WARNING: frameToPivot clamped to {frame_to_pivot:.3f} m"
                    )
                previous_lever = lever_length if lever_length is not None else 0.0
                new_lever = max(track_half - frame_to_pivot, 0.0)
                if abs(new_lever - previous_lever) > tolerance:
                    adjustments.append(
                        f"WARNING: leverLength rescaled to {new_lever:.3f} m to match frame"
                    )
                lever_length = new_lever
            elif changed_lever:
                original = lever_length
                lever_length = max(0.0, min(lever_length, track_half))
                if abs(original - lever_length) > tolerance:
                    adjustments.append(
                        f"WARNING: leverLength clamped to {lever_length:.3f} m"
                    )
                updated_frame = max(track_half - lever_length, 0.0)
                if (
                    frame_to_pivot is None
                    or abs(updated_frame - frame_to_pivot) > tolerance
                ):
                    adjustments.append(
                        f"WARNING: frameToPivot rescaled to {updated_frame:.3f} m to match lever"
                    )
                frame_to_pivot = updated_frame
            else:
                if (
                    frame_to_pivot is not None
                    and lever_length is not None
                    and abs(frame_to_pivot + lever_length - track_half) > tolerance
                ):
                    original = lever_length
                    lever_length = max(track_half - frame_to_pivot, 0.0)
                    if abs(lever_length - original) > tolerance:
                        adjustments.append(
                            f"WARNING: leverLength rescaled to {lever_length:.3f} m"
                        )

            if frame_to_pivot is not None:
                clamped_frame = max(0.0, min(frame_to_pivot, track_half))
                if (
                    abs(clamped_frame - frame_to_pivot) > tolerance
                    and not changed_frame
                ):
                    adjustments.append(
                        f"WARNING: frameToPivot clamped to {clamped_frame:.3f} m"
                    )
                frame_to_pivot = clamped_frame
            if lever_length is not None:
                clamped_lever = max(0.0, min(lever_length, track_half))
                if abs(clamped_lever - lever_length) > tolerance and not changed_lever:
                    adjustments.append(
                        f"WARNING: leverLength clamped to {clamped_lever:.3f} m"
                    )
                lever_length = clamped_lever

        if frame_to_pivot is not None:
            sanitized["frameToPivot"] = frame_to_pivot
        if lever_length is not None:
            sanitized["leverLength"] = lever_length

        max_susp_travel = None
        if lever_length is not None:
            max_susp_travel = max(0.0, 2.0 * lever_length)
        else:
            max_susp_travel = _float(sanitized.get("maxSuspTravel"), prev_max_travel)
            if max_susp_travel is not None and max_susp_travel < 0.0:
                corrected_travel = 0.0
                adjustments.append(
                    f"WARNING: maxSuspTravel clamped to {corrected_travel:.3f} m"
                )
                max_susp_travel = corrected_travel

        if (
            input_max_travel is not None
            and max_susp_travel is not None
            and abs(max_susp_travel - input_max_travel) > tolerance
        ):
            adjustments.append(
                f"WARNING: maxSuspTravel clamped to {max_susp_travel:.3f} m"
            )

        if max_susp_travel is not None:
            sanitized["maxSuspTravel"] = max_susp_travel

        if rod_position is not None:
            clamped = min(max(rod_position, 0.1), 0.9)
            if abs(clamped - rod_position) > tolerance:
                adjustments.append(
                    f"WARNING: rodPosition clamped to {clamped:.3f} (0.1..0.9)"
                )
            sanitized["rodPosition"] = clamped

        if max_susp_travel is not None:
            if stroke is None:
                stroke = max_susp_travel
            elif stroke + tolerance < max_susp_travel:
                stroke = max_susp_travel
                adjustments.append(
                    f"WARNING: stroke increased to {stroke:.3f} m to match lever travel"
                )
            sanitized["strokeM"] = stroke

        if cyl_body is not None and rod_length is not None:
            min_rod = 1.1 * cyl_body
            if rod_length + tolerance < min_rod:
                sanitized["pistonRodLengthM"] = min_rod
                adjustments.append(
                    f"WARNING: pistonRodLength raised to {min_rod:.3f} m (>=110% cylinder body)"
                )

        PRESSURE_MIN_LIMIT = -101_325.0
        PRESSURE_MAX_LIMIT = 10_000_000.0
        PRESSURE_MIN_SPAN = 5_000.0

        if pressure_min is not None or pressure_max is not None:
            if pressure_min is None:
                pressure_min = 0.0
            if pressure_max is None:
                pressure_max = max(pressure_min + PRESSURE_MIN_SPAN, 1_000_000.0)

            original_min = pressure_min
            original_max = pressure_max

            pressure_min = max(
                PRESSURE_MIN_LIMIT, min(pressure_min, PRESSURE_MAX_LIMIT)
            )
            pressure_max = max(
                pressure_min + PRESSURE_MIN_SPAN,
                min(pressure_max, PRESSURE_MAX_LIMIT),
            )

            if abs(original_min - pressure_min) > tolerance:
                adjustments.append(
                    f"WARNING: pressureScaleMin clamped to {pressure_min:.1f} Pa"
                )
            if abs(original_max - pressure_max) > tolerance:
                adjustments.append(
                    f"WARNING: pressureScaleMax clamped to {pressure_max:.1f} Pa"
                )

            sanitized["pressureScaleMin"] = pressure_min
            sanitized["pressureScaleMax"] = pressure_max

        tracked_keys = {
            "trackWidth",
            "frameToPivot",
            "leverLength",
            "rodPosition",
            "strokeM",
            "cylinderBodyLength",
            "pistonRodLengthM",
            "maxSuspTravel",
            "pressureScaleMin",
            "pressureScaleMax",
        }
        for key in tracked_keys:
            value = sanitized.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                self._last_geometry_payload[key] = float(value)

        return sanitized, adjustments

    def _geometry_settings_payload(self, payload: dict[str, Any]) -> dict[str, float]:
        """Convert geometry payload keys to settings manager schema."""

        mapping = {
            "frameLength": "wheelbase",
            "trackWidth": "track",
            "frameToPivot": "frame_to_pivot",
            "leverLength": "lever_length",
            "rodPosition": "rod_position",
            "cylinderBodyLength": "cylinder_body_length_m",
            "strokeM": "stroke_m",
            "deadGapM": "dead_gap_m",
            "cylDiamM": "cyl_diam_m",
            "pistonRodLengthM": "piston_rod_length_m",
            "pistonThicknessM": "piston_thickness_m",
            "tailRodLength": "tail_rod_length_m",
            "frameHeight": "frame_height_m",
            "frameBeamSize": "frame_beam_size_m",
            "maxSuspTravel": "max_susp_travel_m",
            "pressureScaleMin": "pressure_scale_min_pa",
            "pressureScaleMax": "pressure_scale_max_pa",
        }

        settings_payload: dict[str, float] = {}
        for source_key, target_key in mapping.items():
            value = payload.get(source_key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                settings_payload[target_key] = float(value)
        return settings_payload

    # ------------------------------------------------------------------
    # Signal Handlers (delegation to SignalsRouter)
    # ------------------------------------------------------------------
    @Slot(str, float)
    def _on_geometry_parameter_logged(self, name: str, value: float) -> None:
        """Debug helper for geometry panel value changes."""

        SignalsRouter.logger.debug("🔧 GeometryPanel: %s=%s", name, value)

    @Slot(str, str)
    def _on_pneumo_mode_logged(self, mode_type: str, new_mode: str) -> None:
        """Debug helper for pneumatic panel mode changes."""

        SignalsRouter.logger.debug("🔧 Mode changed: %s -> %s", mode_type, new_mode)

    @Slot(str, float)
    def _on_pneumo_parameter_logged(self, name: str, value: float) -> None:
        """Debug helper for pneumatic parameter edits."""

        SignalsRouter.logger.debug("🔧 Pneumo param: %s = %s", name, value)

    @Slot(float, str)
    def _on_pneumo_receiver_volume_changed(self, volume: float, mode: str) -> None:
        """Bridge receiver volume edits into the pneumatic pipeline."""

        SignalsRouter.handle_receiver_volume_changed(self, volume, mode)

    @Slot(str, str)
    def _on_modes_mode_logged(self, mode_type: str, new_mode: str) -> None:
        """Debug helper for modes panel mode selection."""

        SignalsRouter.logger.debug("🔧 Mode changed: %s -> %s", mode_type, new_mode)

    @Slot(str, float)
    def _on_modes_parameter_logged(self, name: str, value: float) -> None:
        """Debug helper for modes panel parameter updates."""

        SignalsRouter.logger.debug("🔧 Param: %s = %s", name, value)

    @Slot(dict)
    def _on_geometry_changed_qml(self, params: dict[str, Any]) -> None:
        """Geometry changed → direct QML call"""
        if not isinstance(params, dict):
            return

        sanitized, adjustments = self._sanitize_geometry_payload(params)
        if adjustments:
            for note in adjustments:
                self.logger.warning(note)
        params = sanitized

        self.logger.info(f"Geometry update: {len(params)} keys")

        settings_payload = self._geometry_settings_payload(params)
        if settings_payload:
            try:
                self._apply_settings_update("current.geometry", settings_payload)
            except Exception as exc:
                self.logger.debug(
                    "Failed to persist geometry settings: %s", exc, exc_info=exc
                )

        push_success = QMLBridge.invoke_qml_function(
            self, "applyGeometryUpdates", params
        )
        if adjustments or not push_success:
            QMLBridge.queue_update(self, "geometry", params)

        if hasattr(self, "status_bar") and self.status_bar:
            self.status_bar.showMessage("Геометрия обновлена", 2000)

    @Slot(dict)
    def _on_lighting_changed(self, params: dict[str, Any]) -> None:
        """Lighting changed → SignalsRouter"""
        SignalsRouter.handle_lighting_changed(self, params)

    @Slot(dict)
    def _on_material_changed(self, params: dict[str, Any]) -> None:
        """Material changed → SignalsRouter"""
        SignalsRouter.handle_material_changed(self, params)

    @Slot(dict)
    def _on_environment_changed(self, params: dict[str, Any]) -> None:
        """Environment changed → SignalsRouter"""
        SignalsRouter.handle_environment_changed(self, params)

    @Slot(dict)
    def _on_quality_changed(self, params: dict[str, Any]) -> None:
        """Quality changed → SignalsRouter"""
        SignalsRouter.handle_quality_changed(self, params)

    @Slot(dict)
    def _on_scene_changed(self, params: dict[str, Any]) -> None:
        """Scene changed → SignalsRouter"""
        SignalsRouter.handle_scene_changed(self, params)

    @Slot(dict)
    def _on_camera_changed(self, params: dict[str, Any]) -> None:
        """Camera changed → SignalsRouter"""
        SignalsRouter.handle_camera_changed(self, params)

    @Slot(dict)
    def _on_effects_changed(self, params: dict[str, Any]) -> None:
        """Effects changed → SignalsRouter"""
        SignalsRouter.handle_effects_changed(self, params)

    @Slot(bool)
    def _on_animation_toggled(self, running: bool) -> None:
        """Animation toggled in QML → persist settings"""
        SignalsRouter.handle_animation_toggled(self, bool(running))

    @Slot(dict)
    def _on_preset_applied(self, full_state: dict[str, Any]) -> None:
        """Preset applied → SignalsRouter"""
        SignalsRouter.handle_preset_applied(self, full_state)

    @Slot(dict)
    def _on_animation_changed(self, params: dict[str, Any]) -> None:
        """Animation changed → SignalsRouter"""
        SignalsRouter.handle_animation_changed(self, params)

    @Slot(str)
    def _on_modes_preset_selected(self, preset_id: str) -> None:
        """Modes preset selected → SignalsRouter"""
        SignalsRouter.handle_modes_preset_selected(self, preset_id)

    @Slot(str, str)
    def _on_modes_mode_changed(self, mode_type: str, new_mode: str) -> None:
        """Modes toggle changed → SignalsRouter"""
        SignalsRouter.handle_modes_mode_changed(self, mode_type, new_mode)

    @Slot(dict)
    def _on_modes_physics_changed(self, payload: dict[str, Any]) -> None:
        """Modes physics toggles changed → SignalsRouter"""
        SignalsRouter.handle_modes_physics_changed(self, payload)

    @Slot(dict)
    def _on_pneumatic_settings_changed(self, payload: dict[str, Any]) -> None:
        """Pneumatic settings changed in QML → SignalsRouter"""
        SignalsRouter.handle_pneumatic_settings_changed(self, payload)

    @Slot(dict)
    def _on_simulation_settings_changed(self, payload: dict[str, Any]) -> None:
        """Core simulation settings changed in QML → SignalsRouter"""
        SignalsRouter.handle_simulation_settings_changed(self, payload)

    @Slot(dict)
    def _on_cylinder_settings_changed(self, payload: dict[str, Any]) -> None:
        """Cylinder constants changed in QML → SignalsRouter"""
        SignalsRouter.handle_cylinder_settings_changed(self, payload)

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
    def _on_qml_batch_ack(self, summary: dict[str, Any]) -> None:
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
