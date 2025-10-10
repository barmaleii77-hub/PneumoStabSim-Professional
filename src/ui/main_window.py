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
    SETTINGS_SPLITTER = "MainWindow/Splitter"  # NEW: Save splitter position
    SETTINGS_HORIZONTAL_SPLITTER = "MainWindow/HorizontalSplitter"  # NEW: Save horizontal splitter position
    SETTINGS_LAST_TAB = "MainWindow/LastTab"    # NEW: Save selected tab
    SETTINGS_LAST_PRESET = "Presets/LastPath"

    def __init__(self, use_qml_3d: bool = True):
        super().__init__()
        
        # Store visualization backend choice
        self.use_qml_3d = use_qml_3d
        
        backend_name = "Qt Quick 3D (Optimized v4.2)" if use_qml_3d else "Legacy OpenGL"
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
        from src.ui.geometry_bridge import create_geometry_converter
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
        """Setup Qt Quick 3D full suspension scene - ТОЛЬКО main_optimized.qml"""
        print("    [QML] Загрузка ТОЛЬКО main_optimized.qml...")
        
        try:
            self._qquick_widget = QQuickWidget(self)
            self._qquick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
            
            # ✅ ЕДИНСТВЕННЫЙ ФАЙЛ: main_optimized.qml
            qml_path = Path("assets/qml/main_optimized.qml")
            
            print(f"    🔍 ЗАГРУЗКА main_optimized.qml:")
            print(f"       Файл: {qml_path}")
            print(f"       Существует: {qml_path.exists()}")
            
            if not qml_path.exists():
                raise FileNotFoundError(f"КРИТИЧНО: main_optimized.qml не найден!")
                
            # Проверяем размер файла
            file_size = qml_path.stat().st_size
            print(f"       Размер: {file_size:,} байт")
            
            if file_size < 30000:  # main_optimized.qml должен быть большим
                raise ValueError(f"КРИТИЧНО: Файл слишком мал ({file_size} байт)")
                
            print(f"    ✅ Загружаем main_optimized.qml v4.2 (БЕЗ ДУБЛИРОВАНИЯ)")
            qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
            
            print(f"    📂 Путь: {qml_url.toString()}")
            
            # Загружаем файл
            self._qquick_widget.setSource(qml_url)
            
            # Проверяем статус
            status = self._qquick_widget.status()
            print(f"    📊 Статус загрузки: {status}")
            
            if status == QQuickWidget.Status.Error:
                errors = self._qquick_widget.errors()
                error_messages = [str(e) for e in errors]
                print(f"    ❌ ОШИБКИ QML:")
                for i, error in enumerate(error_messages, 1):
                    print(f"       {i}. {error}")
                raise RuntimeError(f"Ошибки загрузки main_optimized.qml:\n{'\n'.join(error_messages)}")
                    
            elif status == QQuickWidget.Status.Loading:
                print(f"    ⏳ Загружается...")
            elif status == QQuickWidget.Status.Ready:
                print(f"    ✅ Загружен успешно!")
            
            # Получаем корневой объект
            self._qml_root_object = self._qquick_widget.rootObject()
            if not self._qml_root_object:
                raise RuntimeError("КРИТИЧНО: Не удалось получить QML root object")
            
            print(f"    ✅ main_optimized.qml загружен и готов к работе")
            
            # Проверяем ключевые свойства оптимизированной версии
            key_properties = ['glassIOR', 'iblEnabled', 'fogEnabled', 'bloomThreshold', 'ssaoRadius']
            print(f"    🔍 Проверка оптимизированных свойств:")
            for prop in key_properties:
                try:
                    value = self._qml_root_object.property(prop)
                    print(f"    ✅ {prop}: {value}")
                except Exception as e:
                    print(f"    ❌ {prop}: {e}")
            
            # Проверяем ключевые функции
            key_functions = ['updateGeometry', 'updateMaterials', 'updateLighting', 'applyBatchedUpdates']
            print(f"    🔍 Проверка функций:")
            available = 0
            for func in key_functions:
                if hasattr(self._qml_root_object, func):
                    print(f"    ✅ {func}() доступна")
                    available += 1
                else:
                    print(f"    ❌ {func}() НЕ НАЙДЕНА")
            
            print(f"    📊 Доступно функций: {available}/{len(key_functions)}")
            print(f"    🚀 main_optimized.qml v4.2 ГОТОВ К РАБОТЕ")
            
        except Exception as e:
            print(f"    ❌ КРИТИЧЕСКАЯ ОШИБКА загрузки main_optimized.qml: {e}")
            import traceback
            traceback.print_exc()
            
            # Создаем заглушку
            fallback = QLabel(
                f"❌ КРИТИЧЕСКАЯ ОШИБКА ЗАГРУЗКИ main_optimized.qml\n\n"
                f"Ошибка: {e}\n\n"
                f"Проверьте файл: assets/qml/main_optimized.qml\n"
                f"main.qml НЕ ИСПОЛЬЗУЕТСЯ!"
            )
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setStyleSheet("background: #1a1a2e; color: #ff6b6b; font-size: 12px; padding: 20px;")
            self._qquick_widget = fallback
            print(f"    ⚠️ Использована заглушка")
            return

    def _setup_legacy_opengl_view(self):
        """Setup legacy OpenGL widget - ТАКЖЕ использует main_optimized.qml"""
        print("    _setup_legacy_opengl_view: ТАКЖЕ загружаем main_optimized.qml...")
        # ✅ ИСПРАВЛЕНО: Даже для legacy используем main_optimized.qml
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
        
        # Tab 1: ГеOMETРИЯ (Geometry)
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
    @Slot(dict)
    def _on_material_changed(self, material_params: dict):
        """Обработка изменения параметров материалов от GraphicsPanel
        
        Args:
            material_params: Dictionary with material parameters
        """
        print(f"🏗️ MainWindow: Параметры материалов изменены: {material_params}")
        self.logger.info(f"Materials changed: {material_params}")
        
        # Обновляем материалы в QML сцене
        if self._qml_root_object:
            try:
                # Используем новую функцию updateMaterials
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
                        print(f"   ✅ Металл обновлен")
                    
                    if 'glass' in material_params:
                        glass = material_params['glass']
                        if 'opacity' in glass:
                            self._qml_root_object.setProperty("glassOpacity", glass['opacity'])
                        if 'ior' in glass:
                            self._qml_root_object.setProperty("glassIOR", glass['ior'])
                            print(f"   ✅ Коэффициент преломления стекла: {glass['ior']}")
                        print(f"   ✅ Стекло обновлено")
                
                self.status_bar.showMessage("Материалы обновлены")
                
            except Exception as e:
                print(f"❌ ОШИБКА обновления материалов в QML: {e}")
                self.logger.error(f"QML materials update failed: {e}")
        else:
            print(f"❌ QML root object отсутствует!")

    @Slot(dict)
    def _on_camera_changed(self, camera_params: dict):
        """Обработка изменения настроек камеры от GraphicsPanel
        
        Args:
            camera_params: Dictionary with camera parameters
        """
        print(f"📷 MainWindow: Настройки камеры изменены: {camera_params}")
        self.logger.info(f"Camera changed: {camera_params}")
        
        # Обновляем камеру в QML сцене
        if self._qml_root_object:
            try:
                # Используем новую функцию updateCamera
                if hasattr(self._qml_root_object, 'updateCamera'):
                    self._qml_root_object.updateCamera(camera_params)
                    print(f"   ✅ Камера передана в QML через updateCamera()")
                else:
                    # Fallback: прямая установка свойств
                    if 'fov' in camera_params:
                        self._qml_root_object.setProperty("cameraFov", camera_params['fov'])
                        print(f"   ✅ FOV камеры: {camera_params['fov']}")
                    if 'auto_rotate' in camera_params:
                        self._qml_root_object.setProperty("autoRotate", camera_params['auto_rotate'])
                        print(f"   ✅ Автовращение: {camera_params['auto_rotate']}")
                
                self.status_bar.showMessage("Настройки камеры обновлены")
                
            except Exception as e:
                print(f"❌ ОШИБКА обновления камеры в QML: {e}")
                self.logger.error(f"QML camera update failed: {e}")
        else:
            print(f"❌ QML root object отсутствует!")

    @Slot(dict)
    def _on_effects_changed(self, effects_params: dict):
        """Обработка изменения визуальных эффектов от GraphicsPanel
        
        Args:
            effects_params: Dictionary with effects parameters
        """
        print(f"✨ MainWindow: Визуальные эффекты изменены: {effects_params}")
        self.logger.info(f"Effects changed: {effects_params}")
        
        # Обновляем эффекты в QML сцене
        if self._qml_root_object:
            try:
                # Используем новую функцию updateEffects
                if hasattr(self._qml_root_object, 'updateEffects'):
                    self._qml_root_object.updateEffects(effects_params)
                    print(f"   ✅ Эффекты переданы в QML через updateEffects()")
                else:
                    # Fallback: прямая установка свойств
                    effect_updates = []
                    if 'bloom_enabled' in effects_params:
                        self._qml_root_object.setProperty("bloomEnabled", effects_params['bloom_enabled'])
                        effect_updates.append(f"Bloom: {effects_params['bloom_enabled']}")
                    if 'ssao_enabled' in effects_params:
                        self._qml_root_object.setProperty("ssaoEnabled", effects_params['ssao_enabled'])
                        effect_updates.append(f"SSAO: {effects_params['ssao_enabled']}")
                    if 'vignette_enabled' in effects_params:
                        self._qml_root_object.setProperty("vignetteEnabled", effects_params['vignette_enabled'])
                        effect_updates.append(f"Vignette: {effects_params['vignette_enabled']}")
                    
                    if effect_updates:
                        print(f"   ✅ Обновлены эффекты: {', '.join(effect_updates)}")
                
                self.status_bar.showMessage("Визуальные эффекты обновлены")
                
            except Exception as e:
                print(f"❌ ОШИБКА обновления эффектов в QML: {e}")
                self.logger.error(f"QML effects update failed: {e}")
        else:
            print(f"❌ QML root object отсутствует!")

    @Slot(dict)
    def _on_animation_changed(self, animation_params: dict):
        """Обработка изменения параметров анимации от ModesPanel
        
        Args:
            animation_params: Dictionary with animation parameters (amplitude, frequency, phases)
        """
        self.logger.info(f"Animation changed: {animation_params}")
        
        # Обновляем параметры анимации в QML сцене
        if self._qml_root_object:
            try:
                print(f"🔧 Setting QML animation properties: {animation_params}")
                
                # Устанавливаем параметры анимации напрямую
                if 'amplitude' in animation_params:
                    # Конвертируем амплитуду из метров в градусы для вращения рычага
                    amplitude_deg = animation_params['amplitude'] * 1000 / 10  # Масштабирующий коэффициент
                    self._qml_root_object.setProperty("userAmplitude", amplitude_deg)
                    print(f"   ✅ Set userAmplitude = {amplitude_deg} deg")
                
                if 'frequency' in animation_params:
                    self._qml_root_object.setProperty("userFrequency", animation_params['frequency'])
                    print(f"   ✅ Set userFrequency = {animation_params['frequency']} Hz")
                
                if 'phase' in animation_params:
                    self._qml_root_object.setProperty("userPhaseGlobal", animation_params['phase'])
                    print(f"   ✅ Set userPhaseGlobal = {animation_params['phase']} deg")
                
                if 'lf_phase' in animation_params:
                    self._qml_root_object.setProperty("userPhaseFL", animation_params['lf_phase'])
                    print(f"   ✅ Set userPhaseFL = {animation_params['lf_phase']} deg")
                
                if 'rf_phase' in animation_params:
                    self._qml_root_object.setProperty("userPhaseFR", animation_params['rf_phase'])
                    print(f"   ✅ Set userPhaseFR = {animation_params['rf_phase']} deg")
                
                if 'lr_phase' in animation_params:
                    self._qml_root_object.setProperty("userPhaseRL", animation_params['lr_phase'])
                    print(f"   ✅ Set userPhaseRL = {animation_params['lr_phase']} deg")
                
                if 'rr_phase' in animation_params:
                    self._qml_root_object.setProperty("userPhaseRR", animation_params['rr_phase'])
                    print(f"   ✅ Set userPhaseRR = {animation_params['rr_phase']} deg")
                
                self.status_bar.showMessage("Параметры анимации обновлены")
                print(f"✅ QML animation properties set successfully")
                    
            except Exception as e:
                self.logger.error(f"QML animation update failed: {e}")
                self.status_bar.showMessage(f"Animation update failed: {e}")
                import traceback
                traceback.print_exc()

    # =================================================================
    # Batch QML Update System (для оптимизации)
    # =================================================================
    
    def _queue_qml_update(self, update_type: str, params: dict):
        """Поставить обновление QML в очередь для группового выполнения
        
        Args:
            update_type: Тип обновления ('geometry', 'materials', 'lighting', etc.)
            params: Параметры для обновления
        """
        self._qml_update_queue[update_type] = params
        
        # Запускаем таймер для группового выполнения (если не запущен)
        if not self._qml_flush_timer.isActive():
            self._qml_flush_timer.start(50)  # 50мс задержка для группировки
    
    @Slot()
    def _flush_qml_updates(self):
        """Выполнить все накопленные обновления QML"""
        if not self._qml_update_queue or not self._qml_root_object:
            return
        
        try:
            print(f"📦 Flushing {len(self._qml_update_queue)} QML updates...")
            
            # Если есть функция applyBatchedUpdates в QML, используем её
            if hasattr(self._qml_root_object, 'applyBatchedUpdates'):
                self._qml_root_object.applyBatchedUpdates(self._qml_update_queue)
                print(f"✅ Applied batched updates via applyBatchedUpdates()")
            else:
                # Fallback: применяем обновления по одному
                for update_type, params in self._qml_update_queue.items():
                    print(f"   Applying {update_type}: {params}")
                    
                    # Применяем прямые свойства
                    for key, value in params.items():
                        try:
                            self._qml_root_object.setProperty(key, value)
                        except Exception as e:
                            print(f"     ❌ Failed to set {key}: {e}")
                
                print(f"✅ Applied {len(self._qml_update_queue)} updates individually")
            
        except Exception as e:
            print(f"❌ Error flushing QML updates: {e}")
            self.logger.error(f"QML batch update failed: {e}")
        finally:
            # Очищаем очередь
            self._qml_update_queue.clear()

    # =================================================================
    # MISSING METHODS - CRITICAL FIX
    # =================================================================
    
    def _setup_menus(self):
        """Создать меню приложения / Create application menus"""
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

        # View menu
        view_menu = menubar.addMenu("Вид")
        reset_ui_act = QAction("Сбросить интерфейс", self)
        reset_ui_act.triggered.connect(self._reset_ui_layout)
        view_menu.addAction(reset_ui_act)

        # Settings menu
        settings_menu = menubar.addMenu("Настройки")
        preferences_act = QAction("Параметры...", self)
        preferences_act.triggered.connect(self._show_preferences)
        settings_menu.addAction(preferences_act)

        # Help menu
        help_menu = menubar.addMenu("Справка")
        about_act = QAction("О программе", self)
        about_act.triggered.connect(self._show_about)
        help_menu.addAction(about_act)

    def _setup_toolbar(self):
        """Создать панель инструментов / Create toolbar"""
        toolbar = self.addToolBar("Основная")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(True)
        
        # Simulation control actions
        start_act = QAction("▶️ Старт", self)
        stop_act = QAction("⏹️ Стоп", self)
        pause_act = QAction("⏸️ Пауза", self)
        reset_act = QAction("🔄 Сброс", self)
        
        start_act.triggered.connect(lambda: self._on_sim_control("start"))
        stop_act.triggered.connect(lambda: self._on_sim_control("stop"))
        pause_act.triggered.connect(lambda: self._on_sim_control("pause"))
        reset_act.triggered.connect(lambda: self._on_sim_control("reset"))
        
        toolbar.addActions([start_act, stop_act, pause_act, reset_act])
        toolbar.addSeparator()
        
        # Toggle tabs action
        toggle_tabs_act = QAction("Скрыть/показать панели", self)
        toggle_tabs_act.setCheckable(True)
        toggle_tabs_act.setChecked(True)
        toggle_tabs_act.toggled.connect(self._toggle_tabs_visibility)
        toolbar.addAction(toggle_tabs_act)
        
        # Prevent toolbar from taking too much space
        toolbar.setMaximumHeight(50)

    def _setup_status_bar(self):
        """Создать строку состояния / Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create status bar widgets
        self.sim_time_label = QLabel("Время симуляции: 0.000с")
        self.sim_time_label.setMinimumWidth(150)
        
        self.step_count_label = QLabel("Шагов: 0")
        self.step_count_label.setMinimumWidth(80)
        
        self.fps_label = QLabel("FPS: 0")
        self.fps_label.setMinimumWidth(80)
        
        self.realtime_label = QLabel("RT: 1.00x")
        self.realtime_label.setMinimumWidth(80)
        
        self.queue_label = QLabel("Очередь: 0/0")
        self.queue_label.setMinimumWidth(100)
        
        # Add widgets to status bar
        for widget in [self.sim_time_label, self.step_count_label, self.fps_label, 
                      self.realtime_label, self.queue_label]:
            self.status_bar.addPermanentWidget(widget)
        
        self.status_bar.showMessage("Готово к работе")
        self.status_bar.setMaximumHeight(30)

    def _connect_simulation_signals(self):
        """Подключить сигналы симуляции / Connect simulation signals"""
        try:
            bus = self.simulation_manager.state_bus
            bus.state_ready.connect(self._on_state_update, Qt.ConnectionType.QueuedConnection)
            bus.physics_error.connect(self._on_physics_error, Qt.ConnectionType.QueuedConnection)
            print("✅ Сигналы симуляции подключены")
        except Exception as e:
            print(f"⚠️ Ошибка подключения сигналов симуляции: {e}")

    @Slot()
    def _update_render(self):
        """Обновить отображение / Update rendering"""
        if not self._qml_root_object:
            return
        
        try:
            # Update simulation info if available
            if hasattr(self, 'current_snapshot') and self.current_snapshot:
                sim_text = f"Время: {self.current_snapshot.simulation_time:.2f}с | Шаг: {self.current_snapshot.step_number}"
                if hasattr(self._qml_root_object, 'setProperty'):
                    self._qml_root_object.setProperty("simulationText", sim_text)
                
                # Update status bar
                self.sim_time_label.setText(f"Время симуляции: {self.current_snapshot.simulation_time:.3f}с")
                self.step_count_label.setText(f"Шагов: {self.current_snapshot.step_number}")
                
                if hasattr(self.current_snapshot, 'aggregates') and self.current_snapshot.aggregates.physics_step_time > 0:
                    fps = 1.0 / self.current_snapshot.aggregates.physics_step_time
                    self.fps_label.setText(f"FPS: {fps:.0f}")
            
            # Update queue stats if available
            if hasattr(self.simulation_manager, 'get_queue_stats'):
                try:
                    stats = self.simulation_manager.get_queue_stats()
                    self.queue_label.setText(f"Очередь: {stats.get('get_count', 0)}/{stats.get('put_count', 0)}")
                except:
                    pass
                    
        except Exception as e:
            # Fail silently to avoid spamming console
            pass

    def _restore_settings(self):
        """Восстановить настройки окна / Restore window settings"""
        try:
            settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
            
            # Restore geometry (window size and position)
            if geometry := settings.value(self.SETTINGS_GEOMETRY):
                self.restoreGeometry(geometry)
            
            # Restore window state (toolbars, dock widgets)
            if state := settings.value(self.SETTINGS_STATE):
                self.restoreState(state)
            
            # Restore splitter positions
            if hasattr(self, 'main_horizontal_splitter') and self.main_horizontal_splitter:
                if splitter_state := settings.value(self.SETTINGS_HORIZONTAL_SPLITTER):
                    self.main_horizontal_splitter.restoreState(splitter_state)
            
            if hasattr(self, 'main_splitter') and self.main_splitter:
                if splitter_state := settings.value(self.SETTINGS_SPLITTER):
                    self.main_splitter.restoreState(splitter_state)
                    
            print("✅ Настройки окна восстановлены")
        except Exception as e:
            print(f"⚠️ Не удалось восстановить настройки: {e}")

    # =================================================================
    # Event Handlers and Signal Slots
    # =================================================================

    @Slot(object)
    def _on_state_update(self, snapshot):
        """Обработка обновления состояния симуляции"""
        self.current_snapshot = snapshot
        if self.chart_widget and snapshot:
            self.chart_widget.update_from_snapshot(snapshot)

    @Slot(str)
    def _on_physics_error(self, msg: str):
        """Обработка ошибок физики"""
        self.status_bar.showMessage(f"Ошибка физики: {msg}", 5000)
        self.logger.error(f"Physics error: {msg}")

    def _toggle_tabs_visibility(self, visible: bool):
        """Переключить видимость вкладок"""
        if self.tab_widget:
            self.tab_widget.setVisible(visible)
        status_msg = "Панели показаны" if visible else "Панели скрыты"
        self.status_bar.showMessage(status_msg)

    # =================================================================
    # Menu Actions (Stubs)
    # =================================================================

    def _save_preset(self):
        """Сохранить пресет настроек (заглушка)"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Пресет", "Функция сохранения пресетов будет реализована позже")

    def _load_preset(self):
        """Загрузить пресет настроек (заглушка)"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Пресет", "Функция загрузки пресетов будет реализована позже")

    def _export_timeseries(self):
        """Экспорт временных рядов (заглушка)"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Экспорт", "Функция экспорта данных будет реализована позже")

    def _export_snapshots(self):
        """Экспорт снимков состояния (заглушка)"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Экспорт", "Функция экспорта снимков будет реализована позже")

    def _reset_ui_layout(self):
        """Сбросить макет интерфейса (заглушка)"""
        self.status_bar.showMessage("Макет интерфейса сброшен")

    def _show_preferences(self):
        """Показать окно настроек (заглушка)"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Настройки", "Окно настроек будет реализовано позже")

    def _show_about(self):
        """Показать окно 'О программе'"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "О программе PneumoStabSim",
            "PneumoStabSim Professional v2.0.1\n\n"
            "Симулятор пневматических стабилизаторов\n"
            "с улучшенной 3D визуализацией и поддержкой терминала\n\n"
            "© 2025 PneumoStabSim Project"
        )

    # =================================================================
    # Window Events and Cleanup
    # =================================================================

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        try:
            self.logger.info("Main window closing")
            
            # Stop render timer
            if hasattr(self, 'render_timer'):
                self.render_timer.stop()
            
            # Save settings
            self._save_settings()
            
            # Stop simulation manager
            if hasattr(self, 'simulation_manager'):
                self.simulation_manager.stop()
            
            event.accept()
            self.logger.info("Main window closed successfully")
        except Exception as e:
            self.logger.error(f"Error during window close: {e}")
            event.accept()  # Close anyway

    def _save_settings(self):
        """Сохранить настройки окна"""
        try:
            settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
            settings.setValue(self.SETTINGS_GEOMETRY, self.saveGeometry())
            settings.setValue(self.SETTINGS_STATE, self.saveState())
            
            # Save splitter states
            if hasattr(self, 'main_horizontal_splitter') and self.main_horizontal_splitter:
                settings.setValue(self.SETTINGS_HORIZONTAL_SPLITTER, self.main_horizontal_splitter.saveState())
            
            if hasattr(self, 'main_splitter') and self.main_splitter:
                settings.setValue(self.SETTINGS_SPLITTER, self.main_splitter.saveState())
                
            print("✅ Настройки окна сохранены")
        except Exception as e:
            print(f"⚠️ Не удалось сохранить настройки: {e}")

    def showEvent(self, event):
        """Переопределение showEvent для запуска SimulationManager ПОСЛЕ отображения окна"""
        super().showEvent(event)
        
        # Запускаем simulation manager только один раз, после отображения окна
        if not self._sim_started:
            print("\n🚀 Окно отображено - запуск SimulationManager...")
            try:
                self.simulation_manager.start()
                self._sim_started = True
                print("✅ SimulationManager запущен успешно\n")
            except Exception as e:
                print(f"❌ Не удалось запустить SimulationManager: {e}")
                import traceback
                traceback.print_exc()

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        try:
            self.logger.info("Main window closing")
            
            # Stop render timer
            if hasattr(self, 'render_timer'):
                self.render_timer.stop()
            
            # Save settings
            self._save_settings()
            
            # Stop simulation manager
            if hasattr(self, 'simulation_manager'):
                self.simulation_manager.stop()
            
            event.accept()
            self.logger.info("Main window closed successfully")
        except Exception as e:
            self.logger.error(f"Error during window close: {e}")
            event.accept()  # Close anyway
