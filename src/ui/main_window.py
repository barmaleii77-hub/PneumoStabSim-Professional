"""
Main window for PneumoStabSim application
Qt Quick 3D rendering with QQuickWidget (no createWindowContainer)
РУССКИЙ ИНТЕРФЕЙС (Russian UI)
"""
from PySide6.QtWidgets import (
    QMainWindow, QStatusBar, QDockWidget, QWidget, QMenuBar, QToolBar, QLabel,
    QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QApplication, QSplitter,
    QTabWidget, QScrollArea  # NEW: For tabs and scrolling
)
from PySide6.QtCore import Qt, QTimer, Slot, QSettings, QUrl, QFileInfo
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtQuickWidgets import QQuickWidget
import logging
import json
import numpy as np
from pathlib import Path
from typing import Optional, Dict

from .charts import ChartWidget
from .panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel
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
    SETTINGS_SPLITTER = "MainWindow/Splitter"  # NEW: Save splitter position
    SETTINGS_LAST_TAB = "MainWindow/LastTab"    # NEW: Save selected tab
    SETTINGS_LAST_PRESET = "Presets/LastPath"

    def __init__(self, use_qml_3d: bool = True):
        super().__init__()
        
        # Store visualization backend choice
        self.use_qml_3d = use_qml_3d
        
        backend_name = "Qt Quick 3D (U-Рама PBR)" if use_qml_3d else "Legacy OpenGL"
        self.setWindowTitle(f"PneumoStabSim - {backend_name}")  # Русское название
        
        # Set reasonable initial size
        self.resize(1400, 900)  # Increased for better layout
        
        # Set minimum window size
        self.setMinimumSize(1200, 800)
        
        # Ensure window is in normal state
        self.setWindowState(Qt.WindowState.WindowNoState)

        # Logging
        self.logger = logging.getLogger(__name__)
        
        print("MainWindow: Создание SimulationManager...")
        
        # Simulation manager
        try:
            self.simulation_manager = SimulationManager(self)
            self._sim_started = False
            print("✅ SimulationManager создан (не запущен)");
        except Exception as e:
            print(f"❌ Ошибка создания SimulationManager: {e}")
            import traceback
            traceback.print_exc();
            raise;

        # Current snapshot
        self.current_snapshot: Optional[StateSnapshot] = None
        self.is_simulation_running = False

        # Geometry converter for Python↔QML integration
        from .geometry_bridge import create_geometry_converter
        self.geometry_converter = create_geometry_converter()
        print("✅ GeometryBridge создан для интеграции Python↔QML")

        # Panels references
        self.geometry_panel: Optional[GeometryPanel] = None
        self.pneumo_panel: Optional[PneumoPanel] = None
        self.modes_panel: Optional[ModesPanel] = None
        self.road_panel: Optional[RoadPanel] = None
        self.chart_widget: Optional[ChartWidget] = None
        
        # NEW: Tab widget and splitter
        self.tab_widget: Optional[QTabWidget] = None
        self.main_splitter: Optional[QSplitter] = None

        # Qt Quick 3D view reference
        self._qquick_widget: Optional[QQuickWidget] = None
        self._qml_root_object = None

        print("MainWindow: Построение UI...")
        
        # Build UI (NEW ORDER!)
        self._setup_central()
        print("  ✅ Центральный вид Qt Quick 3D настроен")
        
        self._setup_tabs()  # NEW: Setup tabs instead of docks!
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
    # UI Construction - НОВАЯ СТРУКТУРА!
    # ------------------------------------------------------------------
    def _setup_central(self):
        """Создать центральный вид с вертикальным сплиттером
        
        Create central view with vertical splitter:
          - Top: 3D scene (QQuickWidget)
          - Bottom: Charts (full width)
        """
        print("    _setup_central: Создание вертикального сплиттера...")
        
        # Create vertical splitter
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setObjectName("MainSplitter")
        
        # Top section: 3D scene
        if self.use_qml_3d:
            self._setup_qml_3d_view()
        else:
            self._setup_legacy_opengl_view()
        
        if self._qquick_widget:
            self.main_splitter.addWidget(self._qquick_widget)
        
        # Bottom section: Charts (full width!)
        self.chart_widget = ChartWidget(self)
        self.chart_widget.setMinimumHeight(200)  # Minimum chart height
        self.main_splitter.addWidget(self.chart_widget)
        
        # Set stretch factors (3D scene gets more space)
        self.main_splitter.setStretchFactor(0, 3)  # 60% for 3D
        self.main_splitter.setStretchFactor(1, 2)  # 40% for charts
        
        # Create container with horizontal layout: splitter + tabs
        central_container = QWidget()
        central_layout = QHBoxLayout(central_container)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        
        # Add splitter to container (will add tabs later)
        central_layout.addWidget(self.main_splitter, stretch=3)  # 75% width
        
        self.setCentralWidget(central_container)
        
        print("    ✅ Вертикальный сплиттер создан (сцена сверху, графики снизу)")

    def _setup_qml_3d_view(self):
        """Setup Qt Quick 3D full suspension scene"""
        print("    [QML] Загрузка main.qml...")
        
        try:
            self._qquick_widget = QQuickWidget(self)
            self._qquick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
            
            qml_path = Path("assets/qml/main.qml")
            if not qml_path.exists():
                raise FileNotFoundError(f"QML файл не найден: {qml_path.absolute()}")
            
            qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
            print(f"    Загрузка main.qml: {qml_url.toString()}")
            
            self._qquick_widget.setSource(qml_url)
            
            if self._qquick_widget.status() == QQuickWidget.Status.Error:
                errors = self._qquick_widget.errors()
                error_msg = "\n".join(str(e) for e in errors)
                raise RuntimeError(f"Ошибки QML:\n{error_msg}")
            
            self._qml_root_object = self._qquick_widget.rootObject()
            if not self._qml_root_object:
                raise RuntimeError("Не удалось получить корневой объект QML")
            
            print("    [OK] main.qml загружен успешно")
            
        except Exception as e:
            print(f"    [ERROR] Ошибка загрузки main.qml: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback
            fallback = QLabel(
                "Ошибка загрузки 3D сцены\n\n"
                "Проверьте консоль для деталей."
            )
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setStyleSheet("background: #1a1a2e; color: #ff6b6b; font-size: 14px; padding: 20px;")
            self._qquick_widget = fallback
            print("    [WARNING] Использован запасной виджет")

    def _setup_legacy_opengl_view(self):
        """Setup legacy OpenGL widget"""
        print("    _setup_legacy_opengl_view: Загрузка legacy QML...")
        self._setup_qml_3d_view()  # Same implementation for now

    def _setup_tabs(self):
        """Создать вкладки с панелями параметров (справа от сцены)
        
        Create tabbed panels on the right side:
          - Геометрия (Geometry)
          - Пневмосистема (Pneumatics)
          - Режимы стабилизатора (Modes)
          - Визуализация (Visualization - stub)
          - Динамика движения (Road/Dynamics - stub)
        """
        print("    _setup_tabs: Создание вкладок...")
        
        # Create tab widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setObjectName("ParameterTabs")
        self.tab_widget.setMinimumWidth(350)
        self.tab_widget.setMaximumWidth(500)
        
        # Tab 1: Геометрия (Geometry)
        self.geometry_panel = GeometryPanel(self)
        scroll_geometry = QScrollArea()
        scroll_geometry.setWidgetResizable(True)
        scroll_geometry.setWidget(self.geometry_panel)
        scroll_geometry.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tab_widget.addTab(scroll_geometry, "Геометрия")
        print("      ✅ Вкладка 'Геометрия' создана")
        
        # Tab 2: Пневмосистема (Pneumatics)
        self.pneumo_panel = PneumoPanel(self)
        scroll_pneumo = QScrollArea()
        scroll_pneumo.setWidgetResizable(True)
        scroll_pneumo.setWidget(self.pneumo_panel)
        scroll_pneumo.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tab_widget.addTab(scroll_pneumo, "Пневмосистема")
        print("      ✅ Вкладка 'Пневмосистема' создана")
        
        # Tab 3: Режимы стабилизатора (Modes)
        self.modes_panel = ModesPanel(self)
        scroll_modes = QScrollArea()
        scroll_modes.setWidgetResizable(True)
        scroll_modes.setWidget(self.modes_panel)
        scroll_modes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tab_widget.addTab(scroll_modes, "Режимы стабилизатора")
        print("      ✅ Вкладка 'Режимы стабилизатора' создана")
        
        # Tab 4: Визуализация (Visualization - stub for now)
        viz_stub = QWidget()
        viz_layout = QVBoxLayout(viz_stub)
        viz_label = QLabel("Панель визуализации\n\n(В разработке)")
        viz_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        viz_label.setStyleSheet("color: #888; font-size: 12px; padding: 20px;")
        viz_layout.addWidget(viz_label)
        viz_layout.addStretch()
        self.tab_widget.addTab(viz_stub, "Визуализация")
        print("      ✅ Вкладка 'Визуализация' создана (заглушка)")
        
        # Tab 5: Динамика движения (Road/Dynamics - stub, NO CSV loading!)
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
        
        # Add tab widget to central container layout
        central_widget = self.centralWidget()
        if central_widget:
            layout = central_widget.layout()
            if layout:
                layout.addWidget(self.tab_widget, stretch=1)  # 25% width
        
        # Connect panel signals
        self._wire_panel_signals()
        
        # Restore last selected tab
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        last_tab = settings.value(self.SETTINGS_LAST_TAB, 0, type=int)
        if 0 <= last_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(last_tab)
        
        # Save selected tab on change
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        print("    ✅ Вкладки созданы и подключены")

    @Slot(int)
    def _on_tab_changed(self, index: int):
        """Сохранить выбранную вкладку / Save selected tab"""
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        settings.setValue(self.SETTINGS_LAST_TAB, index)
        
        tab_names = [
            "Геометрия", "Пневмосистема", "Режимы стабилизатора",
            "Визуализация", "Динамика движения"
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
            self.geometry_panel.geometry_changed.connect(self._on_geometry_changed)
            print("✅ Сигналы GeometryPanel подключены")

        # Pneumatic panel
        if self.pneumo_panel:
            self.pneumo_panel.mode_changed.connect(self._on_mode_changed)
            self.pneumo_panel.parameter_changed.connect(self._on_pneumo_param)
            print("✅ Сигналы PneumoPanel подключены")

        # Modes panel
        if self.modes_panel:
            self.modes_panel.simulation_control.connect(self._on_sim_control)
            self.modes_panel.mode_changed.connect(self._on_mode_changed)
            self.modes_panel.parameter_changed.connect(
                lambda n, v: self.logger.debug(f"Параметр {n}={v}"))
            self.modes_panel.animation_changed.connect(self._on_animation_changed)
            print("✅ Сигналы ModesPanel подключены")

    # ------------------------------------------------------------------
    # Menus & Toolbars - РУССКИЙ ИНТЕРФЕЙС
    # ------------------------------------------------------------------
    def _setup_menus(self):
        """Настроить меню (русский интерфейс) / Setup menus (Russian UI)"""
        menubar = self.menuBar()

        # Файл (File menu)
        file_menu = menubar.addMenu("Файл")
        
        # Preset actions
        save_preset_act = QAction("Сохранить пресет...", self)
        load_preset_act = QAction("Загрузить пресет...", self)
        save_preset_act.triggered.connect(self._save_preset)
        load_preset_act.triggered.connect(self._load_preset)
        file_menu.addAction(save_preset_act)
        file_menu.addAction(load_preset_act)
        file_menu.addSeparator()
        
        # Export submenu
        export_menu = file_menu.addMenu("Экспорт")
        export_timeseries_act = QAction("Экспорт временных рядов...", self)
        export_snapshots_act = QAction("Экспорт снимков состояния...", self)
        export_timeseries_act.triggered.connect(self._export_timeseries)
        export_snapshots_act.triggered.connect(self._export_snapshots)
        export_menu.addAction(export_timeseries_act)
        export_menu.addAction(export_snapshots_act)
        file_menu.addSeparator()
        
        # Exit
        exit_act = QAction("Выход", self)
        exit_act.setShortcut(QKeySequence.StandardKey.Quit)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # Параметры (Parameters menu)
        params_menu = menubar.addMenu("Параметры")
        reset_ui_act = QAction("Сбросить раскладку UI", self)
        reset_ui_act.triggered.connect(self._reset_ui_layout)
        params_menu.addAction(reset_ui_act)

        # Вид (View menu)
        view_menu = menubar.addMenu("Вид")
        
        # Toggle tabs visibility
        toggle_tabs_act = QAction("Показать/скрыть панели", self, checkable=True, checked=True)
        toggle_tabs_act.toggled.connect(self._toggle_tabs_visibility)
        view_menu.addAction(toggle_tabs_act)
        
        view_menu.addSeparator()
        
        # Toggle charts visibility
        toggle_charts_act = QAction("Показать/скрыть графики", self, checkable=True, checked=True)
        toggle_charts_act.toggled.connect(self._toggle_charts_visibility)
        view_menu.addAction(toggle_charts_act)

    def _toggle_tabs_visibility(self, visible: bool):
        """Переключить видимость вкладок / Toggle tabs visibility"""
        if self.tab_widget:
            self.tab_widget.setVisible(visible)
        status_msg = "Панели показаны" if visible else "Панели скрыты"
        if hasattr(self, 'status_bar'):
            self.status_bar.showMessage(status_msg)
    
    def _toggle_charts_visibility(self, visible: bool):
        """Переключить видимость графиков / Toggle charts visibility"""
        if self.chart_widget:
            self.chart_widget.setVisible(visible)
        status_msg = "Графики показаны" if visible else "Графики скрыты"
        if hasattr(self, 'status_bar'):
            self.status_bar.showMessage(status_msg)

    def _setup_toolbar(self):
        """Настроить панель инструментов (русский) / Setup toolbar (Russian)"""
        toolbar = self.addToolBar("Главная")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(True)
        
        start_act = QAction("▶ Старт", self)
        stop_act = QAction("⏹ Стоп", self)
        pause_act = QAction("⏸ Пауза", self)
        reset_act = QAction("🔄 Сброс", self)
        
        start_act.setToolTip("Запустить симуляцию")
        stop_act.setToolTip("Остановить симуляцию")
        pause_act.setToolTip("Приостановить симуляцию")
        reset_act.setToolTip("Сбросить симуляцию")
        
        start_act.triggered.connect(lambda: self._on_sim_control("start"))
        stop_act.triggered.connect(lambda: self._on_sim_control("stop"))
        pause_act.triggered.connect(lambda: self._on_sim_control("pause"))
        reset_act.triggered.connect(lambda: self._on_sim_control("reset"))
        
        toolbar.addActions([start_act, stop_act, pause_act, reset_act])
        toolbar.setMaximumHeight(50)

    def _setup_status_bar(self):
        """Настроить строку состояния (русский) / Setup status bar (Russian)"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create status bar widgets with Russian labels
        self.sim_time_label = QLabel("Время: 0.000с")
        self.sim_time_label.setMinimumWidth(120)
        self.sim_time_label.setToolTip("Время симуляции")
        
        self.step_count_label = QLabel("Шаги: 0")
        self.step_count_label.setMinimumWidth(80)
        self.step_count_label.setToolTip("Количество шагов")
        
        self.fps_label = QLabel("FPS физики: 0")
        self.fps_label.setMinimumWidth(100)
        self.fps_label.setToolTip("Частота кадров физики")
        
        self.realtime_label = QLabel("РВ: 1.00x")
        self.realtime_label.setMinimumWidth(80)
        self.realtime_label.setToolTip("Реальное время")
        
        self.queue_label = QLabel("Очередь: 0/0")
        self.queue_label.setMinimumWidth(100)
        self.queue_label.setToolTip("Очередь обновлений")
        
        # Kinematics display (Russian units)
        self.kinematics_label = QLabel("угол: 0.0° | ход: 0.0мм | V_б: 0см³ | V_ш: 0см³")
        self.kinematics_label.setToolTip("Угол рычага, ход цилиндра, объёмы камер (безштоковая/штоковая)")
        self.kinematics_label.setMinimumWidth(350)
        
        for w in [self.sim_time_label, self.step_count_label, self.fps_label, 
                  self.queue_label, self.realtime_label, self.kinematics_label]:
            self.status_bar.addPermanentWidget(w)
        
        self.status_bar.showMessage("Готов")
        self.status_bar.setMaximumHeight(30)

    # ------------------------------------------------------------------
    # Simulation Control & State Updates - РУССКИЙ ТЕКСТ
    # ------------------------------------------------------------------
    @Slot(object)
    def _on_state_update(self, snapshot: StateSnapshot):
        """Обновить состояние из симуляции / Update state from simulation"""
        self.current_snapshot = snapshot
        if snapshot:
            # Update status bar with Russian labels
            self.sim_time_label.setText(f"Время: {snapshot.simulation_time:.3f}с")
            self.step_count_label.setText(f"Шаги: {snapshot.step_number}")
            
            if snapshot.aggregates.physics_step_time > 0:
                fps = 1.0 / snapshot.aggregates.physics_step_time
                self.fps_label.setText(f"FPS физики: {fps:.1f}")
            
            # Update 3D scene
            self._update_3d_scene_from_snapshot(snapshot)
            
        # Update charts
        if self.chart_widget:
            self.chart_widget.update_from_snapshot(snapshot)

    @Slot(str)
    def _on_physics_error(self, msg: str):
        """Обработать ошибку физики / Handle physics error"""
        self.status_bar.showMessage(f"Ошибка физики: {msg}")
        self.logger.error(f"Ошибка физического движка: {msg}")
        
        if "CRITICAL" in msg.upper() or "FATAL" in msg.upper():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Ошибка физического движка",
                f"Критическая ошибка в физической симуляции:\n\n{msg}\n\n"
                "Симуляция может быть нестабильной. Рекомендуется сброс."
            )

    def _on_sim_control(self, command: str):
        """Управление симуляцией / Simulation control"""
        bus = self.simulation_manager.state_bus
        
        status_messages = {
            "start": ("Симуляция запущена", True, True),
            "stop": ("Симуляция остановлена", False, False),
            "reset": ("Симуляция сброшена", False, None),
            "pause": ("Симуляция приостановлена", False, False)
        }
        
        msg, is_running, qml_running = status_messages.get(command, ("", False, None))
        
        if command == "start":
            bus.start_simulation.emit()
        elif command == "stop":
            bus.stop_simulation.emit()
        elif command == "reset":
            bus.reset_simulation.emit()
        elif command == "pause":
            bus.pause_simulation.emit()
        
        self.is_simulation_running = is_running
        
        # Update QML animation state
        if qml_running is not None and self._qml_root_object:
            self._qml_root_object.setProperty("isRunning", qml_running)
            if command == "reset":
                self._qml_root_object.setProperty("animationTime", 0.0)
        
        self.status_bar.showMessage(msg)
        
        if self.modes_panel:
            self.modes_panel.set_simulation_running(self.is_simulation_running)

    def _on_mode_changed(self, mode_type: str, new_mode: str):
        """Изменение режима / Mode change"""
        bus = self.simulation_manager.state_bus
        if mode_type == 'thermo_mode':
            bus.set_thermo_mode.emit(new_mode)
            self.logger.info(f"Термо-режим изменён: {new_mode}")
        elif mode_type == 'sim_type':
            self.logger.info(f"Тип симуляции: {new_mode}")
        else:
            self.logger.info(f"Режим изменён {mode_type} → {new_mode}")

    def _on_pneumo_param(self, name: str, value: float):
        """Параметр пневмосистемы изменён / Pneumatic parameter changed"""
        if name == 'master_isolation_open':
            self.simulation_manager.state_bus.set_master_isolation.emit(bool(value))
            self.logger.info(f"Главная изоляция: {bool(value)}")

    @Slot(dict)
    def _on_geometry_changed(self, geometry_params: dict):
        """Handle geometry changes from GeometryPanel
        
        Args:
            geometry_params: Dictionary with updated geometry parameters
        """
        self.logger.info(f"Geometry changed: {list(geometry_params.keys())}")
        
        # Update the 3D scene through QML
        if self._qml_root_object:
            try:
                # Call updateGeometry method in QML if it exists
                if hasattr(self._qml_root_object, 'updateGeometry'):
                    self._qml_root_object.updateGeometry(geometry_params)
                else:
                    # Set individual properties
                    for key, value in geometry_params.items():
                        self._qml_root_object.setProperty(key, value)
                
                print(f"📤 MainWindow: Updated QML with geometry: {geometry_params}")
            except Exception as e:
                self.logger.warning(f"Failed to update QML geometry: {e}")
        
        # Update the simulation manager if needed
        bus = self.simulation_manager.state_bus
        if 'wheelbase' in geometry_params:
            bus.set_geometry.emit(geometry_params)
    
    @Slot(dict) 
    def _on_animation_changed(self, animation_params: dict):
        """Handle animation parameter changes from ModesPanel
        
        Args:
            animation_params: Dictionary with animation parameters (amplitude, frequency, phase, etc.)
        """
        self.logger.info(f"Animation changed: {animation_params}")
        
        # Update QML animation properties
        if self._qml_root_object:
            try:
                for key, value in animation_params.items():
                    qml_property = f"user{key.capitalize()}"  # e.g., userAmplitude, userFrequency
                    self._qml_root_object.setProperty(qml_property, value)
                
                print(f"🎬 MainWindow: Updated QML animation: {animation_params}")
            except Exception as e:
                self.logger.warning(f"Failed to update QML animation: {e}")
        
        # Update status bar if needed
        if 'amplitude' in animation_params and 'frequency' in animation_params:
            amp_mm = animation_params['amplitude'] * 1000  # Convert to mm
            freq = animation_params['frequency']
            self.status_bar.showMessage(f"Анимация: A={amp_mm:.1f}мм F={freq:.1f}Hz")
    
    # ------------------------------------------------------------------
    # 3D Scene Updates
    # ------------------------------------------------------------------