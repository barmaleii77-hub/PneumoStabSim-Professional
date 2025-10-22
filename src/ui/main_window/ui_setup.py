"""UI Setup Module - MainWindow UI construction

Модуль построения UI элементов главного окна.
Отвечает за создание всех виджетов, сплиттеров, панелей и их расположение.

Russian UI / English code.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

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
    from .main_window import MainWindow


class UISetup:
    """Построение UI элементов главного окна

    Static methods для делегирования из MainWindow.
    Каждый метод принимает `window: MainWindow` как первый аргумент.
    """

    logger = logging.getLogger(__name__)

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
            UISetup.logger.info("    ✅ Window context registered")

            # Expose initial settings to QML context
            from src.settings import SimulationSettings

            settings = SimulationSettings()
            context.setContextProperty("simSettings", settings)
            UISetup.logger.info("    ✅ Simulation settings context registered")

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
            qml_file = Path("assets/qml/main.qml")
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

            # Store base directory
            window._qml_base_dir = qml_file.parent.resolve()

            UISetup.logger.info("    ✅ main.qml loaded successfully")

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
                "background: #1a1a2e; color: #ff6b6b; "
                "font-size: 12px; padding: 20px;"
            )
            window._qquick_widget = fallback

    @staticmethod
    def _setup_legacy_opengl_view(window: MainWindow) -> None:
        """Setup legacy OpenGL widget (stub)"""
        UISetup.logger.debug("_setup_legacy_opengl_view: Fallback to QML")
        UISetup._setup_qml_3d_view(window)

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
