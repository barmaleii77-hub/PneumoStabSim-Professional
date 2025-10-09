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
from .panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
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
        self.graphics_panel: Optional[GraphicsPanel] = None  # NEW: Graphics panel
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

        # Batch updates: queue updates to minimize cross-language calls to QML
        self._qml_update_queue: Dict[str, dict] = {}
        self._qml_flush_timer = QTimer(self)
        self._qml_flush_timer.setSingleShot(True)
        self._qml_flush_timer.timeout.connect(self._flush_qml_updates)
        print("  ✅ Batch update queue initialized")

        print("  ⏸️  SimulationManager запустится после window.show()")

        # Restore settings
        self._restore_settings()
        print("  ✅ Настройки восстановлены")

        self.logger.info("Главное окно (Qt Quick 3D) инициализировано")
        print("✅ MainWindow.__init__() завершён")

    # ------------------------------------------------------------------
    # UI Construction - НОВАЯ СТРУКТУРНА!
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
            
            # Use optimized QML by default
            qml_path = Path("assets/qml/main_optimized.qml")
            if not qml_path.exists():
                # Fallback to original main.qml if optimized not present
                qml_path = Path("assets/qml/main.qml")
            if not qml_path.exists():
                raise FileNotFoundException(f"QML файл не найден: {qml_path.absolute()}")
            
            qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
            print(f"    Загрузка QML: {qml_url.toString()}")
            
            self._qquick_widget.setSource(qml_url)
            
            if self._qquick_widget.status() == QQuickWidget.Status.Error:
                errors = self._qquick_widget.errors()
                error_msg = "\n".join(str(e) for e in errors)
                raise RuntimeError(f"Ошибки QML:\n{error_msg}")
            
            self._qml_root_object = self._qquick_widget.rootObject()
            if not self._qml_root_object:
                raise RuntimeError("Не удалось получить корневой объект QML")
            
            print("    [OK] QML загружен успешно")
            
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
        # Use same loader but prefer optimized QML
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
        
        # Tab 4: Графика и визуализация (объединенная панель)
        self.graphics_panel = GraphicsPanel(self)
        # Не помещаем в scroll area, так как панель уже имеет собственные вкладки с прокруткой
        self.tab_widget.addTab(self.graphics_panel, "🎨 Графика")
        print("      ✅ Вкладка 'Графика и визуализация' создана")
        
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

    # =================================================================
    # Graphics Panel Signal Handlers
    # =================================================================
    
    @Slot(dict)
    def _on_lighting_changed(self, lighting_params: dict):
        """Обработка изменения параметров освещения от GraphicsPanel
        
        Args:
            lighting_params: Dictionary with lighting parameters
        """
        print(f"═══════════════════════════════════════════════")
        print(f"💡 MainWindow: Параметры освещения изменены!")
        print(f"   Получено параметров: {lighting_params}")
        print(f"═══════════════════════════════════════════════")
        
        self.logger.info(f"Lighting changed: {lighting_params}")
        
        # Обновляем освещение в QML сцене
        if self._qml_root_object:
            try:
                # ИСПРАВЛЕНО: Используем новую функцию updateLighting
                if hasattr(self._qml_root_object, 'updateLighting'):
                    self._qml_root_object.updateLighting(lighting_params)
                    print(f"   ✅ Освещение передано в QML через updateLighting()")
                else:
                    # Fallback: прямая установка свойств
                    if 'key_light' in lighting_params:
                        key_light = lighting_params['key_light']
                        if 'brightness' in key_light:
                            self._qml_root_object.setProperty("keyLightBrightness", key_light['brightness'])
                        if 'color' in key_light:
                            self._qml_root_object.setProperty("keyLightColor", key_light['color'])
                        if 'angle_x' in key_light:
                            self._qml_root_object.setProperty("keyLightAngleX", key_light['angle_x'])
                        if 'angle_y' in key_light:
                            self._qml_root_object.setProperty("keyLightAngleY", key_light['angle_y'])
                        print(f"   ✅ Key Light обновлен")
                    
                    if 'fill_light' in lighting_params:
                        fill_light = lighting_params['fill_light']
                        if 'brightness' in fill_light:
                            self._qml_root_object.setProperty("fillLightBrightness", fill_light['brightness'])
                        if 'color' in fill_light:
                            self._qml_root_object.setProperty("fillLightColor", fill_light['color'])
                        print(f"   ✅ Fill Light обновлен")
                    
                    if 'point_light' in lighting_params:
                        point_light = lighting_params['point_light']
                        if 'brightness' in point_light:
                            self._qml_root_object.setProperty("pointLightBrightness", point_light['brightness'])
                        if 'position_y' in point_light:
                            self._qml_root_object.setProperty("pointLightY", point_light['position_y'])
                        print(f"   ✅ Point Light обновлен")
                
                self.status_bar.showMessage("Освещение обновлено")
                print(f"📊 Статус: Освещение успешно обновлено в QML")
                print(f"═══════════════════════════════════════════════")
                
            except Exception as e:
                print(f"═══════════════════════════════════════════════")
                print(f"❌ ОШИБКА обновления освещения в QML!")
                print(f"   Error: {e}")
                print(f"═══════════════════════════════════════════════")
                self.logger.error(f"QML lighting update failed: {e}")
        else:
            print(f"❌ QML root object отсутствует!")
    
    @Slot(dict)
    def _on_environment_changed(self, env_params: dict):
        """Обработка изменения параметров окружения от GraphicsPanel
        
        Args:
            env_params: Dictionary with environment parameters
        """
        print(f"🌍 MainWindow: Параметры окружения изменены: {env_params}")
        self.logger.info(f"Environment changed: {env_params}")
        
        # Обновляем окружение в QML сцене
        if self._qml_root_object:
            try:
                # ИСПРАВЛЕНО: Используем новую функцию updateEnvironment
                if hasattr(self._qml_root_object, 'updateEnvironment'):
                    self._qml_root_object.updateEnvironment(env_params)
                    print(f"   ✅ Окружение передано в QML через updateEnvironment()")
                else:
                    # Fallback: прямая установка свойств
                    if 'background_color' in env_params:
                        self._qml_root_object.setProperty("backgroundColor", env_params['background_color'])
                        print(f"   ✅ Цвет фона обновлен: {env_params['background_color']}")
                
                self.status_bar.showMessage("Окружение обновлено")
                
            except Exception as e:
                print(f"❌ ОШИБКА обновления окружения в QML: {e}")
                self.logger.error(f"QML environment update failed: {e}")
        else:
            print(f"❌ QML root object отсутствует!")
    
    @Slot(dict)
    def _on_quality_changed(self, quality_params: dict):
        """Обработка изменения параметров качества от GraphicsPanel
        
        Args:
            quality_params: Dictionary with quality parameters
        """
        print(f"⚙️ MainWindow: Параметры качества изменены: {quality_params}")
        self.logger.info(f"Quality changed: {quality_params}")
        
        # Обновляем качество рендеринга в QML сцене
        if self._qml_root_object:
            try:
                # ИСПРАВЛЕНО: Используем новую функцию updateQuality
                if hasattr(self._qml_root_object, 'updateQuality'):
                    self._qml_root_object.updateQuality(quality_params)
                    print(f"   ✅ Качество передано в QML через updateQuality()")
                else:
                    # Fallback: прямая установка свойств
                    if 'antialiasing' in quality_params:
                        aa_mode = quality_params['antialiasing']
                        self._qml_root_object.setProperty("antialiasingMode", aa_mode)
                        print(f"   ✅ Сглаживание обновлено: {aa_mode}")
                    
                    if 'aa_quality' in quality_params:
                        aa_quality = quality_params['aa_quality']
                        self._qml_root_object.setProperty("antialiasingQuality", aa_quality)
                        print(f"   ✅ Качество сглаживания обновлено: {aa_quality}")
                    
                    if 'shadows_enabled' in quality_params:
                        shadows = quality_params['shadows_enabled']
                        self._qml_root_object.setProperty("shadowsEnabled", shadows)
                        print(f"   ✅ Тени: {'включены' if shadows else 'отключены'}")
                
                self.status_bar.showMessage("Качество рендеринга обновлено")
                
            except Exception as e:
                print(f"❌ ОШИБКА обновления качества в QML: {e}")
                self.logger.error(f"QML quality update failed: {e}")
        else:
            print(f"❌ QML root object отсутствует!")

    @Slot(str)
    def _on_preset_applied(self, preset_name: str):
        """Обработка применения пресета освещения от GraphicsPanel
        
        Args:
            preset_name: Name of applied preset ('day', 'night', 'industrial')
        """
        preset_names = {
            'day': 'Дневное',
            'night': 'Ночное', 
            'industrial': 'Промышленное'
        }
        
        display_name = preset_names.get(preset_name, preset_name)
        print(f"🎭 MainWindow: Применен пресет освещения '{display_name}'")
        self.logger.info(f"Lighting preset applied: {preset_name}")
        
        self.status_bar.showMessage(f"Применен пресет: {display_name}")
        # Preset application may affect lighting/materials — flush quickly
        if self._qml_root_object:
            self._queue_qml_update('preset', {'name': preset_name})

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
                        # Start immediately (do not batch start/stop commands)
                        try:
                            self._qml_root_object.setProperty("isRunning", True)
                            print("✅ QML анимация запущена (isRunning=True)")
                        except Exception:
                            print("⚠️ Не удалось немедленно установить isRunning=True, поставлено в очередь")
                            self._queue_qml_update('control', {'isRunning': True})
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
                        try:
                            self._qml_root_object.setProperty("isRunning", False)
                            print("✅ QML анимация остановлена (isRunning=False)")
                        except Exception:
                            self._queue_qml_update('control', {'isRunning': False})
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
                    # Batch reset properties for fewer QML calls
                    reset_params = {
                        'isRunning': False,
                        'fl_angle': 0.0,
                        'fr_angle': 0.0,
                        'rl_angle': 0.0,
                        'rr_angle': 0.0,
                        'animationTime': 0.0
                    }
                    self._queue_qml_update('reset', reset_params)
                    print("✅ QML анимация поставлена в очередь на сброс")
                
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
            # Batch animation parameters to send in a single flush
            if self._qml_root_object:
                # Convert amplitude meters -> degrees if present
                if 'amplitude' in animation_params:
                    animation_params = dict(animation_params)  # copy
                    amplitude_m = animation_params['amplitude']
                    animation_params['amplitude_deg'] = amplitude_m * 100
                self._queue_qml_update('animation', animation_params)
                self.status_bar.showMessage("Параметры анимации запланированы")
                print(f"   ✅ Анимация поставлена в очередь (batch)")
            else:
                print(f"═══════════════════════════════════════════════")
                print(f"❌ MainWindow: QML root object отсутствует!")
                print(f"   Не можем обновить параметры анимации")
                print(f"═══════════════════════════════════════════════")
    
    # ------------------------------------------------------------------
    def _queue_qml_update(self, key: str, params: dict):
        """Add or merge an update into the batch queue and schedule a flush."""
        if not isinstance(params, dict):
            return
        existing = self._qml_update_queue.get(key)
        if existing:
            # Shallow merge - newer keys overwrite older
            existing.update(params)
        else:
            self._qml_update_queue[key] = dict(params)
        # Schedule flush on next event loop iteration
        if not self._qml_flush_timer.isActive():
            self._qml_flush_timer.start(0)

    def _flush_qml_updates(self):
        """Flush queued updates to QML in a single batch where possible."""
        if not self._qml_root_object or not self._qml_update_queue:
            self._qml_update_queue.clear()
            return

        batched = dict(self._qml_update_queue)
        self._qml_update_queue.clear()

        try:
            # Prefer single batched method if provided by QML
            if hasattr(self._qml_root_object, 'applyBatchedUpdates'):
                self._qml_root_object.applyBatchedUpdates(batched)
                print("   ✅ Batched updates applied via applyBatchedUpdates()")
                return

            # Otherwise, call existing updateX methods once per category
            if 'lighting' in batched and hasattr(self._qml_root_object, 'updateLighting'):
                self._qml_root_object.updateLighting(batched['lighting'])
            if 'environment' in batched and hasattr(self._qml_root_object, 'updateEnvironment'):
                self._qml_root_object.updateEnvironment(batched['environment'])
            if 'quality' in batched and hasattr(self._qml_root_object, 'updateQuality'):
                self._qml_root_object.updateQuality(batched['quality'])
            if 'preset' in batched and hasattr(self._qml_root_object, 'applyPreset'):
                self._qml_root_object.applyPreset(batched['preset'].get('name'))
            if 'material' in batched and hasattr(self._qml_root_object, 'updateMaterials'):
                self._qml_root_object.updateMaterials(batched['material'])
            if 'camera' in batched and hasattr(self._qml_root_object, 'updateCamera'):
                self._qml_root_object.updateCamera(batched['camera'])
            if 'effects' in batched and hasattr(self._qml_root_object, 'updateEffects'):
                self._qml_root_object.updateEffects(batched['effects'])
            if 'geometry' in batched and hasattr(self._qml_root_object, 'updateGeometry'):
                self._qml_root_object.updateGeometry(batched['geometry'])
            if 'animation' in batched and hasattr(self._qml_root_object, 'updateAnimation'):
                self._qml_root_object.updateAnimation(batched['animation'])

            # Fallback: set properties directly if specific updates not available
            for k, v in batched.items():
                if k in ('control', 'reset') and isinstance(v, dict):
                    for prop, val in v.items():
                        try:
                            self._qml_root_object.setProperty(prop, val)
                        except Exception:
                            pass

            print("   ✅ Batched updates flushed to QML")
        except Exception as e:
            print(f"⚠️ Ошибка при применении batched updates: {e}")
            self.logger.error(f"Batched QML update failed: {e}")

    # =================================================================
    # UI Setup Methods (Menu, Toolbar, Status Bar)
    # =================================================================
    
    def _setup_menus(self):
        """Создать меню / Create menu bar"""
        print("  ✅ Меню настроено (заглушка)")
        pass  # TODO: Implement menu bar
    
    def _setup_toolbar(self):
        """Создать панель инструментов / Create toolbar"""
        print("  ✅ Панель инструментов настроена (заглушка)")
        pass  # TODO: Implement toolbar
    
    def _setup_status_bar(self):
        """Создать строку состояния / Create status bar"""
        from PySide6.QtWidgets import QStatusBar, QLabel
        
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
        
        print("  ✅ Строка состояния настроена")

    def _connect_simulation_signals(self):
        """Подключить сигналы симуляции / Connect simulation signals"""
        print("  ✅ Сигналы подключены (заглушка)")
        pass  # TODO: Connect simulation manager signals
        
    def _update_render(self):
        """Обновить рендеринг / Update rendering (called by timer)"""
        # Simple update - just process events
        if hasattr(self, 'current_snapshot') and self.current_snapshot and hasattr(self, 'sim_time_label'):
            self.sim_time_label.setText(f"Время симуляции: {self.current_snapshot.simulation_time:.3f}с")
            self.step_count_label.setText(f"Шагов: {self.current_snapshot.step_number}")
            
            if self.current_snapshot.aggregates.physics_step_time > 0:
                fps = 1.0 / self.current_snapshot.aggregates.physics_step_time
                self.fps_label.setText(f"FPS: {fps:.0f}")

        # ✅ ИСПРАВЛЕНО: Убрана старая дефолтная анимация!
        # Старый код, который конфликтовал с новой анимацией:
        # if self._qml_root_object and self.is_simulation_running:
        #     # Старая синусоидальная анимация удалена
        #     pass
        
        # Теперь анимация полностью управляется из QML через isRunning и userFrequency/userAmplitude
        # Никаких прямых установок углов из Python больше нет!

    # =================================================================
    # Graphics Panel Signal Handlers - ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ
    # =================================================================
    
    @Slot(dict)
    def _on_material_changed(self, material_params: dict):
        """Обработка изменения параметров материалов от GraphicsPanel
        
        Args:
            material_params: Dictionary with material parameters
        """
        print(f"═══════════════════════════════════════════════")
        print(f"🏗️ MainWindow: Параметры материалов изменены!")
        print(f"   Получено параметров: {material_params}")
        print(f"═══════════════════════════════════════════════")
        
        self.logger.info(f"Materials changed: {material_params}")
        
        # Обновляем материалы в QML сцене
        if self._qml_root_object:
            try:
                # ИСПРАВЛЕНО: Используем новую функцию updateMaterials
                if hasattr(self._qml_root_object, 'updateMaterials'):
                    self._qml_root_object.updateMaterials(material_params)
                    print(f"   ✅ Материалы переданы в QML через updateMaterials()")
                else:
                    # Fallback: прямая установка свойств
                    if 'metal' in material_params:
                        metal = material_params['metal']
                        if 'roughness' in metal:
                            self._qml_root_object.setProperty("metalRoughness", metal['roughness'])
                        if 'metalness' in metal:
                            self._qml_root_object.setProperty("metalMetalness", metal['metalness'])
                        if 'clearcoat' in metal:
                            self._qml_root_object.setProperty("metalClearcoat", metal['clearcoat'])
                    
                    if 'glass' in material_params:
                        glass = material_params['glass']
                        if 'opacity' in glass:
                            self._qml_root_object.setProperty("glassOpacity", glass['opacity'])
                        if 'roughness' in glass:
                            self._qml_root_object.setProperty("glassRoughness", glass['roughness'])
                    
                    if 'frame' in material_params:
                        frame = material_params['frame']
                        if 'metalness' in frame:
                            self._qml_root_object.setProperty("frameMetalness", frame['metalness'])
                        if 'roughness' in frame:
                            self._qml_root_object.setProperty("frameRoughness", frame['roughness'])
                    
                    print(f"   ✅ Материалы обновлены через setProperty() (fallback)")
                
                self.status_bar.showMessage("Материалы обновлены")
                print(f"📊 Статус: Материалы успешно обновлены в QML")
                print(f"═══════════════════════════════════════════════")
                
            except Exception as e:
                print(f"═══════════════════════════════════════════════")
                print(f"❌ ОШИБКА обновления материалов в QML!")
                print(f"   Error: {e}")
                print(f"═══════════════════════════════════════════════")
                self.logger.error(f"QML material update failed: {e}")
        else:
            print(f"❌ QML root object отсутствует!")
    
    @Slot(dict)
    def _on_camera_changed(self, camera_params: dict):
        """Обработка изменения параметров камеры от GraphicsPanel
        
        Args:
            camera_params: Dictionary with camera parameters
        """
        print(f"📷 MainWindow: Параметры камеры изменены: {camera_params}")
        self.logger.info(f"Camera changed: {camera_params}")
        
        # Обновляем настройки камеры в QML сцене
        if self._qml_root_object:
            try:
                # ИСПРАВЛЕНО: Используем новую функцию updateCamera
                if hasattr(self._qml_root_object, 'updateCamera'):
                    self._qml_root_object.updateCamera(camera_params)
                    print(f"   ✅ Настройки камеры переданы в QML через updateCamera()")
                else:
                    # Fallback: прямая установка свойств
                    if 'fov' in camera_params:
                        self._qml_root_object.setProperty("cameraFov", camera_params['fov'])
                        print(f"   ✅ Поле зрения: {camera_params['fov']}°")
                    
                    if 'near' in camera_params:
                        self._qml_root_object.setProperty("cameraNear", camera_params['near'])
                        print(f"   ✅ Ближняя плоскость: {camera_params['near']}мм")
                    
                    if 'far' in camera_params:
                        self._qml_root_object.setProperty("cameraFar", camera_params['far'])
                        print(f"   ✅ Дальняя плоскость: {camera_params['far']}мм")
                    
                    if 'speed' in camera_params:
                        self._qml_root_object.setProperty("cameraSpeed", camera_params['speed'])
                        print(f"   ✅ Скорость камеры: {camera_params['speed']}")
                    
                    if 'auto_rotate' in camera_params:
                        self._qml_root_object.setProperty("autoRotate", camera_params['auto_rotate'])
                        print(f"   ✅ Автоматическое вращение: {'включено' if camera_params['auto_rotate'] else 'отключено'}")
                    
                    if 'auto_rotate_speed' in camera_params:
                        self._qml_root_object.setProperty("autoRotateSpeed", camera_params['auto_rotate_speed'])
                        print(f"   ✅ Скорость автовращения: {camera_params['auto_rotate_speed']}")
                
                self.status_bar.showMessage("Настройки камеры обновлены")
                
            except Exception as e:
                print(f"❌ ОШИБКА обновления настроек камеры в QML: {e}")
                self.logger.error(f"QML camera update failed: {e}")
        else:
            print(f"❌ QML root object отсутствует!")
    
    @Slot(dict)
    def _on_effects_changed(self, effects_params: dict):
        """Обработка изменения параметров эффектов от GraphicsPanel
        
        Args:
            effects_params: Dictionary with effects parameters
        """
        print(f"✨ MainWindow: Параметры эффектов изменены: {effects_params}")
        self.logger.info(f"Effects changed: {effects_params}")
        
        # Обновляем эффекты в QML сцене
        if self._qml_root_object:
            try:
                # ИСПРАВЛЕНО: Используем новую функцию updateEffects
                if hasattr(self._qml_root_object, 'updateEffects'):
                    self._qml_root_object.updateEffects(effects_params)
                    print(f"   ✅ Эффекты переданы в QML через updateEffects()")
                else:
                    # Fallback: прямая установка свойств
                    if 'bloom_enabled' in effects_params:
                        self._qml_root_object.setProperty("bloomEnabled", effects_params['bloom_enabled'])
                        print(f"   ✅ Bloom: {'включен' if effects_params['bloom_enabled'] else 'отключен'}")
                    
                    if 'bloom_intensity' in effects_params:
                        self._qml_root_object.setProperty("bloomIntensity", effects_params['bloom_intensity'])
                        print(f"   ✅ Интенсивность Bloom: {effects_params['bloom_intensity']}")
                    
                    if 'ssao_enabled' in effects_params:
                        self._qml_root_object.setProperty("ssaoEnabled", effects_params['ssao_enabled'])
                        print(f"   ✅ SSAO: {'включен' if effects_params['ssao_enabled'] else 'отключен'}")
                    
                    if 'ssao_intensity' in effects_params:
                        self._qml_root_object.setProperty("ssaoIntensity", effects_params['ssao_intensity'])
                        print(f"   ✅ Интенсивность SSAO: {effects_params['ssao_intensity']}")
                    
                    if 'motion_blur' in effects_params:
                        self._qml_root_object.setProperty("motionBlur", effects_params['motion_blur'])
                        print(f"   ✅ Motion Blur: {'включен' if effects_params['motion_blur'] else 'отключен'}")
                    
                    if 'depth_of_field' in effects_params:
                        self._qml_root_object.setProperty("depthOfField", effects_params['depth_of_field'])
                        print(f"   ✅ Depth of Field: {'включен' if effects_params['depth_of_field'] else 'отключен'}")
                
                self.status_bar.showMessage("Визуальные эффекты обновлены")
                
            except Exception as e:
                print(f"❌ ОШИБКА обновления эффектов в QML: {e}")
                self.logger.error(f"QML effects update failed: {e}")
        else:
            print(f"❌ QML root object отсутствует!")
    
    def _restore_settings(self):
        """Восстановить настройки / Restore settings"""
        print("  ✅ Настройки восстановлены (заглушка)")
        pass  # TODO: Restore window settings

    @Slot(dict)
    def _on_geometry_changed_qml(self, geometry_params: dict):
        """Обработчик прямого изменения геометрии от панели геометрии
        
        Args:
            geometry_params: Параметры геометрии от панели (уже в нужном формате)
        """
        print(f"═══════════════════════════════════════════════")
        print(f"🔺 MainWindow: Получен сигнал geometry_changed от панели")
        print(f"   Параметры ({len(geometry_params)}): {list(geometry_params.keys())}")
        print(f"   Ключевые значения:")
        for key in ['frameLength', 'leverLength', 'trackWidth', 'rodPosition']:
            if key in geometry_params:
                print(f"      {key} = {geometry_params[key]}")
        print(f"═══════════════════════════════════════════════")
        
        if not self._qml_root_object:
            print(f"❌ QML root object отсутствует! Схема не может обновиться")
            print(f"═══════════════════════════════════════════════")
            return
        
        try:
            # ИСПРАВЛЕНО: Сначала пробуем updateGeometry функцию
            if hasattr(self._qml_root_object, 'updateGeometry'):
                print(f"   🔧 Вызываем updateGeometry() в QML...")
                self._qml_root_object.updateGeometry(geometry_params)
                print(f"   ✅ Геометрия передана в QML через updateGeometry()")
            else:
                print(f"   ⚠️ QML объект не имеет метода updateGeometry, используем fallback")
                # Fallback: устанавливаем свойства напрямую
                property_map = {
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
                
                updated_props = []
                for geom_key, qml_prop in property_map.items():
                    if geom_key in geometry_params:
                        try:
                            self._qml_root_object.setProperty(qml_prop, geometry_params[geom_key])
                            updated_props.append(f"{qml_prop}={geometry_params[geom_key]}")
                        except Exception as e:
                            print(f"      ❌ Ошибка установки {qml_prop}: {e}")
                
                if updated_props:
                    print(f"   ✅ Обновлено свойств: {len(updated_props)}")
                    for prop in updated_props[:3]:  # Показываем только первые 3
                        print(f"      {prop}")
                    if len(updated_props) > 3:
                        print(f"      ... и ещё {len(updated_props) - 3}")
            
            # Принудительное обновление QML сцены
            if hasattr(self._qquick_widget, 'update'):
                self._qquick_widget.update()
                print(f"   🔄 QML widget принудительно обновлен")
            
            self.status_bar.showMessage("Геометрия обновлена в 3D сцене")
            print(f"📊 Статус: Геометрия успешно обновлена")
            
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА обновления геометрии в QML!")
            print(f"   Error: {e}")
            print(f"   Type: {type(e)}")
            import traceback
            traceback.print_exc()
            self.logger.error(f"QML geometry update failed: {e}")
            self.status_bar.showMessage(f"Ошибка обновления геометрии: {e}")
        
        print(f"═══════════════════════════════════════════════")
