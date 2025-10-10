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

    def __init__(self, use_qml_3d: bool = True, force_optimized: bool = False):
        super().__init__()
        
        # Store visualization backend choice
        self.use_qml_3d = use_qml_3d
        self.force_optimized = force_optimized
        
        backend_name = "Qt Quick 3D (Оптимизированная v4.1+)" if use_qml_3d else "Legacy OpenGL"
        if force_optimized:
            backend_name += " ПРИНУДИТЕЛЬНЫЙ"
        else:
            backend_name += " ОСНОВНАЯ"
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
        """Setup Qt Quick 3D full suspension scene"""
        print("    [QML] Загрузка QML файла...")
        
        try:
            self._qquick_widget = QQuickWidget(self)
            self._qquick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
            
            # ✅ ИЗМЕНЕНО: main_optimized.qml теперь ОСНОВНОЙ файл по умолчанию
            if self.force_optimized:
                print(f"    🚀 ПРИНУДИТЕЛЬНЫЙ РЕЖИМ: Обязательная загрузка main_optimized.qml")
                qml_path = Path("assets/qml/main_optimized.qml")
                allow_fallback = False  # В принудительном режиме fallback запрещен
            else:
                print(f"    🌟 ОСНОВНОЙ РЕЖИМ: Загрузка main_optimized.qml по умолчанию (последняя версия)")
                qml_path = Path("assets/qml/main_optimized.qml")  # ТЕПЕРЬ ОСНОВННОЙ ФАЙЛ!
                allow_fallback = True   # Разрешен fallback к main.qml только как запасной вариант
            
            print(f"    🔍 ДИАГНОСТИКА ЗАГРУЗКИ QML:")
            print(f"       Целевой файл: {qml_path}")
            print(f"       Файл существует: {qml_path.exists()}")
            print(f"       Fallback разрешен: {allow_fallback}")
            
            if qml_path.exists():
                try:
                    # Проверяем размер файла для дополнительной валидации
                    file_size = qml_path.stat().st_size
                    print(f"       Размер файла: {file_size:,} байт")
                    
                    if qml_path.name == "main_optimized.qml":
                        if file_size > 50000:  # main_optimized.qml должен быть ~57KB+
                            print(f"    ✅ Загружаем ОПТИМИЗИРОВАННУЮ версию (основная версия)!")
                            qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
                        else:
                            raise ValueError(f"Оптимизированный файл слишком мал ({file_size} байт), возможно поврежден")
                    else:  # main.qml (теперь fallback)
                        if file_size > 30000:  # main.qml должен быть достаточно большим с IBL
                            print(f"    ✅ Загружаем РАСШИРЕННУЮ версию (fallback)!")
                            qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
                        else:
                            raise ValueError(f"Расширенный файл слишком мал ({file_size} байт), возможно поврежден")
                    
                    print(f"    📂 Полный путь: {qml_url.toString()}")
                    print(f"    🚀 Файл: {qml_path.name}")
                        
                except Exception as file_error:
                    print(f"    ⚠️ Ошибка проверки файла {qml_path.name}: {file_error}")
                    if not allow_fallback:
                        print(f"    ❌ ПРИНУДИТЕЛЬНЫЙ РЕЖИМ: Fallback запрещен!")
                        raise file_error
                    else:
                        raise file_error  # Пробрасываем для fallback
                        
            else:
                error_msg = f"Файл {qml_path.name} не найден"
                if not allow_fallback:
                    print(f"    ❌ ПРИНУДИТЕЛЬНЫЙ РЕЖИМ: {error_msg}")
                    raise FileNotFoundError(error_msg)
                else:
                    raise FileNotFoundError(error_msg)  # Пробрасываем для fallback
            
            # Пытаемся загрузить выбранный файл
            print(f"    🔄 Устанавливаем source: {qml_url.toString()}")
            self._qquick_widget.setSource(qml_url)
            
            # Проверяем статус загрузки
            status = self._qquick_widget.status()
            print(f"    📊 QML статус загрузки: {status}")
            
            if status == QQuickWidget.Status.Error:
                errors = self._qquick_widget.errors()
                error_messages = [str(e) for e in errors]
                error_msg = "\n".join(error_messages)
                print(f"    ❌ ОШИБКИ QML ЗАГРУЗКИ:")
                for i, error in enumerate(error_messages, 1):
                    print(f"       {i}. {error}")
                
                if not allow_fallback:
                    print(f"    ❌ ПРИНУДИТЕЛЬНЫЙ РЕЖИМ: Прерывание из-за ошибок QML")
                    raise RuntimeError(f"Ошибки загрузки QML (принудительный режим):\n{error_msg}")
                else:
                    raise RuntimeError(f"Ошибки загрузки QML:\n{error_msg}")
                    
            elif status == QQuickWidget.Status.Loading:
                print(f"    ⏳ QML файл загружается...")
            elif status == QQuickWidget.Status.Ready:
                print(f"    ✅ QML файл загружен успешно!")
            
            # Получаем корневой объект
            self._qml_root_object = self._qquick_widget.rootObject()
            if not self._qml_root_object:
                error_msg = "Не удалось получить корневой объект QML"
                if not allow_fallback:
                    print(f"    ❌ ПРИНУДИТЕЛЬНЫЙ РЕЖИМ: {error_msg}")
                    raise RuntimeError(error_msg)
                else:
                    raise RuntimeError(error_msg)
            
            print(f"    [OK] ✅ QML файл '{qml_path.name}' загружен успешно")

            if self._qml_update_queue:
                self._flush_qml_updates
            
            # Проверяем доступные свойства для диагностики
            critical_properties = ['glassIOR', 'userFrameLength', 'bloomEnabled', 'metalRoughness', 'iblEnabled', 'fogEnabled', 'iblTextureReady']
            print(f"    🔍 ДИАГНОСТИКА критических свойств:")
            optimized_props = 0
            extended_props = 0
            for prop in critical_properties:
                try:
                    if hasattr(self._qml_root_object, 'property'):
                        value = self._qml_root_object.property(prop)
                        print(f"    ✅ {prop}: {value}")
                        if prop in ['iblEnabled', 'fogEnabled']:
                            optimized_props += 1  # Эти свойства есть в обеих версиях
                        if prop in ['iblTextureReady'] and value is not None:
                            extended_props += 1  # Это свойство только в расширенной версии
                    else:
                        print(f"    ❌ {prop}: property() метод недоступен")
                except Exception as e:
                    print(f"    ❌ {prop}: ошибка - {e}")
            
            # Проверяем функции обновления (расширенный список для версий)
            update_functions = [
                'updateGeometry', 'updateMaterials', 'updateLighting', 'updateEffects', 
                'updateEnvironment', 'updateQuality', 'updateCamera',
                'applyBatchedUpdates', 'applyGeometryUpdates', 'applyMaterialUpdates',
                'resolvedTonemapMode'  # Функция только в расширенной версии
            ]
            print(f"    🔍 ДИАГНОСТИКА функций обновления:")
            available_functions = []
            extended_functions = []
            for func_name in update_functions:
                try:
                    if hasattr(self._qml_root_object, func_name):
                        print(f"    ✅ Функция {func_name}() доступна")
                        available_functions.append(func_name)
                        if func_name in ['resolvedTonemapMode']:
                            extended_functions.append(func_name)
                    else:
                        print(f"    ❌ Функция {func_name}() не найдена!")
                except Exception as e:
                    print(f"    ❌ Функция {func_name}(): ошибка - {e}")
            
            print(f"    📊 ИТОГО доступно функций: {len(available_functions)}/{len(update_functions)}")
            
            # Определяем версию по количеству доступных функций и свойств
            if len(available_functions) >= 10 and optimized_props >= 1:
                print(f"    🚀 ПОДТВЕРДЖДЕНО: загружена ОПТИМИЗИРОВАННАЯ версия (v4.1+) - ОСНОВНАЯ ВЕРСИЯ!")
                print(f"    ✨ Доступны возможности: IBL, туман, продвинутые эффекты, полная совместимость")
                print(f"    🎨 Поддержка: Все современные функции GraphicsPanel, коэффициент преломления")
            elif extended_props >= 1 or len(extended_functions) >= 1:
                print(f"    🌟 ПОДТВЕРДЖДЕНО: загружена РАСШИРЕННАЯ версия с IBL системой (fallback)!")
                print(f"    ✨ Доступны возможности: IBL система, улучшенные pointer handlers, оптимизированные материалы")
                print(f"    🎨 Поддержка: ExtendedSceneEnvironment, HDR загрузка, современные эффекты")
            elif len(available_functions) >= 5:
                print(f"    ⚠️ ВНИМАНИЕ: загружена БАЗОВАЯ версия (v2.1)")
                print(f"    📝 Некоторые расширенные функции недоступны")
            else:
                print(f"    ❌ КРИТИЧНО: версия неопределена или повреждена")
            
        except Exception as e:
            if not allow_fallback:
                print(f"    [CRITICAL] ПРИНУДИТЕЛЬНЫЙ РЕЖИМ: Ошибка загрузки обязательна")
                print(f"    ❌ Ошибка: {e}")
                import traceback
                traceback.print_exc()
                raise e  # Прерываем выполнение
            
            print(f"    [ERROR] Ошибка загрузки основного файла main_optimized.qml: {e}")
            print(f"    🔄 Переключаемся на fallback: main.qml")
            
            # Fallback к расширенной версии (только если разрешен)
            try:
                fallback_path = Path("assets/qml/main.qml")
                
                if not fallback_path.exists():
                    raise FileNotFoundError(f"Fallback файл не найден: {fallback_path}")
                
                qml_url = QUrl.fromLocalFile(str(fallback_path.absolute()))
                print(f"    📂 Fallback путь: {qml_url.toString()}")
                
                self._qquick_widget.setSource(qml_url)
                
                if self._qquick_widget.status() == QQuickWidget.Status.Error:
                    errors = self._qquick_widget.errors()
                    error_msg = "\n".join(str(e) for e in errors)
                    raise RuntimeError(f"Ошибки fallback QML:\n{error_msg}")
                
                self._qml_root_object = self._qquick_widget.rootObject()
                if not self._qml_root_object:
                    raise RuntimeError("Не удалось получить корневой объект fallback QML")
                
                print(f"    [FALLBACK] ✅ Загружен main.qml как запасной вариант")
                print(f"    📝 Используется расширенная версия с IBL")
                
            except Exception as fallback_error:
                print(f"    [CRITICAL] Ошибка fallback загрузки: {fallback_error}")
                import traceback
                traceback.print_exc()
                
                # Создаем заглушку вместо падения приложения
                fallback = QLabel(
                    "КРИТИЧЕСКАЯ ОШИБКА ЗАГРУЗКИ 3D СЦЕНЫ\n\n"
                    f"Основная: {e}\n"
                    f"Fallback: {fallback_error}\n\n"
                    "Проверьте файлы assets/qml/main*.qml\n"
                    f"Режим: {'ПРИНУДИТЕЛЬНЫЙ' if not allow_fallback else 'АВТОМАТИЧЕСКИЙ'}"
                )
                fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
                fallback.setStyleSheet("background: #1a1a2e; color: #ff6b6b; font-size: 12px; padding: 20px;")
                self._qquick_widget = fallback
                print(f"    [WARNING] Использован заглушка-виджет")
                return

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
        """Обработчик изменения геометрии для отправки в QML
        
        Args:
            geometry_params: Словарь с параметрами геометрии из GeometryPanel
        """
        print(f"═══════════════════════════════════════════════")
        print(f"🔺 MainWindow: Получен сигнал geometry_changed от панели")
        print(f"   Параметры ({len(geometry_params)}): {list(geometry_params.keys())}")
        
        # Показываем ключевые значения для диагностики
        key_params = ['frameLength', 'leverLength', 'trackWidth', 'rodPosition']
        print(f"   Ключевые значения:")
        for key in key_params:
            if key in geometry_params:
                print(f"      {key} = {geometry_params[key]}")
        print(f"═══════════════════════════════════════════════")
        
        self.logger.info(f"Геометрия изменена: {len(geometry_params)} параметров")
        
        # Обновляем QML сцену прямо сейчас
        if self._qml_root_object:
            try:
                print(f"   🔧 Вызываем updateGeometry() в QML...")
                
                # Используем QMetaObject.invokeMethod() для вызова QML функции
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt
                
                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "updateGeometry",
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", geometry_params)
                )
                
                if success:
                    print(f"   ✅ QML updateGeometry() вызван успешно")
                    
                    # Принудительно обновляем QML widget для немедленного отображения
                    if self._qquick_widget:
                        self._qquick_widget.update()
                        print(f"   🔄 QML widget принудительно обновлен")
                    
                    self.status_bar.showMessage("Геометрия обновлена в 3D сцене")
                    print(f"📊 Статус: Геометрия успешно обновлена")
                else:
                    print(f"   ❌ QML updateGeometry() не удалось вызвать")
                    # Fallback к установке отдельных свойств
                    self._set_geometry_properties_fallback(geometry_params)
                    
            except Exception as e:
                print(f"═══════════════════════════════════════════════")
                print(f"❌ Ошибка обновления геометрии в QML!")
                print(f"   Ошибка: {e}")
                print(f"═══════════════════════════════════════════════")
                self.logger.error(f"Ошибка обновления геометрии в QML: {e}")
                self.status_bar.showMessage(f"Ошибка обновления геометрии: {e}")
                import traceback
                traceback.print_exc()
                
                # Fallback к установке отдельных свойств
                self._set_geometry_properties_fallback(geometry_params)
        else:
            print(f"═══════════════════════════════════════════════")
            print(f"❌ MainWindow: QML корневой объект недоступен!")
            print(f"   Невозможно обновить геометрию")
            print(f"═══════════════════════════════════════════════")
            self.status_bar.showMessage("QML недоступен для обновления геометрии")
    
    def _set_geometry_properties_fallback(self, geometry_params: dict):
        """Fallback: Установка отдельных QML свойств напрямую
        
        Args:
            geometry_params: Словарь с параметрами геометрии
        """
        print(f"🔧 Fallback: Установка отдельных QML свойств...")
        
        prop_count = 0
        
        # Конвертируем и устанавливаем основные свойства
        if 'frameLength' in geometry_params:
            self._qml_root_object.setProperty("userFrameLength", geometry_params['frameLength'])
            print(f"   ✅ Set userFrameLength = {geometry_params['frameLength']}")
            prop_count += 1
        
        if 'frameHeight' in geometry_params:
            self._qml_root_object.setProperty("userFrameHeight", geometry_params['frameHeight'])
            print(f"   ✅ Set userFrameHeight = {geometry_params['frameHeight']}")
            prop_count += 1
        
        if 'frameBeamSize' in geometry_params:
            self._qml_root_object.setProperty("userBeamSize", geometry_params['frameBeamSize'])
            print(f"   ✅ Set userBeamSize = {geometry_params['frameBeamSize']}")
            prop_count += 1
        
        if 'leverLength' in geometry_params:
            self._qml_root_object.setProperty("userLeverLength", geometry_params['leverLength'])
            print(f"   ✅ Set userLeverLength = {geometry_params['leverLength']}")
            prop_count += 1
        
        if 'cylinderBodyLength' in geometry_params:
            self._qml_root_object.setProperty("userCylinderLength", geometry_params['cylinderBodyLength'])
            print(f"   ✅ Set userCylinderLength = {geometry_params['cylinderBodyLength']}")
            prop_count += 1
        
        if 'trackWidth' in geometry_params:
            self._qml_root_object.setProperty("userTrackWidth", geometry_params['trackWidth'])
            print(f"   ✅ Set userTrackWidth = {geometry_params['trackWidth']}")
            prop_count += 1
        
        if 'frameToPivot' in geometry_params:
            self._qml_root_object.setProperty("userFrameToPivot", geometry_params['frameToPivot'])
            print(f"   ✅ Set userFrameToPivot = {geometry_params['frameToPivot']}")
            prop_count += 1
        
        if 'rodPosition' in geometry_params:
            self._qml_root_object.setProperty("userRodPosition", geometry_params['rodPosition'])
            print(f"   ✅ Set userRodPosition = {geometry_params['rodPosition']}")
            prop_count += 1
        
        if 'boreHead' in geometry_params:
            self._qml_root_object.setProperty("userBoreHead", geometry_params['boreHead'])
            print(f"   ✅ Set userBoreHead = {geometry_params['boreHead']}")
            prop_count += 1
        
        if 'boreRod' in geometry_params:
            self._qml_root_object.setProperty("userBoreRod", geometry_params['boreRod'])
            print(f"   ✅ Set userBoreRod = {geometry_params['boreRod']}")
            prop_count += 1
        
        if 'rodDiameter' in geometry_params:
            self._qml_root_object.setProperty("userRodDiameter", geometry_params['rodDiameter'])
            print(f"   ✅ Set userRodDiameter = {geometry_params['rodDiameter']}")
            prop_count += 1
        
        if 'pistonThickness' in geometry_params:
            self._qml_root_object.setProperty("userPistonThickness", geometry_params['pistonThickness'])
            print(f"   ✅ Set userPistonThickness = {geometry_params['pistonThickness']}")
            prop_count += 1
        
        if 'pistonRodLength' in geometry_params:
            self._qml_root_object.setProperty("userPistonRodLength", geometry_params['pistonRodLength'])
            print(f"   ✅ Set userPistonRodLength = {geometry_params['pistonRodLength']}")
            prop_count += 1
        
        # Принудительно обновляем виджет
        if self._qquick_widget:
            self._qquick_widget.update()
        
        self.status_bar.showMessage(f"Геометрия обновлена через свойства ({prop_count} параметров)")
        print(f"✅ Установлено {prop_count} QML свойств через fallback")
        print(f"═══════════════════════════════════════════════")

    @Slot(dict)
    def _on_lighting_changed(self, lighting_params: dict):
        """Обработчик изменения параметров освещения"""
        print(f"💡 MainWindow: Lighting changed: {lighting_params}")
        
        if self._qml_root_object:
            try:
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt
                
                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "updateLighting",
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", lighting_params)
                )
                
                if success:
                    self.status_bar.showMessage("Освещение обновлено")
                else:
                    print("❌ Failed to call updateLighting()")
                    
            except Exception as e:
                self.logger.error(f"Lighting update failed: {e}")
    
    @Slot(dict)
    def _on_material_changed(self, material_params: dict):
        """Обработчик изменения параметров материалов"""
        print(f"🎨 MainWindow: Material changed: {material_params}")
        
        if self._qml_root_object:
            try:
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt
                
                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "updateMaterials",
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", material_params)
                )
                
                if success:
                    self.status_bar.showMessage("Материалы обновлены")
                else:
                    print("❌ Failed to call updateMaterials()")
                    
            except Exception as e:
                self.logger.error(f"Material update failed: {e}")
    
    @Slot(dict) 
    def _on_environment_changed(self, environment_params: dict):
        """Обработчик изменения параметров окружения"""
        print(f"🌍 MainWindow: Environment changed: {environment_params}")
        
        if self._qml_root_object:
            try:
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt
                
                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "updateEnvironment",
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", environment_params)
                )
                
                if success:
                    self.status_bar.showMessage("Окружение обновлено")
                else:
                    print("❌ Failed to call updateEnvironment()")
                    
            except Exception as e:
                self.logger.error(f"Environment update failed: {e}")
    
    @Slot(dict)
    def _on_quality_changed(self, quality_params: dict):
        """Обработчик изменения параметров качества"""
        print(f"⚙️ MainWindow: Quality changed: {quality_params}")
        
        if self._qml_root_object:
            try:
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt
                
                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "updateQuality",
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", quality_params)
                )
                
                if success:
                    self.status_bar.showMessage("Качество обновлено")
                else:
                    print("❌ Failed to call updateQuality()")
                    
            except Exception as e:
                self.logger.error(f"Quality update failed: {e}")
    
    @Slot(dict)
    def _on_camera_changed(self, camera_params: dict):
        """Обработчик изменения параметров камеры"""
        print(f"📷 MainWindow: Camera changed: {camera_params}")
        
        if self._qml_root_object:
            try:
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt
                
                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "updateCamera",
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", camera_params)
                )
                
                if success:
                    self.status_bar.showMessage("Камера обновлена")
                else:
                    print("❌ Failed to call updateCamera()")
                    
            except Exception as e:
                self.logger.error(f"Camera update failed: {e}")
    
    @Slot(dict)
    def _on_effects_changed(self, effects_params: dict):
        """Обработчик изменения параметров эффектов"""
        print(f"✨ MainWindow: Effects changed: {effects_params}")
        
        if self._qml_root_object:
            try:
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt
                
                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "updateEffects",
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", effects_params)
                )
                
                if success:
                    self.status_bar.showMessage("Эффекты обновлены")
                else:
                    print("❌ Failed to call updateEffects()")
                    
            except Exception as e:
                self.logger.error(f"Effects update failed: {e}")
    
    @Slot(str)
    def _on_preset_applied(self, preset_name: str):
        """Обработчик применения пресета графики"""
        print(f"🎯 MainWindow: Graphics preset applied: {preset_name}")
        self.status_bar.showMessage(f"Пресет '{preset_name}' применен")
    
    @Slot(dict)
    def _on_animation_changed(self, animation_params: dict):
        """Обработчик изменения параметров анимации от ModesPanel
        
        Args:
            animation_params: Словарь с параметрами анимации
        """
        print(f"🎬 MainWindow: Animation parameters changed: {animation_params}")
        self.logger.info(f"Параметры анимации изменены: {animation_params}")
        
        # Обновляем QML свойства анимации, если доступны
        if self._qml_root_object:
            try:
                print(f"🔧 Установка свойств анимации в QML: {animation_params}")
                
                # Устанавливаем свойства анимации напрямую (QML будет реагировать через property bindings)
                if 'amplitude' in animation_params:
                    # Конвертируем амплитуду из метров в градусы для визуального эффекта
                    amplitude_deg = animation_params['amplitude'] * 1000 / 10  # Коэффициент масштабирования
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
                print(f"✅ QML свойства анимации установлены успешно")
                    
            except Exception as e:
                self.logger.error(f"Ошибка обновления анимации в QML: {e}")
                self.status_bar.showMessage(f"Ошибка обновления анимации: {e}")
                import traceback
                traceback.print_exc()
    
    @Slot(str)
    def _on_sim_control(self, command: str):
        """Обработчик команд управления симуляцией"""
        bus = self.simulation_manager.state_bus

        if command == "start":
            bus.start_simulation.emit()
            self.is_simulation_running = True
            if self._qml_root_object:
                self._qml_root_object.setProperty("isRunning", True)
                print("✅ QML анимация ЗАПУЩЕНА")
        elif command == "stop":
            bus.stop_simulation.emit()
            self.is_simulation_running = False
            if self._qml_root_object:
                self._qml_root_object.setProperty("isRunning", False)
                print("✅ QML анимация ОСТАНОВЛЕНА")
        elif command == "reset":
            bus.reset_simulation.emit()
            if self._qml_root_object:
                self._qml_root_object.setProperty("animationTime", 0.0)
                print("✅ QML анимация СБРОШЕНА")
        elif command == "pause":
            bus.pause_simulation.emit()
            if self._qml_root_object:
                self._qml_root_object.setProperty("isRunning", False)
                print("✅ QML анимация ПРИОСТАНОВЛЕНА")
        
        self.status_bar.showMessage(f"Симуляция: {command}")
        if self.modes_panel:
            self.modes_panel.set_simulation_running(self.is_simulation_running)

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

    def _set_geometry_properties_fallback(self, geometry_params: Dict[str, Any]):
        if not self._qml_root_object:
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
                self._qml_root_object.setProperty(prop, float(geometry_params[key]))

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
