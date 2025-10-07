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
    SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"  # NEW: Save horizontal splitter position
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
        
        # NEW: Tab widget and splitters
        self.tab_widget: Optional[QTabWidget] = None
        self.main_splitter: Optional[QSplitter] = None  # Vertical splitter (scene + charts)
        self.main_horizontal_splitter: Optional[QSplitter] = None  # Horizontal splitter (main layout)

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
        """Создать вкладки с панелями параметров (справа от сцены через сплиттер)
        
        Create tabbed panels on the right side with resizable splitter:
          - Геометрия (Geometry)
          - Пневмосистема (Pneumatics)
          - Режимы стабилизатора (Modes)
          - Визуализация (Visualization - stub)
          - Динамика движения (Road/Dynamics - stub)
        """
        print("    _setup_tabs: Создание вкладок с ресайзбаром...")
        
        # Create tab widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setObjectName("ParameterTabs")
        self.tab_widget.setMinimumWidth(300)  # Reduced minimum width
        self.tab_widget.setMaximumWidth(600)  # Increased maximum width for resizing
        
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
            # ИСПРАВЛЕНО: Подключаем РЕАЛЬНУЮ функцию обновления QML вместо заглушки
            self.geometry_panel.geometry_changed.connect(self._on_geometry_changed_real)
            print("✅ Сигналы GeometryPanel подключены (РЕАЛЬНОЕ ОБНОВЛЕНИЕ QML)")

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

    def _setup_menus(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
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
        export_snapshots_act = QAction("Экспорт снимков...", self)
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

        # Parameters menu
        params_menu = menubar.addMenu("Параметры")
        reset_ui_act = QAction("Сбросить раскладку UI", self)
        reset_ui_act.triggered.connect(self._reset_ui_layout)
        params_menu.addAction(reset_ui_act)

        # View menu
        view_menu = menubar.addMenu("Вид")
        if self.tab_widget:
            toggle_tabs_act = QAction("Показать/скрыть панели", self)
            toggle_tabs_act.setCheckable(True)
            toggle_tabs_act.setChecked(True)
            toggle_tabs_act.toggled.connect(self._toggle_tabs)
            view_menu.addAction(toggle_tabs_act)

    def _toggle_tabs(self, visible: bool):
        """Toggle visibility of tab widget"""
        if self.tab_widget:
            self.tab_widget.setVisible(visible)

    def _setup_toolbar(self):
        """Create toolbar"""
        toolbar = self.addToolBar("Основная")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(True)
        
        start_act = QAction("Пуск", self)
        stop_act = QAction("Стоп", self)
        pause_act = QAction("Пауза", self)
        reset_act = QAction("Сброс", self)
        
        start_act.triggered.connect(lambda: self._on_sim_control("start"))
        stop_act.triggered.connect(lambda: self._on_sim_control("stop"))
        pause_act.triggered.connect(lambda: self._on_sim_control("pause"))
        reset_act.triggered.connect(lambda: self._on_sim_control("reset"))
        
        toolbar.addActions([start_act, stop_act, pause_act, reset_act])
        toolbar.setMaximumHeight(50)

    def _setup_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create status bar widgets
        self.sim_time_label = QLabel("Время симуляции: 0.000с")
        self.sim_time_label.setMinimumWidth(180)
        
        self.step_count_label = QLabel("Шагов: 0")
        self.step_count_label.setMinimumWidth(80)
        
        self.fps_label = QLabel("FPS: 0")
        self.fps_label.setMinimumWidth(80)
        
        for w in [self.sim_time_label, self.step_count_label, self.fps_label]:
            self.status_bar.addPermanentWidget(w)
        
        self.status_bar.showMessage("Готов")
        self.status_bar.setMaximumHeight(30)

    def _connect_simulation_signals(self):
        """Connect simulation signals to UI"""
        try:
            bus = self.simulation_manager.state_bus
            bus.state_ready.connect(self._on_state_update, Qt.QueuedConnection)
            bus.physics_error.connect(self._on_physics_error, Qt.QueuedConnection)
        except Exception as e:
            self.logger.error(f"Ошибка подключения сигналов: {e}")

    @Slot(object)
    def _on_state_update(self, snapshot):
        """Handle state update from simulation"""
        self.current_snapshot = snapshot
        # TODO: Update charts and UI elements

    @Slot(str)
    def _on_physics_error(self, msg: str):
        """Handle physics error"""
        self.logger.error(f"Physics error: {msg}")

    @Slot()
    def _update_render(self):
        """Update rendering (called by timer)"""
        # Simple update - just process events
        if self.current_snapshot and hasattr(self, 'sim_time_label'):
            self.sim_time_label.setText(f"Время симуляции: {self.current_snapshot.simulation_time:.3f}с")
            self.step_count_label.setText(f"Шагов: {self.current_snapshot.step_number}")
            
            if self.current_snapshot.aggregates.physics_step_time > 0:
                fps = 1.0 / self.current_snapshot.aggregates.physics_step_time
                self.fps_label.setText(f"FPS: {fps:.0f}")

        # Update QML scene if needed
        if self._qml_root_object and self.is_simulation_running:
            import time
            current_time = time.time()
            # Simple animation for testing
            if not hasattr(self, '_start_time'):
                self._start_time = current_time
            elapsed = current_time - self._start_time
            
            # Simple sine wave animation
            import math
            angle = math.sin(elapsed * 2) * 10  # 10 degree amplitude
            
            # Set angles for all corners
            for corner in ['fl', 'fr', 'rl', 'rr']:
                prop_name = f"{corner}_angle"
                try:
                    self._qml_root_object.setProperty(prop_name, angle)
                except:
                    pass

    # ------------------------------------------------------------------
    # Preset Save/Load & Settings - РУССКИЙ ИНТЕРФЕЙС
    # ------------------------------------------------------------------
    def _save_preset(self):
        """Сохранить пресет UI / Save UI preset"""
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        last_dir = settings.value(self.SETTINGS_LAST_PRESET, str(Path.cwd()))
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить пресет UI", last_dir, "JSON файлы (*.json)"
        )
        if not file_path:
            return
        
        settings.setValue(self.SETTINGS_LAST_PRESET, str(Path(file_path).parent))
        
        preset = {
            'geometry': self.geometry_panel.get_parameters() if self.geometry_panel else {},
            'pneumo': self.pneumo_panel.get_parameters() if self.pneumo_panel else {},
            'modes': self.modes_panel.get_parameters() if self.modes_panel else {},
            'physics': self.modes_panel.get_physics_options() if self.modes_panel else {}
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(preset, f, indent=2, ensure_ascii=False)
            self.status_bar.showMessage(f"Пресет сохранён: {Path(file_path).name}")
            self.logger.info(f"Пресет сохранён: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения пресета", str(e))

    def _load_preset(self):
        """Загрузить пресет UI / Load UI preset"""
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        last_dir = settings.value(self.SETTINGS_LAST_PRESET, str(Path.cwd()))
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить пресет UI", last_dir, "JSON файлы (*.json)"
        )
        if not file_path:
            return
        
        settings.setValue(self.SETTINGS_LAST_PRESET, str(Path(file_path).parent))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                preset = json.load(f)
            
            if self.geometry_panel and 'geometry' in preset:
                self.geometry_panel.set_parameters(preset['geometry'])
            if self.pneumo_panel and 'pneumo' in preset:
                self.pneumo_panel.set_parameters(preset['pneumo'])
            if self.modes_panel and 'modes' in preset:
                for k, v in preset['modes'].items():
                    self.logger.info(f"Загружен параметр режима {k}={v}")
            
            self.status_bar.showMessage(f"Пресет загружен: {Path(file_path).name}")
            self.logger.info(f"Пресет загружен: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка загрузки пресета", str(e))

    def _reset_ui_layout(self):
        """Сбросить раскладку UI / Reset UI layout"""
        # Show all tabs
        if self.tab_widget:
            self.tab_widget.setVisible(True)
        
        # Show charts
        if self.chart_widget:
            self.chart_widget.setVisible(True)
        
        # Reset vertical splitter to default (60/40)
        if self.main_splitter:
            total_height = self.main_splitter.height()
            self.main_splitter.setSizes([int(total_height * 0.6), int(total_height * 0.4)])
        
        # Reset horizontal splitter to default (75/25)
        if self.main_horizontal_splitter:
            total_width = self.main_horizontal_splitter.width()
            self.main_horizontal_splitter.setSizes([int(total_width * 0.75), int(total_width * 0.25)])
        
        # Reset to first tab
        if self.tab_widget:
            self.tab_widget.setCurrentIndex(0)
        
        self.status_bar.showMessage("Раскладка UI сброшена")
        self.logger.info("Раскладка UI сброшена к значениям по умолчанию")

    def _restore_settings(self):
        """Восстановить настройки из QSettings / Restore settings from QSettings"""
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        
        # Restore geometry (commented out to avoid crashes)
        # if geo := settings.value(self.SETTINGS_GEOMETRY):
        #     self.restoreGeometry(geo)
        
        # Restore vertical splitter position
        if self.main_splitter and (splitter_state := settings.value(self.SETTINGS_SPLITTER)):
            try:
                self.main_splitter.restoreState(splitter_state)
                self.logger.debug("Позиция вертикального сплиттера восстановлена")
            except Exception as e:
                self.logger.warning(f"Не удалось восстановить позицию вертикального сплиттера: {e}")
        
        # Restore horizontal splitter position
        if self.main_horizontal_splitter and (h_splitter_state := settings.value(self.SETTINGS_HORIZONTAL_SPLITTER)):
            try:
                self.main_horizontal_splitter.restoreState(h_splitter_state)
                self.logger.debug("Позиция горизонтального сплиттера восстановлена")
            except Exception as e:
                self.logger.warning(f"Не удалось восстановить позицию горизонтального сплиттера: {e}")

    def _save_settings(self):
        """Сохранить настройки в QSettings / Save settings to QSettings"""
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        
        # Save geometry
        settings.setValue(self.SETTINGS_GEOMETRY, self.saveGeometry())
        
        # Save vertical splitter position
        if self.main_splitter:
            settings.setValue(self.SETTINGS_SPLITTER, self.main_splitter.saveState())
        
        # Save horizontal splitter position
        if self.main_horizontal_splitter:
            settings.setValue(self.SETTINGS_HORIZONTAL_SPLITTER, self.main_horizontal_splitter.saveState())
        
        self.logger.debug("Настройки UI saved")

    # ------------------------------------------------------------------
    # CSV Export (P11) - РУССКИЙ ИНТЕРФЕЙС
    # ------------------------------------------------------------------
    def _export_timeseries(self):
        """Экспорт временных рядов в CSV / Export timeseries to CSV"""
        from PySide6.QtCore import QStandardPaths
        from ..common import export_timeseries_csv, get_default_export_dir, ensure_csv_extension, log_export
        
        if not self.chart_widget:
            QMessageBox.warning(self, "Экспорт", "Нет данных графиков для экспорта")
            return
        
        try:
            time, series = self.chart_widget.get_series_buffers()
            if len(time) == 0:
                QMessageBox.warning(self, "Экспорт", "Нет данных для экспорта")
                return
        except AttributeError:
            QMessageBox.warning(self, "Экспорт", "Виджет графиков не поддерживает экспорт")
            return
        
        default_dir = str(get_default_export_dir())
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Экспорт временных рядов в CSV",
            f"{default_dir}/PneumoStabSim_timeseries.csv",
            "CSV файлы (*.csv);;Сжатые CSV (*.csv.gz)"
        )
        
        if not file_path:
            return
        
        file_path = ensure_csv_extension(Path(file_path), allow_gz=True)
        header = ['time'] + list(series.keys())
        
        try:
            export_timeseries_csv(time, series, file_path, header)
            log_export("TIMESERIES", file_path, len(time))
            self.status_bar.showMessage(f"Экспортировано {len(time)} точек в {file_path.name}")
            QMessageBox.information(
                self,
                "Экспорт завершён",
                f"Экспортировано {len(time)} точек данных в:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", str(e))
            self.logger.error(f"Ошибка экспорта временных рядов: {e}")
    
    def _export_snapshots(self):
        """Экспорт снимков состояния в CSV / Export state snapshots to CSV"""
        from PySide6.QtCore import QStandardPaths
        from ..common import export_state_snapshot_csv, get_default_export_dir, ensure_csv_extension, log_export
        
        try:
            snapshots = self.simulation_manager.get_snapshot_buffer()
            if not snapshots or len(snapshots) == 0:
                QMessageBox.warning(self, "Экспорт", "Нет снимков для экспорта")
                return
        except AttributeError:
            QMessageBox.warning(self, "Экспорт", "Буфер снимков не реализован")
            return
        
        default_dir = str(get_default_export_dir())
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Экспорт снимков состояния в CSV",
            f"{default_dir}/PneumoStabSim_snapshots.csv",
            "CSV файлы (*.csv);;Сжатые CSV (*.csv.gz)"
        )
        
        if not file_path:
            return
        
        file_path = ensure_csv_extension(Path(file_path), allow_gz=True)
        
        try:
            export_state_snapshot_csv(snapshots, file_path)
            log_export("SNAPSHOTS", file_path, len(snapshots))
            self.status_bar.showMessage(f"Экспортировано {len(snapshots)} снимков в {file_path.name}")
            QMessageBox.information(
                self,
                "Экспорт завершён",
                f"Экспортировано {len(snapshots)} снимков в:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка экспорта", str(e))
            self.logger.error(f"Ошибка экспорта снимков: {e}")

    @Slot(dict)
    def _on_geometry_changed_real(self, geometry_params: dict):
        """РЕАЛЬНАЯ функция обновления геометрии в QML сцене
        
        Args:
            geometry_params: Dictionary with geometry parameters from UI
        """
        print(f"═══════════════════════════════════════════════")
        print(f"🔧 MainWindow: РЕАЛЬНОЕ обновление QML геометрии!")
        print(f"   Получено параметров: {len(geometry_params)}")
        for key, val in geometry_params.items():
            if 'Length' in key or 'Diam' in key or 'Position' in key:
                print(f"      🎯 {key}: {val}")
        print(f"═══════════════════════════════════════════════")
        
        self.logger.info(f"Geometry changed: {geometry_params}")
        
        # Обновляем QML сцену если доступна
        if self._qml_root_object:
            try:
                print(f"🔧 Вызываем QML updateGeometry()...")
                
                # Используем QMetaObject.invokeMethod() для вызова updateGeometry в QML
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt
                
                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "updateGeometry",
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", geometry_params)
                )
                
                if success:
                    print(f"✅ QML updateGeometry() вызван успешно!")
                    self.status_bar.showMessage("Геометрия обновлена в 3D сцене")
                    print(f"📊 Статус: Геометрия успешно передана в QML")
                else:
                    print(f"❌ QML updateGeometry() НЕ СРАБОТАЛ!")
                    # Fallback - устанавливаем свойства напрямую
                    self._update_qml_properties_fallback(geometry_params)
                    
            except Exception as e:
                print(f"═══════════════════════════════════════════════")
                print(f"❌ ОШИБКА обновления QML геометрии!")
                print(f"   Error: {e}")
                print(f"═══════════════════════════════════════════════")
                self.logger.error(f"QML geometry update failed: {e}")
                import traceback
                traceback.print_exc()
                
                # Fallback - устанавлием свойства напрямую
                self._update_qml_properties_fallback(geometry_params)
        else:
            print(f"═══════════════════════════════════════════════")
            print(f"❌ MainWindow: QML root object отсутствует!")
            print(f"   Не можем обновить геометрию")
            print(f"═══════════════════════════════════════════════")

    def _update_qml_properties_fallback(self, geometry_params: dict):
        """Fallback: устанавливаем QML свойства напрямую если updateGeometry не работает
        
        Args:
            geometry_params: Dictionary with geometry parameters
        """
        print(f"🔄 Fallback: установка QML свойств напрямую...")
        
        # Соответствие параметров Python -> QML свойства
        param_mapping = {
            'frameLength': 'userFrameLength',
            'frameHeight': 'userFrameHeight', 
            'frameBeamSize': 'userBeamSize',
            'leverLength': 'userLeverLength',
            'cylinderBodyLength': 'userCylinderLength',
            'trackWidth': 'userTrackWidth',
            'frameToPivot': 'userFrameToPivot',
            'rodPosition': 'userRodPosition',
            'boreHead': 'userBoreHead',
            'boreRod': 'userBoreRod',
            'rodDiameter': 'userRodDiameter',
            'pistonThickness': 'userPistonThickness',
            'pistonRodLength': 'userPistonRodLength'
        }
        
        success_count = 0
        
        for param_key, qml_prop in param_mapping.items():
            if param_key in geometry_params:
                try:
                    value = geometry_params[param_key]
                    self._qml_root_object.setProperty(qml_prop, float(value))
                    print(f"   ✅ {qml_prop} = {value}")
                    success_count += 1
                except Exception as e:
                    print(f"   ❌ {qml_prop}: {e}")
        
        self.status_bar.showMessage(f"Геометрия обновлена ({success_count} параметров)")
        print(f"✅ Установлено {success_count} QML свойств успешно")
        print(f"═══════════════════════════════════════════════")

    def closeEvent(self, event):
        """Обработка закрытия окна / Handle window closing"""
        try:
            # Save settings before closing
            self._save_settings()
            
            # Stop simulation if running
            if hasattr(self, 'simulation_manager') and self.simulation_manager:
                if self.is_simulation_running:
                    print("🛑 Останавливаем симуляцию перед закрытием...")
                    self._on_sim_control("stop")
                
                # Cleanup simulation manager
                self.simulation_manager.cleanup()
            
            # Stop render timer
            if hasattr(self, 'render_timer'):
                self.render_timer.stop()
            
            self.logger.info("Приложение закрывается...")
            print("✅ MainWindow: Очистка завершена, приложение закрывается")
            
        except Exception as e:
            self.logger.error(f"Ошибка при закрытии приложения: {e}")
            print(f"❌ Ошибка при закрытии: {e}")
        
        # Accept the close event
        event.accept()

    @Slot(str)
    def _on_sim_control(self, command: str):
        """Обработка команд управления симуляцией / Handle simulation control commands
        
        Args:
            command: "start", "stop", "pause", or "reset"
        """
        print(f"🎮 SimControl: {command}")
        self.logger.info(f"Simulation control: {command}")
        
        try:
            if command == "start":
                if not self.is_simulation_running:
                    print("▶️ Запуск симуляции...")
                    # ИСПРАВЛЕНО: Используем state_bus сигналы вместо прямых вызовов
                    self.simulation_manager.state_bus.start_simulation.emit()
                    self.is_simulation_running = True
                    self.status_bar.showMessage("Симуляция запущена")
                    self._start_time = None  # Reset animation timer
                    
                    # ✨ НОВОЕ: Запускаем анимацию в QML
                    if self._qml_root_object:
                        self._qml_root_object.setProperty("isRunning", True)
                        print("✅ QML анимация запущена (isRunning=True)")
                else:
                    print("⚠️ Симуляция уже запущена")
                    
            elif command == "stop":
                if self.is_simulation_running:
                    print("⏹️ Остановка симуляции...")
                    # ИСПРАВЛЕНО: Используем state_bus сигналы
                    self.simulation_manager.state_bus.stop_simulation.emit()
                    self.is_simulation_running = False
                    self.status_bar.showMessage("Симуляция остановлена")
                    
                    # ✨ НОВОЕ: Останавливаем анимацию в QML
                    if self._qml_root_object:
                        self._qml_root_object.setProperty("isRunning", False)
                        print("✅ QML анимация остановлена (isRunning=False)")
                else:
                    print("⚠️ Симуляция не запущена")
                    
            elif command == "pause":
                if self.is_simulation_running:
                    print("⏸️ Пауза симуляции...")
                    # ИСПРАВЛЕНО: Используем state_bus сигналы
                    self.simulation_manager.state_bus.pause_simulation.emit()
                    self.status_bar.showMessage("Симуляция приостановлена")
                    
                    # ✨ НОВОЕ: Приостанавливаем анимацию в QML
                    if self._qml_root_object:
                        current_running = self._qml_root_object.property("isRunning")
                        self._qml_root_object.setProperty("isRunning", not current_running)
                        state_text = "возобновлена" if not current_running else "приостановлена"
                        print(f"✅ QML анимация {state_text} (isRunning={not current_running})")
                else:
                    print("⚠️ Нечего приостанавливать")
                    
            elif command == "reset":
                print("🔄 Сброс симуляции...")
                # ИСПРАВЛЕНО: Используем state_bus сигналы
                self.simulation_manager.state_bus.reset_simulation.emit()
                self.is_simulation_running = False
                self.status_bar.showMessage("Симуляция сброшена")
                self._start_time = None  # Reset animation timer
                
                # ✨ НОВОЕ: Останавливаем анимацию и сбрасываем углы в QML
                if self._qml_root_object:
                    self._qml_root_object.setProperty("isRunning", False)
                    self._qml_root_object.setProperty("fl_angle", 0.0)
                    self._qml_root_object.setProperty("fr_angle", 0.0)
                    self._qml_root_object.setProperty("rl_angle", 0.0)
                    self._qml_root_object.setProperty("rr_angle", 0.0)
                    self._qml_root_object.setProperty("animationTime", 0.0)
                    print("✅ QML анимация сброшена (isRunning=False, все углы=0)")
                
            else:
                print(f"❌ Неизвестная команда: {command}")
                
        except Exception as e:
            error_msg = f"Ошибка управления симуляцией ({command}): {e}"
            print(f"❌ {error_msg}")
            self.logger.error(error_msg)
            self.status_bar.showMessage(f"Ошибка: {command}")
            import traceback
            traceback.print_exc()

    @Slot(dict)
    def _on_animation_changed(self, animation_params: dict):
        """Обработка изменения параметров анимации от ModesPanel
        
        Args:
            animation_params: Dictionary with animation parameters:
                - amplitude: амплитуда колебаний (м)
                - frequency: частота (Гц)
                - phase: глобальная фаза (градусы)
                - lf_phase, rf_phase, lr_phase, rr_phase: фазы для каждого колеса (градусы)
        """
        print(f"═══════════════════════════════════════════════")
        print(f"🎬 MainWindow: Параметры анимации изменены!")
        print(f"   Получено параметров: {animation_params}")
        print(f"═══════════════════════════════════════════════")
        
        self.logger.info(f"Animation changed: {animation_params}")
        
        # Обновляем параметры анимации в QML сцене
        if self._qml_root_object:
            try:
                # Амплитуда: конвертируем метры в градусы (примерное преобразование)
                # Для подвески обычно 0.05м = ~5° угла рычага
                if 'amplitude' in animation_params:
                    amplitude_m = animation_params['amplitude']
                    amplitude_deg = amplitude_m * 100  # 0.05м = 5°
                    self._qml_root_object.setProperty("userAmplitude", amplitude_deg)
                    print(f"   ✅ Амплитуда: {amplitude_m}м → {amplitude_deg}°")
                
                # Частота (Hz)
                if 'frequency' in animation_params:
                    frequency = animation_params['frequency']
                    self._qml_root_object.setProperty("userFrequency", frequency)
                    print(f"   ✅ Частота: {frequency} Гц")
                
                # Глобальная фаза (градусы)
                if 'phase' in animation_params:
                    phase = animation_params['phase']
                    self._qml_root_object.setProperty("userPhaseGlobal", phase)
                    print(f"   ✅ Глобальная фаза: {phase}°")
                
                # Фазы для каждого колеса (градусы)
                if 'lf_phase' in animation_params:
                    self._qml_root_object.setProperty("userPhaseFL", animation_params['lf_phase'])
                    print(f"   ✅ Фаза ЛП: {animation_params['lf_phase']}°")
                
                if 'rf_phase' in animation_params:
                    self._qml_root_object.setProperty("userPhaseFR", animation_params['rf_phase'])
                    print(f"   ✅ Фаза ПП: {animation_params['rf_phase']}°")
                
                if 'lr_phase' in animation_params:
                    self._qml_root_object.setProperty("userPhaseRL", animation_params['lr_phase'])
                    print(f"   ✅ Фаза ЛЗ: {animation_params['lr_phase']}°")
                
                if 'rr_phase' in animation_params:
                    self._qml_root_object.setProperty("userPhaseRR", animation_params['rr_phase'])
                    print(f"   ✅ Фаза ПЗ: {animation_params['rr_phase']}°")
                
                self.status_bar.showMessage("Параметры анимации обновлены")
                print(f"📊 Статус: Параметры анимации успешно переданы в QML")
                print(f"═══════════════════════════════════════════════")
                
            except Exception as e:
                print(f"═══════════════════════════════════════════════")
                print(f"❌ ОШИБКА обновления параметров анимации в QML!")
                print(f"   Error: {e}")
                print(f"═══════════════════════════════════════════════")
                self.logger.error(f"QML animation update failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"═══════════════════════════════════════════════")
            print(f"❌ MainWindow: QML root object отсутствует!")
            print(f"   Не можем обновить параметры анимации")
            print(f"═══════════════════════════════════════════════")
