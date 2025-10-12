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
    QMetaObject,
    Q_ARG,
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
        
        backend_name = "Qt Quick 3D (main.qml v4.3)" if use_qml_3d else "Legacy OpenGL"
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
        """Setup Qt Quick 3D full suspension scene - теперь загружает ЕДИНЫЙ main.qml"""
        print("    [QML] Загрузка ЕДИНОГО QML файла main.qml...")
        
        try:
            self._qquick_widget = QQuickWidget(self)
            self._qquick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
            
            # CRITICAL: Set up QML import paths BEFORE loading any QML
            engine = self._qquick_widget.engine()
            
            # Add Qt's QML import path
            from PySide6.QtCore import QLibraryInfo
            qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
            engine.addImportPath(str(qml_path))
            print(f"    🔧 Added QML import path: {qml_path}")
            
            # Also add local paths if they exist
            local_qml_path = Path("assets/qml")
            if local_qml_path.exists():
                engine.addImportPath(str(local_qml_path.absolute()))
                print(f"    🔧 Added local QML path: {local_qml_path.absolute()}")
            
            # ✅ НОВОЕ: Теперь используем только ОДИН файл main.qml
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
            
            print(f"    [OK] ✅ ЕДИНЫЙ QML файл 'main.qml' загружен успешно")
            print(f"    ✨ Версия: Enhanced v5.0 (объединённая, оптимизированная, с IBL)")
            print(f"    🔧 QML import paths настроены для QtQuick3D")
            
        except Exception as e:
            print(f"    [CRITICAL] Ошибка загрузки main.qml: {e}")
            import traceback
            traceback.print_exc()
            
            fallback = QLabel(
                "КРИТИЧЕСКАЯ ОШИБКА ЗАГРУЗКИ 3D СЦЕНЫ\n\n"
                f"Ошибка: {e}\n\n"
                "Проверьте файл assets/qml/main.qml\n"
                "и убедитесь, что QtQuick3D установлен правильно"
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
        # ✅ ИСПРАВЛЕНО: Разумные ограничения ширины для адаптивности
        self.tab_widget.setMinimumWidth(300)  # Минимум для узких экранов
        self.tab_widget.setMaximumWidth(800)  # Максимум чтобы не было слишком широко
        
        # Tab 1: ГеОМЕТРИЯ (Geometry)
        self.geometry_panel = GeometryPanel(self)
        scroll_geometry = QScrollArea()
        scroll_geometry.setWidgetResizable(True)
        scroll_geometry.setWidget(self.geometry_panel)
        # ✅ ИСПРАВЛЕНО: Разрешаем горизонтальную прокрутку для геометрии если нужно
        scroll_geometry.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tab_widget.addTab(scroll_geometry, "Геометрия")
        print("      ✅ Вкладка 'Геометрия' создана")
        
        # Tab 2: ПНЕВМОСИСТЕМА (Pneumatics)
        self.pneumo_panel = PneumoPanel(self)
        scroll_pneumo = QScrollArea()
        scroll_pneumo.setWidgetResizable(True)
        scroll_pneumo.setWidget(self.pneumo_panel)
        scroll_pneumo.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tab_widget.addTab(scroll_pneumo, "Пневмосистема")
        print("      ✅ Вкладка 'Пневмосистема' создана")
        
        # Tab 3: РЕЖИМЫ СТАБИЛИЗАТОРА (Modes)
        self.modes_panel = ModesPanel(self)
        scroll_modes = QScrollArea()
        scroll_modes.setWidgetResizable(True)
        scroll_modes.setWidget(self.modes_panel)
        scroll_modes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tab_widget.addTab(scroll_modes, "Режимы стабилизатора")
        print("      ✅ Вкладка 'Режимы стабилизатора' создана")
        
        # Tab 4: ГРАФИКА И ВИЗУАЛИЗАЦИЯ (объединенная панель)
        self.graphics_panel = GraphicsPanel(self)
        self._graphics_panel = self.graphics_panel  # ✅ ИСПРАВЛЕНО: Добавляем атрибут для диагностики
        # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: НЕ оборачиваем GraphicsPanel в еще один ScrollArea!
        # Она уже имеет внутренние ScrollArea для каждой вкладки
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
        
        # ✅ ИСПРАВЛЕНО: Более гибкие stretch factors для адаптивности
        self.main_horizontal_splitter.setStretchFactor(0, 3)  # 75% для сцены+графиков
        self.main_horizontal_splitter.setStretchFactor(1, 1)  # 25% для панелей (но может расти)
        
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

        # ✅ ИСПРАВЛЕНО: Graphics panel подключение сигналов
        if self.graphics_panel:
            print("🔧 Подключаем сигналы GraphicsPanel...")
            
            # Lighting changes
            self.graphics_panel.lighting_changed.connect(self._on_lighting_changed)
            print("   ✅ Сигнал lighting_changed подключен")
            
            # Material changes
            self.graphics_panel.material_changed.connect(self._on_material_changed)
            print("   ✅ Сигнал material_changed подключен")
            
            # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Environment changes
            self.graphics_panel.environment_changed.connect(self._on_environment_changed)  
            print("   ✅ Сигнал environment_changed подключен")
            
            # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Quality changes
            self.graphics_panel.quality_changed.connect(self._on_quality_changed)
            print("   ✅ Сигнал quality_changed подключен")
            
            # Camera changes
            self.graphics_panel.camera_changed.connect(self._on_camera_changed)
            print("   ✅ Сигнал camera_changed подключен")
            
            # Effects changes
            self.graphics_panel.effects_changed.connect(self._on_effects_changed)
            print("   ✅ Сигнал effects_changed подключен")
            
            # Preset applied
            self.graphics_panel.preset_applied.connect(self._on_preset_applied)
            print("   ✅ Сигнал preset_applied подключен")
            
            print("✅ Все сигналы GraphicsPanel подключены УСПЕШНО")
            
            # ✅ ДОБАВЛЯЕМ ТЕСТОВЕ ПОДКЛЮЧЕНИЕ ДЛЯ ДИАГНОСТИКИ
            try:
                # Тестируем работу сигналов немедленно после подключения
                print("🧪 Тестирование подключения сигналов...")
                
                # Создаем тестовую функцию для проверки
                def test_environment_signal(params):
                    print(f"🔥 ТЕСТ: environment_changed получен! Параметры: {params}")
                
                def test_quality_signal(params):
                    print(f"🔥 ТЕСТ: quality_changed получен! Параметры: {params}")
                
                # Подключаем тестовые обработчики 
                self.graphics_panel.environment_changed.connect(test_environment_signal)
                self.graphics_panel.quality_changed.connect(test_quality_signal)
                
                print("   ✅ Тестовые обработчики подключены")
                
            except Exception as e:
                print(f"   ❌ Ошибка тестового подключения: {e}")
            
        else:
            print("❌ GraphicsPanel недоступна для подключения сигналов!")

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

            if not success and key == "geometry":
                self._set_geometry_properties_fallback(payload)

    def _invoke_qml_function(self, method_name: str, payload: Optional[Dict[str, Any]] = None) -> bool:
        if not self._qml_root_object:
            return False

        connection = Qt.ConnectionType.DirectConnection
        try:
            if payload is None:
                return QMetaObject.invokeMethod(self._qml_root_object, method_name, connection)
            return QMetaObject.invokeMethod(
                self._qml_root_object,
                method_name,
                connection,
                Q_ARG("QVariant", payload),
            )
        except Exception as exc:
            self.logger.debug(f"Failed to call {method_name} in QML: {exc}")
            return False

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

    @staticmethod
    def _set_geometry_properties_fallback(geometry_params: Dict[str, Any]):
        if not geometry_params:
            return

        mapping = {
            "frameLength": "userFrameLength",
            "frameHeight": "userFrameHeight",
            "frameBeamSize": "userBeamSize",
            "leverLength": "userLeverLength",
            "cylinderBodyLength": "userCylinderLength",
            "trackWidth": "userTrackWidth",
            "frameToPivot": "userFrameToPivot",
            "rodPosition": "userRodPosition",
            "boreHead": "userBoreHead",
            "boreRod": "userBoreRod",
            "rodDiameter": "userRodDiameter",
            "pistonThickness": "userPistonThickness",
            "pistonRodLength": "userPistonRodLength",
        }

        for key, prop in mapping.items():
            if key in geometry_params:
                try:
                    value = float(geometry_params[key])
                    MainWindow._set_qml_property(prop, value)
                except Exception as e:
                    print(f"  ❌ Failed to set {prop}: {e}")

    @staticmethod
    def _set_qml_property(name: str, value: Any):
        """Установить QML свойство через rootObject (если доступно)"""
        if not name or value is None:
            return

        target = getattr(MainWindow, "_qml_root_object", None)
        if target is not None:
            try:
                target.setProperty(name, value)
                print(f"   ✅ Set {name} = {value}")
            except Exception as e:
                print(f"   ❌ Ошибка установки {name}: {e}")

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
        """Обработчик изменения параметров окружения - ПРЯМОЙ ВЫЗОВ QML"""
        print(f"🌍 MainWindow: Environment changed: {params}")
        self.logger.debug(f"Environment update: {params}")
        
        # ✅ ИСПРАВЛЕНО: НЕ используем систему очередей, вызываем QML НАПРЯМУЮ
        if self._qml_root_object:
            try:
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt
                
                print(f"🔧 MainWindow: Вызываем applyEnvironmentUpdates напрямую...")
                print(f"     fog_enabled = {params.get('fog_enabled', 'N/A')}")
                
                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "applyEnvironmentUpdates",
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", params)
                )
                
                if success:
                    self.status_bar.showMessage("Окружение обновлено")
                    print("✅ Successfully called applyEnvironmentUpdates()")
                else:
                    print("❌ Failed to call applyEnvironmentUpdates()")
                    
            except Exception as e:
                self.logger.error(f"Environment update failed: {e}")
                print(f"❌ Exception in environment update: {e}")
                import traceback
                traceback.print_exc()

    @Slot(dict)
    def _on_quality_changed(self, params: Dict[str, Any]):
        """Обработчик изменения параметров качества - ПРЯМОЙ ВЫЗОВ QML"""
        print(f"⚙️ MainWindow: Quality changed: {params}")
        self.logger.debug(f"Quality update: {params}")
        
        # ✅ ИСПРАВЛЕНО: НЕ используем систему очередей, вызываем QML НАПРЯМУЮ
        if self._qml_root_object:
            try:
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt
                
                print(f"🔧 MainWindow: Вызываем applyQualityUpdates напрямую...")
                print(f"     antialiasing = {params.get('antialiasing', 'N/A')}")
                print(f"     aa_quality = {params.get('aa_quality', 'N/A')}")
                
                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "applyQualityUpdates",
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", params)
                )
                
                if success:
                    self.status_bar.showMessage("Качество обновлено")
                    print("✅ Successfully called applyQualityUpdates()")
                else:
                    print("❌ Failed to call applyQualityUpdates()")
                    
            except Exception as e:
                self.logger.error(f"Quality update failed: {e}")
                print(f"❌ Exception in quality update: {e}")
                import traceback
                traceback.print_exc()

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
