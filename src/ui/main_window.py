"""
Main window for PneumoStabSim application
Qt Quick 3D rendering with QQuickWidget (no createWindowContainer)
РУССКИЙ ИНТЕРФЕЙС (Russian UI)
"""
from PySide6.QtWidgets import (
    QMainWindow, QStatusBar, QDockWidget, QWidget, QMenuBar, QToolBar, QLabel,
    QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QApplication, QSplitter,
    QTabWidget, QScrollArea
)
from PySide6.QtCore import (
    Qt,
    QTimer,
    Slot,
    QSettings,
    QUrl,
    QFileInfo,
    QByteArray,
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtQuickWidgets import QQuickWidget
import logging
import json
import numpy as np
import time
from pathlib import Path
from typing import Optional, Dict, Any

from src.ui.charts import ChartWidget
from src.ui.panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
from ..runtime import SimulationManager, StateSnapshot


class MainWindow(QMainWindow):
    """Главное окно приложения с Qt Quick 3D (RHI/Direct3D)
    
    Main application window with Qt Quick 3D rendering (RHI/Direct3D)
    RUSSIAN UI - Русский интерфейс
    """
    SETTINGS_ORG = "PneumoStabSim"
    SETTINGS_APP = "PneumoStabSimApp"
    SETTINGS_GEOMETRY = "MainWindow/Geometry"
    SETTINGS_STATE = "MainWindow/State"
    SETTINGS_SPLITTER = "MainWindow/Splitter"
    SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"
    SETTINGS_LAST_TAB = "MainWindow/LastTab"
    SETTINGS_LAST_PRESET = "Presets/LastPath"

    QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
        "geometry": ("applyGeometryUpdates", "updateGeometry"),
        "animation": ("applyAnimationUpdates", "updateAnimation"),
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

    def __init__(self, use_qml_3d: bool = True):
        super().__init__()
        
        # Store visualization backend choice
        self.use_qml_3d = use_qml_3d
        
        backend_name = "Qt Quick 3D (Enhanced v5.0)" if use_qml_3d else "Legacy OpenGL"
        self.setWindowTitle(f"PneumoStabSim - {backend_name}")
        
        self.resize(1400, 900)
        self.setMinimumSize(1200, 800)
        self.setWindowState(Qt.WindowState.WindowNoState)

        # Logging
        self.logger = logging.getLogger(self.__class__.__name__)
        
        print("MainWindow: Создание SimulationManager...")
        
        # Simulation manager
        try:
            self.simulation_manager = SimulationManager(self)
            print("✅ SimulationManager создан (не запущен)")
        except Exception as e:
            print(f"❌ Ошибка создания SimulationManager: {e}")
            import traceback
            traceback.print_exc()
            raise

        # QML update system
        self._qml_update_queue: Dict[str, Dict[str, Any]] = {}
        self._qml_method_support: Dict[tuple[str, bool], bool] = {}
        self._qml_flush_timer = QTimer()
        self._qml_flush_timer.setSingleShot(True)
        self._qml_flush_timer.timeout.connect(self._flush_qml_updates)
        
        # State tracking
        self.current_snapshot: Optional[StateSnapshot] = None
        self.is_simulation_running = False
        self._sim_started = False

        # Geometry converter for Python↔QML integration
        from src.ui.geometry_bridge import create_geometry_converter
        self.geometry_converter = create_geometry_converter()
        print("✅ GeometryBridge создан для интеграции Python↔QML")

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

        # Qt Quick 3D view reference
        self._qquick_widget: Optional[QQuickWidget] = None
        self._qml_root_object = None
        self._qml_base_dir: Optional[Path] = None

        print("MainWindow: Построение UI...")
        
        # Build UI
        self._setup_central()
        print("  ✅ Центральный вид Qt Quick 3D настроен")
        
        self._setup_tabs()
        print("  ✅ Вкладки настроены")
        
        self._setup_menus()
        print("  ✅ Меню настроено")
        
        self._setup_toolbar()
        print("  ✅ Панель инструментов настроена")
        
        self._setup_status_bar()
        print("  ✅ Строка состояния настроена")
        
        self._connect_simulation_signals()
        print("  ✅ Сигналы подключены")

        # Render timer (UI thread ~60 FPS)
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self._update_render)
        self.render_timer.start(16)
        print("  ✅ Таймер рендеринга запущен")

        print("  ⏸️  SimulationManager запустится после window.show()")

        # Restore settings
        self._restore_settings()
        print("  ✅ Настройки восстановлены")

        self.logger.info("Главное окно (Qt Quick 3D) инициализировано")
        print("✅ MainWindow.__init__() завершён")

    # ------------------------------------------------------------------
    # UI Construction - НОВАЯ СТРУКТРАА!
    # ------------------------------------------------------------------
    def _setup_central(self):
        """Создать центральный вид с горизонтальным и вертикальным сплиттерами
        
        Create central view with horizontal and vertical splitters:
        Layout: [3D Scene (top) + Charts (bottom)] | [Control Panels (right)]
        """
        print("    _setup_central: Создание системы сплиттеров...")
        
        # Create main horizontal splitter (left: scene+charts, right: panels)
        self.main_horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_horizontal_splitter.setObjectName("MainHorizontalSplitter")
        
        # Create vertical splitter for left side (scene + charts)
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setObjectName("SceneChartsSplitter")
        
        # Top section of vertical splitter: 3D scene
        if self.use_qml_3d:
            self._setup_qml_3d_view()
        else:
            self._setup_legacy_opengl_view()
        
        if self._qquick_widget:
            self.main_splitter.addWidget(self._qquick_widget)
        
        # Bottom section of vertical splitter: Charts
        self.chart_widget = ChartWidget(self)
        self.chart_widget.setMinimumHeight(200)  # Minimum chart height
        self.main_splitter.addWidget(self.chart_widget)
        
        # Set stretch factors for vertical splitter (3D scene gets more space)
        self.main_splitter.setStretchFactor(0, 3)  # 60% for 3D
        self.main_splitter.setStretchFactor(1, 2)  # 40% for charts
        
        # Add vertical splitter to left side of horizontal splitter
        self.main_horizontal_splitter.addWidget(self.main_splitter)
        
        # Right side will be added in _setup_tabs() method
        
        # Set as central widget
        self.setCentralWidget(self.main_horizontal_splitter)
        
        print("    ✅ Система сплиттеров создана (горизонтальный + вертикальный)")

    def _setup_qml_3d_view(self):
        """Setup Qt Quick 3D full suspension scene - загружает main.qml"""
        print("    [QML] Загрузка QML файла main.qml...")
        
        try:
            self._qquick_widget = QQuickWidget(self)
            self._qquick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
            
            # Используем единый файл main.qml
            qml_path = Path("assets/qml/main.qml")
            
            print(f"    🔍 ДИАГНОСТИКА ЗАГРУЗКИ QML:")
            print(f"       Целевой файл: {qml_path}")
            print(f"       Файл существует: {qml_path.exists()}")
            
            if not qml_path.exists():
                raise FileNotFoundError(f"QML файл не найден: {qml_path}")
            
            file_size = qml_path.stat().st_size
            print(f"       Размер файла: {file_size:,} байт")
            
            qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
            print(f"    📂 Полный путь: {qml_url.toString()}")
            
            self._qquick_widget.setSource(qml_url)
            
            status = self._qquick_widget.status()
            print(f"    📊 QML статус загрузки: {status}")
            
            if status == QQuickWidget.Status.Error:
                errors = self._qquick_widget.errors()
                error_messages = [str(e) for e in errors]
                error_msg = "\n".join(error_messages)
                print(f"    ❌ ОШИБКИ QML ЗАГРУЗКИ:")
                for i, error in enumerate(error_messages, 1):
                    print(f"       {i}. {error}")
                raise RuntimeError(f"Ошибки загрузки QML:\n{error_msg}")
                    
            elif status == QQuickWidget.Status.Loading:
                print(f"    ⏳ QML файл загружается...")
            elif status == QQuickWidget.Status.Ready:
                print(f"    ✅ QML файл загружен успешно!")
            
            self._qml_root_object = self._qquick_widget.rootObject()
            if not self._qml_root_object:
                raise RuntimeError("Не удалось получить корневой объект QML")

            self._qml_method_support.clear()
            self._qml_base_dir = qml_path.parent.resolve()

            print(f"    [OK] ✅ QML файл 'main.qml' загружен успешно")
            
        except Exception as e:
            print(f"    [CRITICAL] Ошибка загрузки main.qml: {e}")
            import traceback
            traceback.print_exc()
            
            fallback = QLabel(
                "КРИТИЧЕСКАЯ ОШИБКА ЗАГРУЗКИ 3D СЦЕНЫ\n\n"
                f"Ошибка: {e}\n\n"
                "Проверьте файл assets/qml/main.qml"
            )
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setStyleSheet("background: #1a1a2e; color: #ff6b6b; font-size: 12px; padding: 20px;")
            self._qquick_widget = fallback
            print(f"    [WARNING] Использован заглушка-виджет")

    def _setup_legacy_opengl_view(self):
        """Setup legacy OpenGL widget"""
        print("    _setup_legacy_opengl_view: Загрузка legacy QML...")
        self._setup_qml_3d_view()

    def _setup_tabs(self):
        """Создать вкладки с панелями параметров (справа от сцены через сплиттер)
        
        Create tabbed panels on the right side with resizable splitter:
          - Геометрия (Geometry)
          - Пневмосистема (Pneumatics)
          - Режимы стабилизатора (Modes)
          - Графика (Graphics settings)
          - Визуализация (Visualization - stub)
          - Динамика движения (Road/Dynamics - stub)
        """
        print("    _setup_tabs: Создание вкладок с ресайзбаром...")
        
        # Create tab widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setObjectName("ParameterTabs")
        self.tab_widget.setMinimumWidth(300)  # Reduced minimum width
        self.tab_widget.setMaximumWidth(600)  # Increased maximum width for resizing
        
        # Tab 1: ГеОМЕТРИЯ (Geometry)
        self.geometry_panel = GeometryPanel(self)
        scroll_geometry = QScrollArea()
        scroll_geometry.setWidgetResizable(True)
        scroll_geometry.setWidget(self.geometry_panel)
        scroll_geometry.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tab_widget.addTab(scroll_geometry, "Геометрия")
        print("      ✅ Вкладка 'Геометрия' создана")
        
        # Tab 2: ПНЕВМОСИСТЕМА (Pneumatics)
        self.pneumo_panel = PneumoPanel(self)
        scroll_pneumo = QScrollArea()
        scroll_pneumo.setWidgetResizable(True)
        scroll_pneumo.setWidget(self.pneumo_panel)
        scroll_pneumo.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tab_widget.addTab(scroll_pneumo, "Пневмосистема")
        print("      ✅ Вкладка 'Пневмосистема' создана")
        
        # Tab 3: РЕЖИМЫ СТАБИЛИЗАТОРА (Modes)
        self.modes_panel = ModesPanel(self)
        scroll_modes = QScrollArea()
        scroll_modes.setWidgetResizable(True)
        scroll_modes.setWidget(self.modes_panel)
        scroll_modes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tab_widget.addTab(scroll_modes, "Режимы стабилизатора")
        print("      ✅ Вкладка 'Режимы стабилизатора' создана")
        
        # Tab 4: ГРАФИКА И ВИЗУАЛИЗАЦИЯ (объединенная панель)
        self.graphics_panel = GraphicsPanel(self)
        # Не помещаем в scroll area, так как панель уже имеет собственные вкладки с прокруткой
        self.tab_widget.addTab(self.graphics_panel, "🎨 Графика")
        print("      ✅ Вкладка 'Графика и визуализация' создана")
        
        # Tab 5: ДИНАМИКА ДВИЖЕНИЯ (Road/Dynamics - stub, NO CSV loading!)
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
        self.tab_widget.addTab(dynamics_stub, "Динамика движения")
        print("      ✅ Вкладка 'Динамика движения' создана (заглушка)")
        
        # Add tab widget to right side of horizontal splitter
        self.main_horizontal_splitter.addWidget(self.tab_widget)
        
        # Set stretch factors for horizontal splitter
        self.main_horizontal_splitter.setStretchFactor(0, 3)  # 75% for scene+charts
        self.main_horizontal_splitter.setStretchFactor(1, 1)  # 25% for panels
        
        # Connect panel signals
        self._wire_panel_signals()
        
        # Restore last selected tab
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        last_tab = settings.value(self.SETTINGS_LAST_TAB, 0, type=int)
        if 0 <= last_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(last_tab)
        
        # Save selected tab on change
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        print("    ✅ Вкладки созданы и подключены к горизональному сплиттеру")

    @Slot(int)
    def _on_tab_changed(self, index: int):
        """Сохранить выбранную вкладку / Save selected tab"""
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        settings.setValue(self.SETTINGS_LAST_TAB, index)
        
        tab_names = [
            "Геометрия", "Пневмосистема", "Режимы стабилизатора",
            "Графика и визуализация", "Динамика движения"
        ]
        if 0 <= index < len(tab_names):
            self.logger.debug(f"Переключено на вкладку: {tab_names[index]}")

    def _wire_panel_signals(self):
        """Connect panel signals to simulation/state bus"""
        bus = self.simulation_manager.state_bus

        # Geometry updates
        if self.geometry_panel:
            self.geometry_panel.parameter_changed.connect(
                lambda name, val: [
                    self.logger.info(f"Параметр геометрии {name}={val}"),
                    print(f"🔧 GeometryPanel: {name}={val}")
                ])
            # ИСПРАВЛЕНО: Подключаем geometry_changed сигнал к обработчику QML
            self.geometry_panel.geometry_changed.connect(self._on_geometry_changed_qml)
            print("✅ Сигналы GeometryPanel подключены (geometry_changed → QML)")

        # Pneumatic panel
        if self.pneumo_panel:
            # ВРЕМЕННАЯ ЗАГЛУШКА - просто логируем
            self.pneumo_panel.mode_changed.connect(lambda mode_type, new_mode: print(f"🔧 Mode changed: {mode_type} -> {new_mode}"))
            self.pneumo_panel.parameter_changed.connect(lambda name, value: print(f"🔧 Pneumo param: {name} = {value}"))
            print("✅ Сигналы PneumoPanel подключены (ЗАГЛУШКА)")

        # Modes panel
        if self.modes_panel:
            # Simulation control
            self.modes_panel.simulation_control.connect(self._on_sim_control)
            print("✅ Сигнал simulation_control подключен")
            
            # Mode changes (заглушка)
            self.modes_panel.mode_changed.connect(lambda mode_type, new_mode: print(f"🔧 Mode changed: {mode_type} -> {new_mode}"))
            
            # Parameter changes (заглушка)
            self.modes_panel.parameter_changed.connect(lambda n, v: print(f"🔧 Param: {n} = {v}"))
            
            # ✨ НОВОЕ: Подключаем обработчик изменения параметров анимации
            self.modes_panel.animation_changed.connect(self._on_animation_changed)
            print("✅ Сигнал animation_changed подключен к _on_animation_changed")
            
            print("✅ Сигналы ModesPanel подключены")

        # Graphics panel  
        if self.graphics_panel:
            # Lighting changes
            self.graphics_panel.lighting_changed.connect(self._on_lighting_changed)
            print("✅ Сигнал lighting_changed подключен")
            
            # Material changes
            self.graphics_panel.material_changed.connect(self._on_material_changed)
            print("✅ Сигнал material_changed подключен")
            
            # Environment changes
            self.graphics_panel.environment_changed.connect(self._on_environment_changed)  
            print("✅ Сигнал environment_changed подключен")
            
            # Quality changes
            self.graphics_panel.quality_changed.connect(self._on_quality_changed)
            print("✅ Сигнал quality_changed подключен")
            
            # Camera changes
            self.graphics_panel.camera_changed.connect(self._on_camera_changed)
            print("✅ Сигнал camera_changed подключен")
            
            # Effects changes
            self.graphics_panel.effects_changed.connect(self._on_effects_changed)
            print("✅ Сигнал effects_changed подключен")
            
            # Preset applied
            self.graphics_panel.preset_applied.connect(self._on_preset_applied)
            print("✅ Сигнал preset_applied подключен")
            
            print("✅ Все сигналы GraphicsPanel подключены")

    @Slot(dict)
    def _on_geometry_changed_qml(self, geometry_params: dict):
        """Получить обновления геометрии от панели и передать их в сцену."""
        if not isinstance(geometry_params, dict):
            self.logger.warning("Geometry update payload is not a dict: %r", geometry_params)
            return

        self.logger.info(
            "Geometry update received (%d keys): %s",
            len(geometry_params),
            list(geometry_params.keys()),
        )

        self._queue_qml_update("geometry", geometry_params)

        if self.status_bar:
            self.status_bar.showMessage("Геометрия отправлена в 3D сцену", 2000)


    # ------------------------------------------------------------------
    # Меню, тулбар и строка состояния
    # ------------------------------------------------------------------
    def _setup_menus(self):
        """Создать простое меню приложения"""
        menubar = self.menuBar()
        menubar.clear()

        file_menu = menubar.addMenu("Файл")
        exit_action = QAction("Выход", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("Вид")
        reset_layout_action = QAction("Сбросить расположение", self)
        reset_layout_action.triggered.connect(self._reset_ui_layout)
        view_menu.addAction(reset_layout_action)

    def _setup_toolbar(self):
        """Создать верхнюю панель управления симуляцией"""
        toolbar = self.addToolBar("Основная")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(True)

        actions = [
            ("▶ Старт", "start"),
            ("⏸ Пауза", "pause"),
            ("⏹ Стоп", "stop"),
            ("↺ Сброс", "reset"),
        ]

        for title, command in actions:
            act = QAction(title, self)
            act.triggered.connect(lambda _=False, cmd=command: self._on_sim_control(cmd))
            toolbar.addAction(act)

    def _setup_status_bar(self):
        """Создать строку состояния с диагностикой"""
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)

        self.sim_time_label = QLabel("Sim Time: 0.000s")
        self.step_count_label = QLabel("Steps: 0")
        self.fps_label = QLabel("Physics FPS: 0.0")
        self.queue_label = QLabel("Queue: 0/0")

        for widget in (self.sim_time_label, self.step_count_label, self.fps_label, self.queue_label):
            widget.setStyleSheet("padding: 0 6px")
            status_bar.addPermanentWidget(widget)

        self.status_bar = status_bar

    # ------------------------------------------------------------------
    # Сохранение и восстановление состояния окна
    # ------------------------------------------------------------------
    def _restore_settings(self):
        """Восстановить геометрию окна и положение сплиттеров"""
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)

        geometry = settings.value(self.SETTINGS_GEOMETRY)
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)
        elif isinstance(geometry, (bytes, bytearray)):
            self.restoreGeometry(QByteArray(geometry))

        state = settings.value(self.SETTINGS_STATE)
        if isinstance(state, QByteArray):
            self.restoreState(state)
        elif isinstance(state, (bytes, bytearray)):
            self.restoreState(QByteArray(state))

        splitter_state = settings.value(self.SETTINGS_SPLITTER)
        if isinstance(splitter_state, QByteArray) and self.main_splitter:
            self.main_splitter.restoreState(splitter_state)
        elif isinstance(splitter_state, (bytes, bytearray)) and self.main_splitter:
            self.main_splitter.restoreState(QByteArray(splitter_state))

        hsplit_state = settings.value(self.SETTINGS_HORIZONTAL_SPLITTER)
        if isinstance(hsplit_state, QByteArray) and self.main_horizontal_splitter:
            self.main_horizontal_splitter.restoreState(hsplit_state)
        elif isinstance(hsplit_state, (bytes, bytearray)) and self.main_horizontal_splitter:
            self.main_horizontal_splitter.restoreState(QByteArray(hsplit_state))

    def _save_settings(self):
        """Сохранить текущие настройки интерфейса"""
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        settings.setValue(self.SETTINGS_GEOMETRY, self.saveGeometry())
        settings.setValue(self.SETTINGS_STATE, self.saveState())

        if self.main_splitter:
            settings.setValue(self.SETTINGS_SPLITTER, self.main_splitter.saveState())
        if self.main_horizontal_splitter:
            settings.setValue(
                self.SETTINGS_HORIZONTAL_SPLITTER,
                self.main_horizontal_splitter.saveState(),
            )

    def _reset_ui_layout(self):
        """Сбросить размеры сплиттеров к значениям по умолчанию"""
        if self.main_splitter:
            self.main_splitter.setSizes([3, 2])
        if self.main_horizontal_splitter:
            self.main_horizontal_splitter.setSizes([3, 1])
        if hasattr(self, "status_bar"):
            self.status_bar.showMessage("Макет интерфейса сброшен", 2000)

    # ------------------------------------------------------------------
    # Интеграция с SimulationManager
    # ------------------------------------------------------------------
    def _connect_simulation_signals(self):
        bus = self.simulation_manager.state_bus
        bus.state_ready.connect(self._on_state_update, Qt.QueuedConnection)
        bus.physics_error.connect(self._on_physics_error, Qt.QueuedConnection)

    @Slot(object)
    def _on_state_update(self, snapshot: StateSnapshot):
        self.current_snapshot = snapshot

        if snapshot:
            self.sim_time_label.setText(f"Sim Time: {snapshot.simulation_time:.3f}s")
            self.step_count_label.setText(f"Steps: {snapshot.step_number}")

            if snapshot.aggregates.physics_step_time > 0:
                fps = 1.0 / snapshot.aggregates.physics_step_time
                self.fps_label.setText(f"Physics FPS: {fps:.1f}")

            self._update_3d_from_snapshot(snapshot)

        if self.chart_widget:
            self.chart_widget.update_from_snapshot(snapshot)

    @Slot(str)
    def _on_physics_error(self, message: str):
        self.logger.error(f"Physics engine error: {message}")
        if hasattr(self, "status_bar"):
            self.status_bar.showMessage(f"Physics error: {message}", 5000)

    def _update_render(self):
        """Обновление метрик и плавного времени анимации"""
        if not self._qml_root_object:
            return

        now = time.perf_counter()
        last_tick = getattr(self, "_last_animation_tick", None)
        self._last_animation_tick = now

        if bool(self._qml_root_object.property("isRunning")) and last_tick is not None:
            elapsed = now - last_tick
            current = self._qml_root_object.property("animationTime") or 0.0
            self._qml_root_object.setProperty("animationTime", float(current) + float(elapsed))

        # ✅ ИСПРАВЛЕНО: Проверка наличия state_queue перед вызовом get_stats()
        if hasattr(self.simulation_manager, 'state_queue') and self.simulation_manager.state_queue is not None:
            stats = self.simulation_manager.get_queue_stats()
            self.queue_label.setText(f"Queue: {stats.get('get_count', 0)}/{stats.get('put_count', 0)}")
        else:
            self.queue_label.setText("Queue: -/-")

    # ------------------------------------------------------------------
    # Обновление QML сцены
    # ------------------------------------------------------------------
    def _queue_qml_update(self, key: str, params: Dict[str, Any]):
        if not params:
            return

        if key not in self._qml_update_queue:
            self._qml_update_queue[key] = {}

        self._deep_merge_dicts(self._qml_update_queue[key], params)

        if not self._qml_flush_timer.isActive():
            self._qml_flush_timer.start(0)

    def _flush_qml_updates(self):
        if not self._qml_update_queue:
            return

        if not self._qml_root_object:
            # Попробуем снова, когда QML будет готов
            self._qml_flush_timer.start(100)
            return

        pending = self._qml_update_queue
        self._qml_update_queue = {}

        for key, payload in pending.items():
            methods = self.QML_UPDATE_METHODS.get(key, ())
            success = False
            for method_name in methods:
                if self._invoke_qml_function(method_name, payload):
                    success = True
                    break

            if success:
                continue

            self._apply_fallback(key, payload)

    def _invoke_qml_function(self, method_name: str, payload: Optional[Dict[str, Any]] = None) -> bool:
        if not self._qml_root_object:
            return False

        has_payload = payload is not None
        cache_key = (method_name, has_payload)
        cached = self._qml_method_support.get(cache_key)
        if cached is False:
            return False

        candidate = getattr(self._qml_root_object, method_name, None)
        if not callable(candidate):
            self._qml_method_support[cache_key] = False
            return False

        try:
            if payload is None:
                candidate()
            else:
                candidate(payload)
        except TypeError as exc:
            self.logger.debug(
                "QML callable %s rejected payload: %s",
                method_name,
                exc,
            )
            self._qml_method_support[cache_key] = False
            return False
        except Exception as exc:
            self.logger.warning(
                "Unhandled exception when invoking QML callable %s: %s",
                method_name,
                exc,
            )
            self._qml_method_support[cache_key] = False
            return False

        self._qml_method_support[cache_key] = True
        return True

    @staticmethod
    def _deep_merge_dicts(target: Dict[str, Any], source: Dict[str, Any]):
        for key, value in source.items():
            if (
                isinstance(value, dict)
                and key in target
                and isinstance(target[key], dict)
            ):
                MainWindow._deep_merge_dicts(target[key], value)
            else:
                target[key] = value

    def _apply_fallback(self, key: str, payload: Dict[str, Any]) -> None:
        if not payload:
            return

        handlers = {
            "geometry": self._apply_geometry_fallback,
            "lighting": self._apply_lighting_fallback,
            "environment": self._apply_environment_fallback,
            "quality": self._apply_quality_fallback,
            "camera": self._apply_camera_fallback,
            "effects": self._apply_effects_fallback,
            "materials": self._apply_materials_fallback,
        }

        handler = handlers.get(key)
        if handler:
            handler(payload)
        else:
            self.logger.debug("No fallback handler for %s", key)

    def _apply_geometry_fallback(self, geometry: Dict[str, Any]) -> None:
        mapping = {
            ("frameLength",): ("userFrameLength", float),
            ("frameHeight",): ("userFrameHeight", float),
            ("frameBeamSize",): ("userBeamSize", float),
            ("leverLength",): ("userLeverLength", float),
            ("cylinderBodyLength",): ("userCylinderLength", float),
            ("trackWidth",): ("userTrackWidth", float),
            ("frameToPivot",): ("userFrameToPivot", float),
            ("rodPosition",): ("userRodPosition", float),
            ("boreHead",): ("userBoreHead", float),
            ("boreRod",): ("userBoreRod", float),
            ("rodDiameter",): ("userRodDiameter", float),
            ("pistonThickness",): ("userPistonThickness", float),
            ("pistonRodLength",): ("userPistonRodLength", float),
        }
        self._apply_nested_mapping(geometry, mapping)

    def _apply_lighting_fallback(self, lighting: Dict[str, Any]) -> None:
        mapping = {
            ("key_light", "brightness"): ("keyLightBrightness", float),
            ("key_light", "color"): "keyLightColor",
            ("key_light", "angle_x"): ("keyLightAngleX", float),
            ("key_light", "angle_y"): ("keyLightAngleY", float),
            ("fill_light", "brightness"): ("fillLightBrightness", float),
            ("fill_light", "color"): "fillLightColor",
            ("rim_light", "brightness"): ("rimLightBrightness", float),
            ("rim_light", "color"): "rimLightColor",
            ("point_light", "brightness"): ("pointLightBrightness", float),
            ("point_light", "color"): "pointLightColor",
            ("point_light", "position_y"): ("pointLightY", float),
            ("point_light", "range"): ("pointLightRange", float),
        }
        self._apply_nested_mapping(lighting, mapping)

    def _apply_environment_fallback(self, environment: Dict[str, Any]) -> None:
        mapping = {
            ("background", "mode"): "backgroundMode",
            ("background", "color"): "backgroundColor",
            ("ibl", "enabled"): "iblEnabled",
            ("ibl", "intensity"): ("iblIntensity", float),
            ("ibl", "blur"): ("skyboxBlur", float),
            ("fog", "enabled"): "fogEnabled",
            ("fog", "color"): "fogColor",
            ("fog", "density"): ("fogDensity", float),
            ("fog", "near"): ("fogNear", float),
            ("fog", "far"): ("fogFar", float),
            ("ambient_occlusion", "enabled"): "aoEnabled",
            ("ambient_occlusion", "strength"): ("aoStrength", float),
            ("ambient_occlusion", "radius"): ("aoRadius", float),
        }
        self._apply_nested_mapping(environment, mapping)

        ibl = environment.get("ibl")
        if isinstance(ibl, dict):
            for key, prop in (("source", "iblPrimarySource"), ("fallback", "iblFallbackSource")):
                value = ibl.get(key)
                if isinstance(value, str) and value:
                    resolved = self._resolve_qurl(value)
                    if resolved is not None:
                        self._set_qml_property(prop, resolved)

    def _apply_quality_fallback(self, quality: Dict[str, Any]) -> None:
        mapping = {
            ("shadows", "enabled"): "shadowsEnabled",
            ("shadows", "resolution"): "shadowResolution",
            ("shadows", "filter"): ("shadowFilterSamples", int),
            ("shadows", "bias"): ("shadowBias", float),
            ("shadows", "darkness"): ("shadowFactor", float),
            ("antialiasing", "primary"): "aaPrimaryMode",
            ("antialiasing", "quality"): "aaQualityLevel",
            ("antialiasing", "post"): "aaPostMode",
            ("taa_enabled",): "taaEnabled",
            ("taa_strength",): ("taaStrength", float),
            ("taa_motion_adaptive",): "taaMotionAdaptive",
            ("fxaa_enabled",): "fxaaEnabled",
            ("specular_aa",): "specularAAEnabled",
            ("dithering",): "ditheringEnabled",
            ("render_scale",): ("renderScale", float),
            ("render_policy",): "renderPolicy",
            ("frame_rate_limit",): ("frameRateLimit", float),
            ("oit",): "oitMode",
            ("preset",): "qualityPreset",
        }
        self._apply_nested_mapping(quality, mapping)

    def _apply_camera_fallback(self, camera: Dict[str, Any]) -> None:
        mapping = {
            ("fov",): ("cameraFov", float),
            ("near",): ("cameraNear", float),
            ("far",): ("cameraFar", float),
            ("speed",): ("cameraSpeed", float),
            ("auto_rotate",): "autoRotate",
            ("auto_rotate_speed",): ("autoRotateSpeed", float),
        }
        self._apply_nested_mapping(camera, mapping)

    def _apply_effects_fallback(self, effects: Dict[str, Any]) -> None:
        mapping = {
            ("bloom_enabled",): "bloomEnabled",
            ("bloom_intensity",): ("bloomIntensity", float),
            ("bloom_threshold",): ("bloomThreshold", float),
            ("bloom_spread",): ("bloomSpread", float),
            ("depth_of_field",): "depthOfFieldEnabled",
            ("dof_focus_distance",): ("dofFocusDistance", float),
            ("dof_blur",): ("dofBlurAmount", float),
            ("motion_blur",): "motionBlurEnabled",
            ("motion_blur_amount",): ("motionBlurAmount", float),
            ("lens_flare",): "lensFlareEnabled",
            ("vignette",): "vignetteEnabled",
            ("vignette_strength",): ("vignetteStrength", float),
            ("tonemap_enabled",): "tonemapEnabled",
            ("tonemap_mode",): "tonemapModeName",
        }
        self._apply_nested_mapping(effects, mapping)

    def _apply_materials_fallback(self, materials: Dict[str, Any]) -> None:
        prefix_map = {
            "frame": "frame",
            "lever": "lever",
            "tail": "tailRod",
            "cylinder": "cylinder",
            "piston_body": "pistonBody",
            "piston_rod": "pistonRod",
            "joint_tail": "jointTail",
            "joint_arm": "jointArm",
        }

        suffix_map = {
            "base_color": "BaseColor",
            "metalness": "Metalness",
            "roughness": "Roughness",
            "specular_amount": "SpecularAmount",
            "specular_tint": "SpecularTint",
            "clearcoat": "Clearcoat",
            "clearcoat_roughness": "ClearcoatRoughness",
            "transmission": "Transmission",
            "opacity": "Opacity",
            "ior": "Ior",
            "attenuation_distance": "AttenuationDistance",
            "attenuation_color": "AttenuationColor",
            "emissive_color": "EmissiveColor",
            "emissive_intensity": "EmissiveIntensity",
        }

        for material_key, values in materials.items():
            prefix = prefix_map.get(material_key)
            if not prefix or not isinstance(values, dict):
                continue

            for prop_key, prop_value in values.items():
                if prop_value is None:
                    continue

                if material_key == "piston_body" and prop_key == "warning_color":
                    self._set_qml_property("pistonBodyWarningColor", prop_value)
                    continue
                if material_key == "piston_rod" and prop_key == "warning_color":
                    self._set_qml_property("pistonRodWarningColor", prop_value)
                    continue
                if material_key == "joint_tail":
                    if prop_key == "ok_color":
                        self._set_qml_property("jointRodOkColor", prop_value)
                        continue
                    if prop_key == "error_color":
                        self._set_qml_property("jointRodErrorColor", prop_value)
                        continue

                suffix = suffix_map.get(prop_key)
                if not suffix:
                    continue

                self._set_qml_property(f"{prefix}{suffix}", prop_value)

    def _apply_nested_mapping(self, payload: Dict[str, Any], mapping: Dict[tuple[str, ...], Any]) -> None:
        for path, target in mapping.items():
            cast = None
            if isinstance(target, tuple):
                target, cast = target

            value = self._extract_nested_value(payload, path)
            if value is None:
                continue

            if cast is not None:
                try:
                    value = cast(value)
                except (TypeError, ValueError):
                    continue

            self._set_qml_property(target, value)

    @staticmethod
    def _extract_nested_value(data: Dict[str, Any], path: tuple[str, ...]) -> Any:
        current: Any = data
        for key in path:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current

    def _resolve_qurl(self, value: str) -> Optional[QUrl]:
        if not value:
            return None

        url = QUrl(value)
        if url.isRelative() or not url.isValid() or not url.scheme():
            base = getattr(self, "_qml_base_dir", None)
            if isinstance(base, Path):
                candidate = (base / value).resolve()
                if candidate.exists():
                    return QUrl.fromLocalFile(str(candidate))
        return url

    def _set_qml_property(self, name: str, value: Any) -> None:
        if not name or value is None:
            return
        if self._qml_root_object is None:
            self.logger.debug("Cannot set %s: QML root not ready", name)
            return
        try:
            self._qml_root_object.setProperty(name, value)
        except Exception as exc:
            self.logger.debug("Failed to set %s: %s", name, exc)

    # ------------------------------------------------------------------
    # Обработчики сигналов панелей
    # ------------------------------------------------------------------
    @Slot(dict)
    def _on_geometry_changed_qml(self, geometry: Dict[str, Any]):
        self.logger.info(f"Geometry update received: {list(geometry.keys())}")
        self._queue_qml_update("geometry", geometry)

    @Slot(dict)
    def _on_lighting_changed(self, params: Dict[str, Any]):
        self.logger.debug(f"Lighting update: {params}")
        self._queue_qml_update("lighting", params)

    @Slot(dict)
    def _on_material_changed(self, params: Dict[str, Any]):
        self.logger.debug(f"Material update: {params}")
        self._queue_qml_update("materials", params)

    @Slot(dict)
    def _on_environment_changed(self, params: Dict[str, Any]):
        self.logger.debug(f"Environment update: {params}")
        self._queue_qml_update("environment", params)

    @Slot(dict)
    def _on_quality_changed(self, params: Dict[str, Any]):
        self.logger.debug(f"Quality update: {params}")
        self._queue_qml_update("quality", params)

    @Slot(dict)
    def _on_camera_changed(self, params: Dict[str, Any]):
        self.logger.debug(f"Camera update: {params}")
        self._queue_qml_update("camera", params)

    @Slot(dict)
    def _on_effects_changed(self, params: Dict[str, Any]):
        self.logger.debug(f"Effects update: {params}")
        self._queue_qml_update("effects", params)

    @Slot(str)
    def _on_preset_applied(self, preset_name: str):
        if hasattr(self, "status_bar"):
            self.status_bar.showMessage(f"Пресет '{preset_name}' применён", 2000)

    @Slot(dict)
    def _on_animation_changed(self, params: Dict[str, Any]):
        self.logger.debug(f"Animation update: {params}")
        self._queue_qml_update("animation", params)

    def _on_sim_control(self, command: str):
        bus = self.simulation_manager.state_bus

        if command == "start":
            bus.start_simulation.emit()
            self.is_simulation_running = True
            if self._qml_root_object:
                self._qml_root_object.setProperty("isRunning", True)
        elif command == "stop":
            bus.stop_simulation.emit()
            self.is_simulation_running = False
            if self._qml_root_object:
                self._qml_root_object.setProperty("isRunning", False)
        elif command == "pause":
            bus.pause_simulation.emit()
            self.is_simulation_running = False
            if self._qml_root_object:
                self._qml_root_object.setProperty("isRunning", False)
        elif command == "reset":
            bus.reset_simulation.emit()
            if self._qml_root_object:
                self._qml_root_object.setProperty("animationTime", 0.0)

    def _update_3d_from_snapshot(self, snapshot: StateSnapshot):
        if not self._qml_root_object or not snapshot:
            return

        piston_positions: Dict[str, float] = {}
        for wheel_enum, wheel_state in snapshot.wheels.items():
            corner_key = self.WHEEL_KEY_MAP.get(wheel_enum.value)
            if not corner_key:
                continue
            piston_positions[corner_key] = float(wheel_state.piston_position * 1000.0)

        if piston_positions:
            self._invoke_qml_function("updatePistonPositions", piston_positions)

        self._qml_root_object.setProperty("animationTime", float(snapshot.simulation_time))

    # ------------------------------------------------------------------
    # События окна
    # ------------------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, "_sim_started", False):
            try:
                self.simulation_manager.start()
                self._sim_started = True
            except Exception as exc:
                self.logger.error(f"Failed to start SimulationManager: {exc}")

    def closeEvent(self, event):
        """Сохранение настроек и корректное завершение"""
        self._save_settings()
        try:
            self.simulation_manager.cleanup()
        finally:
            super().closeEvent(event)
