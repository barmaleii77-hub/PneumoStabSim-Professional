"""
Main window for PneumoStabSim application
Qt Quick3D rendering with QQuickWidget (no createWindowContainer)
РУССКИЙ ИНТЕРФЕЙС (Russian UI)
"""

from PySide6.QtWidgets import (
    QMainWindow,
    QStatusBar,
    QWidget,
    QLabel,
    QSplitter,
    QTabWidget,
    QScrollArea,
)
from PySide6.QtCore import (
    Qt,
    QTimer,
    Slot,
    QUrl,
    QByteArray,
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtQuickWidgets import QQuickWidget
import logging
import os
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any

from src.ui.charts import ChartWidget
from src.ui.panels import (
    GeometryPanel,
    PneumoPanel,
    ModesPanel,
    RoadPanel,
    GraphicsPanel,
)
from ..runtime import SimulationManager, StateSnapshot
from .ibl_logger import get_ibl_logger, log_ibl_event  # ✅ IBL логгер
from .environment_schema import (
    ENVIRONMENT_CONTEXT_PROPERTIES,
    EnvironmentValidationError,
    validate_environment_settings,
)
from src.common.event_logger import get_event_logger  # ✅ EventLogger
from src.common.settings_manager import (
    get_settings_event_bus,
    get_settings_manager,
)
from src.common.signal_trace import get_signal_trace_service
from src.ui.scene_bridge import SceneBridge
from src.ui.main_window.qml_bridge import QMLBridge
from src.ui.qml_bridge import register_qml_signals


class MainWindow(QMainWindow):
    """Главное окно приложения с Qt Quick3D (RHI/Direct3D) + SettingsManager"""

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

    WHEEL_KEY_MAP = {
        "LP": "fl",
        "PP": "fr",
        "LZ": "rl",
        "PZ": "rr",
    }

    def __init__(self, use_qml_3d: bool = True) -> None:
        super().__init__()

        # SettingsManager
        self.settings_manager = get_settings_manager()
        self.settings_event_bus = get_settings_event_bus()
        self.signal_trace_service = get_signal_trace_service()

        # Scene bridge exposed to QML
        self.scene_bridge = SceneBridge(self)
        self._registered_qml_signals = []

        # Store visualization backend choice
        self.use_qml_3d = use_qml_3d
        backend_name = "Qt Quick3D (main.qml v4.3)" if use_qml_3d else "Legacy OpenGL"
        self.setWindowTitle(f"PneumoStabSim - {backend_name}")

        self.resize(1400, 900)
        self.setMinimumSize(1200, 800)
        self.setWindowState(Qt.WindowState.WindowNoState)

        # Logging
        self.logger = logging.getLogger(self.__class__.__name__)
        # IBL logger
        self.ibl_logger = get_ibl_logger()
        log_ibl_event("INFO", "MainWindow", "IBL Logger initialized")
        # Event logger
        self.event_logger = get_event_logger()

        # Diagnostics services exposed to QML
        self._settings_event_bus = get_settings_event_bus()
        self._signal_trace = get_signal_trace_service()

        # State tracking
        self.current_snapshot: Optional[StateSnapshot] = None
        self.is_simulation_running = False
        self._sim_started = False

        # Geometry bridge
        from src.ui.geometry_bridge import create_geometry_converter

        self.geometry_converter = create_geometry_converter(self.settings_manager)
        self.logger.info("✅ GeometryBridge создан для интеграции Python↔QML")

        # Panels references
        self.geometry_panel: Optional[GeometryPanel] = None
        self.pneumo_panel: Optional[PneumoPanel] = None
        self.modes_panel: Optional[ModesPanel] = None
        self.road_panel: Optional[RoadPanel] = None
        self.graphics_panel: Optional[GraphicsPanel] = None
        self.chart_widget: Optional[ChartWidget] = None

        # Tab widget and splitters
        self.tab_widget: Optional[QTabWidget] = None
        self.main_splitter: Optional[QSplitter] = None
        self.main_horizontal_splitter: Optional[QSplitter] = None

        # Qt Quick3D view reference
        self._qquick_widget: Optional[QQuickWidget] = None
        self._qml_root_object = None
        self._qml_base_dir: Optional[Path] = None

        # Simulation manager
        try:
            self.simulation_manager = SimulationManager(self)
            self.logger.info("✅ SimulationManager создан (не запущен)")
        except Exception as e:
            self.logger.exception(f"❌ Ошибка создания SimulationManager: {e}")
            raise

        # QML update system
        self._qml_update_queue: Dict[str, Dict[str, Any]] = {}
        self._qml_method_support: Dict[tuple[str, bool], bool] = {}
        self._qml_flush_timer = QTimer()
        self._qml_flush_timer.setSingleShot(True)
        self._qml_flush_timer.timeout.connect(self._flush_qml_updates)
        self._qml_pending_property_supported: Optional[bool] = None
        self._qml_batch_ack_supported: Optional[bool] = None
        self._last_batched_updates: Optional[Dict[str, Any]] = None

        # UI
        self._setup_central()
        self._setup_tabs()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        self._connect_simulation_signals()

        # Render timer (UI thread ~60 FPS)
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self._update_render)
        self.render_timer.start(16)

        # Restore UI from JSON (НЕ QSettings)
        self._restore_ui_from_json()

        # Initial full sync to QML
        self._initial_full_sync()
        self.logger.info("✅ MainWindow initialized")

    # ---------- UI layout ----------
    def _setup_central(self) -> None:
        self.main_horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_horizontal_splitter.setObjectName("MainHorizontalSplitter")
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setObjectName("SceneChartsSplitter")

        # Always use QML3D for now
        self._setup_qml_3d_view()

        if self._qquick_widget:
            self.main_splitter.addWidget(self._qquick_widget)

        self.chart_widget = ChartWidget(self)
        self.chart_widget.setMinimumHeight(200)
        self.main_splitter.addWidget(self.chart_widget)

        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 2)
        self.main_horizontal_splitter.addWidget(self.main_splitter)
        self.setCentralWidget(self.main_horizontal_splitter)

    def _select_qml_entrypoint(self) -> Path:
        """Determine which QML file should be loaded for the 3D scene."""
        candidates: list[Path] = []

        override = os.environ.get("PSS_QML_SCENE")
        if override:
            candidate = Path(override)
            if not candidate.is_absolute():
                candidate = Path("assets/qml") / candidate
            candidates.append(candidate)

        candidates.extend(
            [
                Path("assets/qml/main_optimized.qml"),
                Path("assets/qml/main.qml"),
                Path("assets/qml/SimulationFallbackRoot.qml"),
            ]
        )

        seen: set[str] = set()
        for candidate in candidates:
            key = str(candidate.resolve() if candidate.exists() else candidate)
            if key in seen:
                continue
            seen.add(key)
            if candidate.exists():
                return candidate

        raise FileNotFoundError("Не удалось найти подходящий QML-файл для загрузки")

    def _build_initial_qml_payload(self) -> Dict[str, Dict[str, Any]]:
        """Collect initial settings payloads for the QML context."""

        payload: Dict[str, Dict[str, Any]] = {
            "animation": {},
            "scene": {},
            "materials": {},
            "diagnostics": {},
        }

        manager = getattr(self, "settings_manager", None)
        if manager is None:
            return payload

        def _sanitise(data: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return json.loads(json.dumps(data))
            except Exception:
                return data

        try:
            animation = manager.get("graphics.animation", {}) or {}
            scene = manager.get("graphics.scene", {}) or {}
            materials = manager.get("graphics.materials", {}) or {}
            diagnostics = manager.get("diagnostics", {}) or {}

            if isinstance(animation, dict):
                payload["animation"] = _sanitise(animation)
            if isinstance(scene, dict):
                payload["scene"] = _sanitise(scene)
            if isinstance(materials, dict):
                payload["materials"] = _sanitise(materials)
            if isinstance(diagnostics, dict):
                payload["diagnostics"] = _sanitise(diagnostics)
        except Exception as exc:  # pragma: no cover - defensive fallback
            self.logger.debug(
                "Failed to build initial QML payload: %s", exc, exc_info=True
            )

        return payload

    def _setup_qml_3d_view(self) -> None:
        """Setup Qt Quick 3D scene backed by the modular SimulationRoot."""
        qml_file: Optional[Path] = None
        try:
            qml_file = self._select_qml_entrypoint()
            self.logger.info("[QML] Загрузка QML: %s", qml_file)
            self._qquick_widget = QQuickWidget(self)
            self._qquick_widget.setResizeMode(
                QQuickWidget.ResizeMode.SizeRootObjectToView
            )

            engine = self._qquick_widget.engine()
            context = engine.rootContext()
            context.setContextProperty("window", self)
            context.setContextProperty("pythonSceneBridge", self.scene_bridge)
            context.setContextProperty("settingsEvents", self.settings_event_bus)
            context.setContextProperty("signalTrace", self.signal_trace_service)
            log_ibl_event(
                "INFO",
                "MainWindow",
                "IBL Logger registered in QML context (BEFORE QML load)",
            )

            def _ctx(name: str, value: Any) -> None:
                try:
                    context.setContextProperty(name, value)
                except Exception as err:  # pragma: no cover - Qt binding failure
                    raise RuntimeError(
                        f"Failed to expose context property {name}: {err}"
                    ) from err

            try:
                env_raw = self.settings_manager.get("graphics.environment", {}) or {}

                def _prepare(payload: Any) -> Any:
                    return QMLBridge._prepare_for_qml(payload)

                env_values = validate_environment_settings(env_raw)
                for key, ctx_name in ENVIRONMENT_CONTEXT_PROPERTIES.items():
                    _ctx(ctx_name, env_values[key])

            except EnvironmentValidationError as ex:
                self.logger.error(
                    "Некорректные параметры окружения в config/app_settings.json: %s",
                    ex,
                )
                raise
            except Exception as ex:
                self.logger.error(
                    f"Не удалось применить стартовые параметры окружения: {ex}"
                )
                raise

            try:
                graphics_state = self.settings_manager.get("graphics", {}) or {}

                def _ctx_dict(name: str, payload: Any, *extra_names: str) -> None:
                    """Пробрасывает словарь в контекст, с безопасной нормализацией JSON"""
                    if not isinstance(payload, dict) or not payload:
                        return
                    normalized = _prepare(payload)
                    targets = (name,) + tuple(extra_names)
                    for target in targets:
                        _ctx(target, normalized)

                _ctx_dict(
                    "startLightingState",
                    graphics_state.get("lighting"),
                )
                _ctx_dict(
                    "startQualityState",
                    graphics_state.get("quality"),
                )
                _ctx_dict(
                    "startCameraState",
                    graphics_state.get("camera"),
                )
                _ctx_dict(
                    "startMaterialsState",
                    graphics_state.get("materials"),
                )
                _ctx_dict(
                    "startEffectsState",
                    graphics_state.get("effects"),
                )
                _ctx_dict(
                    "initialSceneSettings",
                    graphics_state.get("scene"),
                )
                _ctx_dict(
                    "initialAnimationSettings",
                    graphics_state.get("animation"),
                )
            except Exception as ex:
                self.logger.warning(
                    f"Не удалось подготовить стартовые состояния графики: {ex}"
                )

            try:
                diagnostics_state = self.settings_manager.get("diagnostics", {}) or {}
                if isinstance(diagnostics_state, dict) and diagnostics_state:
                    context.setContextProperty(
                        "initialDiagnosticsSettings",
                        QMLBridge._prepare_for_qml(diagnostics_state),
                    )
            except Exception as ex:
                self.logger.warning(
                    f"Не удалось пробросить стартовые диагностические настройки: {ex}"
                )

            # Путь импорта Qt
            from PySide6.QtCore import QLibraryInfo

            qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
            engine.addImportPath(str(qml_path))

            local_qml_path = Path("assets/qml")
            if local_qml_path.exists():
                engine.addImportPath(str(local_qml_path.absolute()))

            self._qml_base_dir = qml_file.parent.resolve()
            self._qquick_widget.setSource(QUrl.fromLocalFile(str(qml_file.absolute())))

            status = self._qquick_widget.status()
            if status == QQuickWidget.Status.Error:
                errors = self._qquick_widget.errors()
                msgs = "\n".join(str(e) for e in errors)
                raise RuntimeError(f"Ошибки загрузки QML:\n{msgs}")

            self._qml_root_object = self._qquick_widget.rootObject()
            if not self._qml_root_object:
                raise RuntimeError("Не удалось получить корневой объект QML")

            self._register_qml_signals()

        except Exception as e:
            target = qml_file if qml_file is not None else Path("assets/qml/main.qml")
            self.logger.exception(f"[CRITICAL] Ошибка загрузки {target}: {e}")
            fallback = QLabel(
                "КРИТИЧЕСКАЯ ОШИБКА ЗАГРУЗКИ3D СЦЕНЫ\n\n"
                f"Ошибка: {e}\n\n"
                f"Проверьте файл {target}\n"
                "и убедитесь, что QtQuick3D установлен правильно"
            )
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setStyleSheet(
                "background: #1a1a2e; color: #ff6b6b; font-size:12px; padding:20px;"
            )
            self._qquick_widget = fallback

    def _register_qml_signals(self) -> None:
        if not self._qml_root_object:
            return
        try:
            specs = register_qml_signals(self, self._qml_root_object)
            self._registered_qml_signals = specs
            if specs:
                names = ", ".join(spec.name for spec in specs)
                self.logger.info("✅ QML signals connected: %s", names)
        except Exception as exc:
            self.logger.error(f"Не удалось подключить QML сигналы: {exc}")

    def _setup_tabs(self) -> None:
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setObjectName("ParameterTabs")
        self.tab_widget.setMinimumWidth(300)
        self.tab_widget.setMaximumWidth(800)

        # Geometry
        self.geometry_panel = GeometryPanel(self)
        sg = QScrollArea()
        sg.setWidgetResizable(True)
        sg.setWidget(self.geometry_panel)
        sg.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tab_widget.addTab(sg, "Геометрия")

        # Pneumatics
        self.pneumo_panel = PneumoPanel(self)
        sp = QScrollArea()
        sp.setWidgetResizable(True)
        sp.setWidget(self.pneumo_panel)
        sp.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tab_widget.addTab(sp, "Пневмосистема")

        # Modes
        self.modes_panel = ModesPanel(self)
        sm = QScrollArea()
        sm.setWidgetResizable(True)
        sm.setWidget(self.modes_panel)
        sm.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tab_widget.addTab(sm, "Режимы стабилизатора")

        # Road profile
        try:
            self.road_panel = RoadPanel(self)
            sr = QScrollArea()
            sr.setWidgetResizable(True)
            sr.setWidget(self.road_panel)
            sr.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.tab_widget.addTab(sr, "Дорожный профиль")
        except Exception as ex:
            # Панель может быть недоступна в некоторых конфигурациях; продолжаем без неё
            self.logger.warning(f"RoadPanel недоступна: {ex}")
            self.road_panel = None

        # Graphics
        self.graphics_panel = GraphicsPanel(self)
        self.tab_widget.addTab(self.graphics_panel, "🎨 Графика")

        # Dynamics (stub)
        dynamics_stub = QWidget()
        self.tab_widget.addTab(dynamics_stub, "Динамика движения")

        self.main_horizontal_splitter.addWidget(self.tab_widget)
        self.main_horizontal_splitter.setStretchFactor(0, 3)
        self.main_horizontal_splitter.setStretchFactor(1, 1)

        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        self._wire_panel_signals()

    def _setup_menus(self) -> None:
        menubar = self.menuBar()
        menubar.clear()
        file_menu = menubar.addMenu("Файл")
        exit_action = QAction("Выход", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _setup_toolbar(self) -> None:
        toolbar = self.addToolBar("Основная")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(True)
        for title, command in [
            ("▶ Старт", "start"),
            ("⏸ Пауза", "pause"),
            ("⏹ Стоп", "stop"),
            ("↺ Сброс", "reset"),
        ]:
            act = QAction(title, self)
            act.triggered.connect(
                lambda _=False, cmd=command: self._on_sim_control(cmd)
            )
            toolbar.addAction(act)

    def _setup_status_bar(self) -> None:
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        self.sim_time_label = QLabel("Sim Time:0.000s")
        self.step_count_label = QLabel("Steps:0")
        self.fps_label = QLabel("Physics FPS:0.0")
        self.queue_label = QLabel("Queue:0/0")
        for w in (
            self.sim_time_label,
            self.step_count_label,
            self.fps_label,
            self.queue_label,
        ):
            w.setStyleSheet("padding:6px")
            status_bar.addPermanentWidget(w)
        self.status_bar = status_bar

    # ---------- SettingsManager-based UI restore/save ----------
    def _restore_ui_from_json(self) -> None:
        try:
            ui_state: Dict[str, Any] = (
                self.settings_manager.get("ui.main_window", {}) or {}
            )
            geom_b64 = ui_state.get("geometry")
            if geom_b64:
                self.restoreGeometry(QByteArray.fromBase64(geom_b64.encode("utf-8")))
            win_state_b64 = ui_state.get("window_state")
            if win_state_b64:
                self.restoreState(QByteArray.fromBase64(win_state_b64.encode("utf-8")))
            split_b64 = ui_state.get("splitter")
            if split_b64 and self.main_splitter:
                self.main_splitter.restoreState(
                    QByteArray.fromBase64(split_b64.encode("utf-8"))
                )
            hsplit_b64 = ui_state.get("horizontal_splitter")
            if hsplit_b64 and self.main_horizontal_splitter:
                self.main_horizontal_splitter.restoreState(
                    QByteArray.fromBase64(hsplit_b64.encode("utf-8"))
                )
            last_tab = ui_state.get("last_tab")
            if (
                isinstance(last_tab, int)
                and self.tab_widget
                and 0 <= last_tab < self.tab_widget.count()
            ):
                self.tab_widget.setCurrentIndex(last_tab)
            self.logger.info("✅ UI restored from app_settings.json")
        except Exception as e:
            self.logger.warning(f"⚠️ UI restore failed: {e}")

    def _save_ui_to_json(self) -> None:
        try:
            ui_state: Dict[str, Any] = {
                "geometry": self.saveGeometry().toBase64().data().decode("utf-8"),
                "window_state": self.saveState().toBase64().data().decode("utf-8"),
            }
            if self.main_splitter:
                ui_state["splitter"] = (
                    self.main_splitter.saveState().toBase64().data().decode("utf-8")
                )
            if self.main_horizontal_splitter:
                ui_state["horizontal_splitter"] = (
                    self.main_horizontal_splitter.saveState()
                    .toBase64()
                    .data()
                    .decode("utf-8")
                )
            if self.tab_widget:
                ui_state["last_tab"] = int(self.tab_widget.currentIndex())
            self.settings_manager.set("ui.main_window", ui_state, auto_save=False)
        except Exception as e:
            self.logger.warning(f"⚠️ UI save failed: {e}")

    @Slot(int)
    def _on_tab_changed(self, index: int) -> None:
        ui_state = self.settings_manager.get("ui.main_window", {}) or {}
        ui_state["last_tab"] = int(index)
        self.settings_manager.set("ui.main_window", ui_state, auto_save=False)

    # ---------- Signal wiring ----------
    def _connect_simulation_signals(self) -> None:
        try:
            bus = self.simulation_manager.state_bus
            bus.state_updated.connect(self._on_state_update)
            bus.physics_error.connect(self._on_physics_error)
        except Exception:
            pass

    def _wire_panel_signals(self) -> None:
        if self.geometry_panel:
            self.geometry_panel.parameter_changed.connect(
                lambda n, v: self.logger.debug(f"🔧 GeometryPanel: {n}={v}")
            )
            self.geometry_panel.geometry_changed.connect(self._on_geometry_changed_qml)

        if self.pneumo_panel:
            self.pneumo_panel.mode_changed.connect(
                lambda t, m: self.logger.debug(f"🔧 Pneumo mode: {t} -> {m}")
            )
            self.pneumo_panel.parameter_changed.connect(
                lambda n, v: self.logger.debug(f"🔧 Pneumo param: {n} = {v}")
            )

        if self.modes_panel:
            self.modes_panel.simulation_control.connect(self._on_sim_control)
            self.modes_panel.mode_changed.connect(
                lambda t, m: self.logger.debug(f"🔧 Mode changed: {t} -> {m}")
            )
            self.modes_panel.parameter_changed.connect(
                lambda n, v: self.logger.debug(f"🔧 Param: {n} = {v}")
            )
            self.modes_panel.animation_changed.connect(self._on_animation_changed)

        if self.graphics_panel:
            self.graphics_panel.lighting_changed.connect(self._on_lighting_changed)
            self.graphics_panel.material_changed.connect(self._on_material_changed)
            self.graphics_panel.environment_changed.connect(
                self._on_environment_changed
            )
            self.graphics_panel.quality_changed.connect(self._on_quality_changed)
            self.graphics_panel.camera_changed.connect(self._on_camera_changed)
            self.graphics_panel.effects_changed.connect(self._on_effects_changed)
            self.graphics_panel.preset_applied.connect(self._on_preset_applied)

    # ---------- QML update batching ----------
    def _queue_qml_update(self, category: str, payload: Dict[str, Any]) -> None:
        """Добавить обновление в очередь QML"""
        if not isinstance(payload, dict):
            return
        QMLBridge.queue_update(self, category, payload)

    @Slot(dict)
    def _on_geometry_changed_qml(self, geometry_params: Dict[str, Any]) -> None:
        if not isinstance(geometry_params, dict):
            return
        if self._qml_root_object and self._invoke_qml_function(
            "applyGeometryUpdates", geometry_params
        ):
            if hasattr(self, "status_bar"):
                self.status_bar.showMessage("Геометрия обновлена", 2000)
        else:
            self._queue_qml_update("geometry", geometry_params)
        if self.status_bar:
            self.status_bar.showMessage("Геометрия отправлена в3D сцену", 2000)

    def _flush_qml_updates(self) -> None:
        QMLBridge.flush_updates(self)

    def _push_batched_updates(self, updates: Dict[str, Any]) -> bool:
        if not updates:
            return False

        dispatched = False
        if self.scene_bridge:
            try:
                sanitized = QMLBridge._prepare_for_qml(updates)
                dispatched = self.scene_bridge.dispatch_updates(sanitized)
            except Exception:
                self.logger.debug("SceneBridge dispatch failed", exc_info=True)

        if dispatched:
            self._last_batched_updates = updates
            return True

        success = bool(QMLBridge._push_batched_updates(self, updates))
        if success:
            self._last_batched_updates = updates
        return success

    def _invoke_qml_function(
        self, method_name: str, payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        if not self._qml_root_object:
            return False
        try:
            from PySide6.QtCore import QMetaObject, Q_ARG, Qt as _Qt

            if payload is None:
                return QMetaObject.invokeMethod(
                    self._qml_root_object,
                    method_name,
                    _Qt.ConnectionType.DirectConnection,
                )
            else:
                result = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    method_name,
                    _Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", payload),
                )
                if result and isinstance(payload, dict):
                    try:
                        category = next(
                            (
                                cat
                                for cat, methods in self.QML_UPDATE_METHODS.items()
                                if method_name in methods
                            ),
                            None,
                        )
                        if category and self.scene_bridge:
                            self.scene_bridge.dispatch_updates({category: payload})
                    except Exception:
                        self.logger.debug(
                            "SceneBridge failed to mirror %s",
                            method_name,
                            exc_info=True,
                        )
                return result
        except Exception:
            return False

    @Slot(dict)
    def _on_qml_batch_ack(self, summary: Dict[str, Any]) -> None:
        self._qml_batch_ack_supported = True
        try:
            QMLBridge.handle_qml_ack(self, summary)
        except Exception:
            self.logger.debug("QML batch ACK handling failed", exc_info=True)

    @Slot(str)
    def logIblEvent(self, message: str) -> None:
        entry = str(message)
        try:
            if hasattr(self.ibl_logger, "logIblEvent"):
                self.ibl_logger.logIblEvent(entry)
            else:
                log_ibl_event("INFO", "IblProbeLoader", entry)
            self.logger.info("IBL: %s", entry)
        except Exception:
            self.logger.debug("Failed to persist IBL event", exc_info=True)

    @Slot(str, result=str)
    def normalizeHdrPath(self, raw_path: str) -> str:
        """Normalize HDR paths requested from QML helpers."""
        try:
            text = str(raw_path)
        except Exception:
            return ""

        candidate = text.strip()
        if not candidate:
            return ""

        path_obj = Path(candidate)
        if not path_obj.is_absolute():
            search_roots = []
            if self._qml_base_dir:
                search_roots.append(self._qml_base_dir)
            search_roots.append(Path.cwd())

            for root_path in search_roots:
                resolved = (root_path / path_obj).resolve()
                if resolved.exists():
                    path_obj = resolved
                    break
            else:
                # Fall back to resolving relative to the first available root.
                base = search_roots[0] if search_roots else Path.cwd()
                path_obj = (base / path_obj).resolve()

        try:
            return str(path_obj).replace("\\", "/")
        except Exception:
            return ""

    # ---------- Panel signals → QML ----------
    @Slot(dict)
    def _on_lighting_changed(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return
        if not self._invoke_qml_function("applyLightingUpdates", params):
            self._queue_qml_update("lighting", params)

    @Slot(dict)
    def _on_material_changed(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return
        if not self._invoke_qml_function("applyMaterialUpdates", params):
            self._queue_qml_update("materials", params)

    @Slot(dict)
    def _on_environment_changed(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return
        if not self._invoke_qml_function("applyEnvironmentUpdates", params):
            self._queue_qml_update("environment", params)

    @Slot(dict)
    def _on_quality_changed(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return
        if not self._invoke_qml_function("applyQualityUpdates", params):
            self._queue_qml_update("quality", params)

    @Slot(dict)
    def _on_camera_changed(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return
        if not self._invoke_qml_function("applyCameraUpdates", params):
            self._queue_qml_update("camera", params)

    @Slot(dict)
    def _on_effects_changed(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return
        if not self._invoke_qml_function("applyEffectsUpdates", params):
            self._queue_qml_update("effects", params)

    @Slot(dict)
    def _on_preset_applied(self, full_state: Dict[str, Any]) -> None:
        if not isinstance(full_state, dict):
            return
        for cat in (
            "environment",
            "lighting",
            "materials",
            "quality",
            "camera",
            "effects",
        ):
            self._queue_qml_update(cat, full_state.get(cat, {}))

    @Slot(dict)
    def _on_animation_changed(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return
        if not self._invoke_qml_function("applyAnimationUpdates", params):
            self._queue_qml_update("animation", params)

    # ---------- Simulation ----------
    @Slot(str)
    def _on_sim_control(self, command: str) -> None:
        """Управление симуляцией из панели режимов и тулбара. Синхронизирует состояние анимации в QML."""
        try:
            bus = self.simulation_manager.state_bus
            cmd = str(command).lower().strip()
            if cmd == "start":
                bus.start_simulation.emit()
                self.is_simulation_running = True
                if self._qml_root_object:
                    self._qml_root_object.setProperty("isRunning", True)
                if hasattr(self, "status_bar") and self.status_bar:
                    self.status_bar.showMessage("Симуляция: старт", 2000)
            elif cmd == "pause":
                bus.pause_simulation.emit()
                self.is_simulation_running = False
                if self._qml_root_object:
                    self._qml_root_object.setProperty("isRunning", False)
                if hasattr(self, "status_bar") and self.status_bar:
                    self.status_bar.showMessage("Симуляция: пауза", 2000)
            elif cmd == "stop":
                bus.stop_simulation.emit()
                self.is_simulation_running = False
                if self._qml_root_object:
                    self._qml_root_object.setProperty("isRunning", False)
                if hasattr(self, "status_bar") and self.status_bar:
                    self.status_bar.showMessage("Симуляция: стоп", 2000)
            elif cmd == "reset":
                bus.reset_simulation.emit()
                if self._qml_root_object:
                    self._qml_root_object.setProperty("animationTime", 0.0)
                if hasattr(self, "status_bar") and self.status_bar:
                    self.status_bar.showMessage("Симуляция: сброс", 2000)
            else:
                self.logger.warning(f"Неизвестная команда симуляции: {command}")
        except Exception as e:
            self.logger.error(f"Ошибка управления симуляцией '{command}': {e}")

    @Slot(object)
    def _on_state_update(self, snapshot: StateSnapshot) -> None:
        self.current_snapshot = snapshot
        try:
            if snapshot:
                self.sim_time_label.setText(
                    f"Sim Time: {snapshot.simulation_time:.3f}s"
                )
                self.step_count_label.setText(f"Steps: {snapshot.step_number}")
                if snapshot.aggregates.physics_step_time > 0:
                    fps = 1.0 / snapshot.aggregates.physics_step_time
                    self.fps_label.setText(f"Physics FPS: {fps:.1f}")
            if self.chart_widget:
                self.chart_widget.update_from_snapshot(snapshot)
        except Exception:
            pass
        try:
            if hasattr(self.simulation_manager, "get_queue_stats"):
                stats = self.simulation_manager.get_queue_stats()
                get_c = stats.get("get_count", 0)
                put_c = stats.get("put_count", 0)
                if hasattr(self, "queue_label") and self.queue_label:
                    self.queue_label.setText(f"Queue: {get_c}/{put_c}")
        except Exception:
            if hasattr(self, "queue_label") and self.queue_label:
                self.queue_label.setText("Queue: -/-")

    @Slot(str)
    def _on_physics_error(self, message: str) -> None:
        self.logger.error(f"Physics engine error: {message}")
        if hasattr(self, "status_bar") and self.status_bar:
            self.status_bar.showMessage(f"Physics error: {message}", 5000)

    def _update_render(self) -> None:
        if not self._qml_root_object:
            return
        now = time.perf_counter()
        last_tick = getattr(self, "_last_animation_tick", None)
        self._last_animation_tick = now
        try:
            if (
                bool(self._qml_root_object.property("isRunning"))
                and last_tick is not None
            ):
                elapsed = now - last_tick
                current = float(self._qml_root_object.property("animationTime") or 0.0)
                self._qml_root_object.setProperty(
                    "animationTime", current + float(elapsed)
                )
        except Exception:
            pass
        try:
            if hasattr(self.simulation_manager, "get_queue_stats"):
                stats = self.simulation_manager.get_queue_stats()
                get_c = stats.get("get_count", 0)
                put_c = stats.get("put_count", 0)
                if hasattr(self, "queue_label") and self.queue_label:
                    self.queue_label.setText(f"Queue: {get_c}/{put_c}")
        except Exception:
            if hasattr(self, "queue_label") and self.queue_label:
                self.queue_label.setText("Queue: -/-")

    # ---------- Initial sync ----------
    def _initial_full_sync(self) -> None:
        try:
            if not self.graphics_panel:
                return
            pending: Dict[str, Any] = (
                self.graphics_panel.collect_state()
                if hasattr(self.graphics_panel, "collect_state")
                else {}
            )
            if pending:
                if not self._push_batched_updates(pending):
                    for cat, payload in pending.items():
                        self._invoke_qml_function(
                            f"apply{cat.capitalize()}Updates", payload
                        )
        except Exception as e:
            self.logger.error(f"Initial full sync failed: {e}")

    # ---------- Centralized save on exit ----------
    def closeEvent(self, event) -> None:  # type: ignore[override]
        try:
            # 1) Собираем состояние панелей → SettingsManager (без немедленной записи)
            if self.graphics_panel and hasattr(self.graphics_panel, "collect_state"):
                g = self.graphics_panel.collect_state()
                self.settings_manager.set_category("graphics", g, auto_save=False)
            if self.geometry_panel and hasattr(self.geometry_panel, "collect_state"):
                geo = self.geometry_panel.collect_state()
                self.settings_manager.set_category("geometry", geo, auto_save=False)
            if self.pneumo_panel and hasattr(self.pneumo_panel, "collect_state"):
                pneu = self.pneumo_panel.collect_state()
                self.settings_manager.set_category("pneumatic", pneu, auto_save=False)
            if self.modes_panel and hasattr(self.modes_panel, "collect_state"):
                modes = self.modes_panel.collect_state()
                self.settings_manager.set_category("modes", modes, auto_save=False)

            # 2) Сохраняем UI состояние
            self._save_ui_to_json()

            # 3) Пишем на диск ОДИН РАЗ
            self.settings_manager.save()
            self.logger.info(
                "✅ All settings saved to config/app_settings.json on exit"
            )

            try:
                self.simulation_manager.stop()
            except Exception:
                pass
        except Exception as e:
            self.logger.error(f"Failed to save settings on exit: {e}")
        finally:
            super().closeEvent(event)
