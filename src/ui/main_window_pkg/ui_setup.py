"""UI Setup Module - MainWindow UI construction

Модуль построения UI элементов главного окна.
Отвечает за создание всех виджетов, сплиттеров, панелей и их расположение.

Russian UI / English code.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

from PySide6.QtCore import Qt, QSettings, QUrl
from PySide6.QtWidgets import (
    QLabel,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtGui import QAction, QKeySequence

if TYPE_CHECKING:
    from .main_window_refactored import MainWindow


class UISetup:
    """Построение UI элементов главного окна

    Static methods для делегирования из MainWindow.
    Каждый метод принимает `window: MainWindow` как первый аргумент.
    """

    logger = logging.getLogger(__name__)

    _SUPPORTED_SCENES: dict[str, Path] = {
        "main": Path("assets/qml/main.qml"),
        "realism": Path("assets/qml/main_v2_realism.qml"),
        "fallback": Path("assets/qml/main_fallback.qml"),
    }
    _SCENE_LOAD_ORDER: tuple[str, ...] = ("main", "realism", "fallback")
    _SCENE_ENV_VAR = "PSS_QML_SCENE"

    @staticmethod
    def build_qml_context_payload(
        settings_manager: Any | None,
    ) -> Dict[str, Dict[str, Any]]:
        """Подготовить стартовые словари для QML контекста."""

        from src.common.settings_manager import (
            SettingsManager,
            get_settings_manager,
        )

        manager = settings_manager
        if manager is None:
            try:
                manager = get_settings_manager()
            except Exception:
                manager = None

        def _section(name: str) -> Dict[str, Any]:
            if manager is None:
                return SettingsManager.get_graphics_default(name)
            try:
                data = manager.get(f"graphics.{name}", {}) or {}
            except Exception:
                data = {}
            if not isinstance(data, dict) or not data:
                data = SettingsManager.get_graphics_default(name)
            return data

        def _sanitize(payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return json.loads(json.dumps(payload))
            except Exception:
                return payload

        def _diagnostics() -> Dict[str, Any]:
            if manager is None:
                return {}
            try:
                payload = manager.get("diagnostics", {}) or {}
            except Exception:
                payload = {}
            if not isinstance(payload, dict):
                return {}
            return payload

        return {
            "animation": _sanitize(_section("animation")),
            "scene": _sanitize(_section("scene")),
            "materials": _sanitize(_section("materials")),
            "diagnostics": _sanitize(_diagnostics()),
        }

    # ------------------------------------------------------------------
    # Central Widget Setup
    # ------------------------------------------------------------------
    @staticmethod
    def setup_central(window: MainWindow) -> None:
        """Создать центральный вид с горизонтальным и вертикальным сплиттерами

        Layout: [3D Scene (top) + Charts (bottom)] | [Control Panels (right)]

        Args:
            window: MainWindow instance
        """
        UISetup.logger.debug("setup_central: Создание системы сплиттеров...")

        # Create main horizontal splitter (left: scene+charts, right: panels)
        window.main_horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        window.main_horizontal_splitter.setObjectName("MainHorizontalSplitter")

        # Create vertical splitter for left side (scene + charts)
        window.main_splitter = QSplitter(Qt.Orientation.Vertical)
        window.main_splitter.setObjectName("SceneChartsSplitter")

        # Top section: 3D scene
        if window.use_qml_3d:
            UISetup._setup_qml_3d_view(window)
        else:
            UISetup._setup_legacy_opengl_view(window)

        if window._qquick_widget:
            window.main_splitter.addWidget(window._qquick_widget)

        # Bottom section: Charts
        from src.ui.charts import ChartWidget

        window.chart_widget = ChartWidget(window)
        window.chart_widget.setMinimumHeight(200)
        window.main_splitter.addWidget(window.chart_widget)

        # Set stretch factors (3D gets more space)
        window.main_splitter.setStretchFactor(0, 3)  # 60% for 3D
        window.main_splitter.setStretchFactor(1, 2)  # 40% for charts

        # Add to horizontal splitter
        window.main_horizontal_splitter.addWidget(window.main_splitter)

        # Set as central widget
        window.setCentralWidget(window.main_horizontal_splitter)

        UISetup.logger.debug("✅ Система сплиттеров создана")

    @staticmethod
    def _setup_qml_3d_view(window: MainWindow) -> None:
        """Setup Qt Quick 3D scene with QQuickWidget

        Loads unified main.qml file with full suspension visualization.

        Args:
            window: MainWindow instance
        """
        UISetup.logger.info("    [QML] Загрузка main.qml...")

        try:
            window._qquick_widget = QQuickWidget(window)
            window._qquick_widget.setResizeMode(
                QQuickWidget.ResizeMode.SizeRootObjectToView
            )

            # Get QML engine
            engine = window._qquick_widget.engine()

            # ✅ КРИТИЧЕСКОЕ: Устанавливаем контекст ДО загрузки QML
            context = engine.rootContext()
            context.setContextProperty("window", window)

            try:
                from src.ui.scene_bridge import SceneBridge

                window._scene_bridge = SceneBridge(window)
                context.setContextProperty("pythonSceneBridge", window._scene_bridge)
                UISetup.logger.info("    ✅ SceneBridge exposed to QML context")
            except Exception as bridge_exc:
                window._scene_bridge = None
                UISetup.logger.error(
                    "    ❌ Failed to initialise SceneBridge: %s", bridge_exc
                )

            # Новые контексты: события настроек и трассировка сигналов
            try:
                from src.common.settings_manager import get_settings_event_bus
                from src.common.signal_trace import get_signal_trace_service

                context.setContextProperty("settingsEvents", get_settings_event_bus())
                context.setContextProperty("signalTrace", get_signal_trace_service())
            except Exception as inject_exc:
                UISetup.logger.warning(
                    "    ⚠️ Failed to inject diagnostics contexts: %s", inject_exc
                )

            UISetup.logger.info("    ✅ Window context registered")

            try:
                payload = UISetup.build_qml_context_payload(
                    getattr(window, "settings_manager", None)
                )
                context.setContextProperty(
                    "initialAnimationSettings", payload["animation"]
                )
                context.setContextProperty("initialSceneSettings", payload["scene"])
                context.setContextProperty(
                    "initialSharedMaterials", payload["materials"]
                )
                context.setContextProperty(
                    "initialDiagnosticsSettings", payload.get("diagnostics", {})
                )
                UISetup.logger.info("    ✅ Initial graphics settings exposed to QML")
            except Exception as ctx_exc:
                UISetup.logger.warning(
                    "    ⚠️ Failed to expose initial graphics settings: %s",
                    ctx_exc,
                )

            # Export profile manager
            profile_service = getattr(window, "profile_manager", None)
            try:
                if profile_service is not None:
                    context.setContextProperty("settingsProfiles", profile_service)
            except Exception as profile_exc:
                UISetup.logger.warning(
                    "    ⚠️ Failed to expose profile manager: %s", profile_exc
                )

            try:
                if profile_service is not None and hasattr(profile_service, "refresh"):
                    profile_service.refresh()
            except Exception as refresh_exc:
                UISetup.logger.debug(
                    "    ⚠️ Failed to refresh profile list: %s", refresh_exc
                )

            # Import paths
            from PySide6.QtCore import QLibraryInfo

            qml_import_path = QLibraryInfo.path(
                QLibraryInfo.LibraryPath.Qml2ImportsPath
            )
            engine.addImportPath(str(qml_import_path))

            local_qml_path = Path("assets/qml")
            if local_qml_path.exists():
                engine.addImportPath(str(local_qml_path.absolute()))

            # Load QML file
            qml_file = UISetup._resolve_supported_qml_scene()
            if not qml_file.exists():
                raise FileNotFoundError(f"QML file not found: {qml_file}")

            qml_url = QUrl.fromLocalFile(str(qml_file.absolute()))
            window._qquick_widget.setSource(qml_url)

            # Check status
            status = window._qquick_widget.status()
            if status == QQuickWidget.Status.Error:
                errors = window._qquick_widget.errors()
                error_msg = "\n".join(str(e) for e in errors)
                raise RuntimeError(f"QML load errors:\n{error_msg}")

            # Get root object
            window._qml_root_object = window._qquick_widget.rootObject()
            if not window._qml_root_object:
                raise RuntimeError("Failed to get QML root object")

            try:
                if getattr(window, "_scene_bridge", None) is not None:
                    window._qml_root_object.setProperty(
                        "sceneBridge", window._scene_bridge
                    )
                    UISetup.logger.info(
                        "    ✅ SceneBridge assigned to QML root property"
                    )
            except Exception as assign_exc:
                UISetup.logger.warning(
                    "    ⚠️ Failed to assign SceneBridge to QML root: %s", assign_exc
                )

            # Store base directory
            window._qml_base_dir = qml_file.parent.resolve()

            UISetup.logger.info("    ✅ %s loaded successfully", qml_file.name)

        except Exception as e:
            UISetup.logger.exception(f"    ❌ QML load failed: {e}")

            # Fallback: error label
            fallback = QLabel(
                f"КРИТИЧЕСКАЯ ОШИБКА ЗАГРУЗКИ 3D СЦЕНЫ\n\n"
                f"Ошибка: {e}\n\n"
                f"Проверьте файл assets/qml/main.qml"
            )
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setStyleSheet(
                "background: #1a1a2e; color: #ff6b6b; font-size: 12px; padding: 20px;"
            )
            window._qquick_widget = fallback

    @staticmethod
    def _setup_legacy_opengl_view(window: MainWindow) -> None:
        """Setup legacy OpenGL widget (stub)"""
        UISetup.logger.debug("_setup_legacy_opengl_view: Fallback to QML")
        UISetup._setup_qml_3d_view(window)

    @staticmethod
    def _normalize_scene_key(value: str) -> str:
        key = value.strip().lower().replace("-", "_")
        if key.endswith(".qml"):
            key = key[:-4]
        if key.startswith("main.") and key != "main":
            key = key.split(".", 1)[0]
        if key.startswith("main_") and key != "main":
            key = key[len("main_") :]
        return key

    @staticmethod
    def _resolve_supported_qml_scene() -> Path:
        """Resolve which QML scene should be loaded."""

        requested = os.environ.get(UISetup._SCENE_ENV_VAR)
        load_order = list(UISetup._SCENE_LOAD_ORDER)

        if requested:
            normalized = UISetup._normalize_scene_key(requested)
            if normalized in UISetup._SUPPORTED_SCENES:
                load_order = [normalized] + [
                    name for name in load_order if name != normalized
                ]
                UISetup.logger.info(
                    "    [QML] Requested scene via %s: %s",
                    UISetup._SCENE_ENV_VAR,
                    UISetup._SUPPORTED_SCENES[normalized].name,
                )
            else:
                UISetup.logger.warning(
                    "    [QML] Unsupported scene '%s' requested via %s. Allowed: %s",
                    requested,
                    UISetup._SCENE_ENV_VAR,
                    ", ".join(
                        UISetup._SUPPORTED_SCENES[name].name
                        for name in UISetup._SCENE_LOAD_ORDER
                    ),
                )

        for scene_key in load_order:
            scene_path = UISetup._SUPPORTED_SCENES[scene_key]
            if scene_path.exists():
                UISetup.logger.info("    [QML] Загрузка сцены: %s", scene_path.name)
                return scene_path
            UISetup.logger.debug(
                "    [QML] Scene %s not found at %s",
                scene_key,
                scene_path,
            )

        searched = ", ".join(
            str(UISetup._SUPPORTED_SCENES[key]) for key in UISetup._SCENE_LOAD_ORDER
        )
        raise FileNotFoundError("No supported QML scenes found. Checked: " + searched)

    # ------------------------------------------------------------------
    # Tabs Setup
    # ------------------------------------------------------------------
    @staticmethod
    def setup_tabs(window: MainWindow) -> None:
        """Создать вкладки с панелями параметров

        Tabs:
          - Геометрия (Geometry)
          - Пневмосистема (Pneumatics)
          - Режимы стабилизатора (Modes)
          - Графика (Graphics)
          - Динамика движения (Road - stub)

        Args:
            window: MainWindow instance
        """
        UISetup.logger.debug("setup_tabs: Создание вкладок...")

        # Create tab widget
        window.tab_widget = QTabWidget(window)
        window.tab_widget.setObjectName("ParameterTabs")
        window.tab_widget.setMinimumWidth(300)
        window.tab_widget.setMaximumWidth(800)

        # Import panels
        from src.ui.panels import (
            GeometryPanel,
            PneumoPanel,
            ModesPanel,
            GraphicsPanel,
        )

        # Tab 1: Геометрия
        window.geometry_panel = GeometryPanel(window)
        scroll_geometry = QScrollArea()
        scroll_geometry.setWidgetResizable(True)
        scroll_geometry.setWidget(window.geometry_panel)
        scroll_geometry.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        window.tab_widget.addTab(scroll_geometry, "Геометрия")

        # Tab 2: Пневмосистема
        window.pneumo_panel = PneumoPanel(window)
        scroll_pneumo = QScrollArea()
        scroll_pneumo.setWidgetResizable(True)
        scroll_pneumo.setWidget(window.pneumo_panel)
        scroll_pneumo.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        window.tab_widget.addTab(scroll_pneumo, "Пневмосистема")

        # Tab 3: Режимы стабилизатора
        window.modes_panel = ModesPanel(window)
        scroll_modes = QScrollArea()
        scroll_modes.setWidgetResizable(True)
        scroll_modes.setWidget(window.modes_panel)
        scroll_modes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        window.tab_widget.addTab(scroll_modes, "Режимы стабилизатора")

        # Tab 4: Графика (без дополнительного ScrollArea!)
        window.graphics_panel = GraphicsPanel(window)
        window._graphics_panel = window.graphics_panel  # Alias
        window.tab_widget.addTab(window.graphics_panel, "🎨 Графика")

        # Tab 5: Динамика движения (stub)
        dynamics_stub = QWidget()
        dynamics_layout = QVBoxLayout(dynamics_stub)
        dynamics_label = QLabel(
            "Динамика движения\n\n"
            "Генератор профилей дороги\n"
            "(Будет реализовано отдельным промтом)"
        )
        dynamics_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dynamics_label.setStyleSheet("color: #888; font-size: 12px; padding: 20px;")
        dynamics_layout.addWidget(dynamics_label)
        dynamics_layout.addStretch()
        window.tab_widget.addTab(dynamics_stub, "Динамика движения")

        # Add to horizontal splitter
        window.main_horizontal_splitter.addWidget(window.tab_widget)

        # Set stretch factors
        window.main_horizontal_splitter.setStretchFactor(0, 3)  # 75% scene+charts
        window.main_horizontal_splitter.setStretchFactor(1, 1)  # 25% panels

        # Restore last tab
        settings = QSettings(window.SETTINGS_ORG, window.SETTINGS_APP)
        last_tab = settings.value(window.SETTINGS_LAST_TAB, 0, type=int)
        if 0 <= last_tab < window.tab_widget.count():
            window.tab_widget.setCurrentIndex(last_tab)

        # Connect tab change signal
        window.tab_widget.currentChanged.connect(window._on_tab_changed)

        UISetup.logger.debug("✅ Вкладки созданы")

    # ------------------------------------------------------------------
    # Menus Setup
    # ------------------------------------------------------------------
    @staticmethod
    def setup_menus(window: MainWindow) -> None:
        """Создать меню приложения

        Menus:
          - Файл (File): Выход
          - Вид (View): Сбросить расположение

        Args:
            window: MainWindow instance
        """
        menubar = window.menuBar()
        menubar.clear()

        # File menu
        file_menu = menubar.addMenu("Файл")
        exit_action = QAction("Выход", window)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(window.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("Вид")
        reset_layout_action = QAction("Сбросить расположение", window)
        reset_layout_action.triggered.connect(window._reset_ui_layout)
        view_menu.addAction(reset_layout_action)

        UISetup.logger.debug("✅ Меню создано")

    # ------------------------------------------------------------------
    # Toolbar Setup
    # ------------------------------------------------------------------
    @staticmethod
    def setup_toolbar(window: MainWindow) -> None:
        """Создать панель инструментов

        Buttons:
          - ▶ Старт
          - ⏸ Пауза
          - ⏹ Стоп
          - ↺ Сброс

        Args:
            window: MainWindow instance
        """
        toolbar = window.addToolBar("Основная")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(True)

        actions = [
            ("▶ Старт", "start"),
            ("⏸ Пауза", "pause"),
            ("⏹ Стоп", "stop"),
            ("↺ Сброс", "reset"),
        ]

        for title, command in actions:
            act = QAction(title, window)
            act.triggered.connect(
                lambda _=False, cmd=command: window._on_sim_control(cmd)
            )
            toolbar.addAction(act)

        UISetup.logger.debug("✅ Панель инструментов создана")

    # ------------------------------------------------------------------
    # Status Bar Setup
    # ------------------------------------------------------------------
    @staticmethod
    def setup_status_bar(window: MainWindow) -> None:
        """Создать строку состояния

        Displays:
          - Sim Time
          - Steps
          - Physics FPS
          - Queue stats

        Args:
            window: MainWindow instance
        """
        status_bar = QStatusBar(window)
        window.setStatusBar(status_bar)

        window.sim_time_label = QLabel("Sim Time: 0.000s")
        window.step_count_label = QLabel("Steps: 0")
        window.fps_label = QLabel("Physics FPS: 0.0")
        window.queue_label = QLabel("Queue: 0/0")

        for widget in (
            window.sim_time_label,
            window.step_count_label,
            window.fps_label,
            window.queue_label,
        ):
            widget.setStyleSheet("padding: 0 6px")
            status_bar.addPermanentWidget(widget)

        window.status_bar = status_bar

        UISetup.logger.debug("✅ Строка состояния создана")
