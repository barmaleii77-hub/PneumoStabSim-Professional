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

    def __init__(self, use_qml_3d: bool = True, force_optimized: bool = False):
        super().__init__()
        
        # Store visualization backend choice
        self.use_qml_3d = use_qml_3d
        self.force_optimized = force_optimized  # NEW: Force main_optimized.qml
        
        backend_name = "Qt Quick 3D (U-Рама PBR)" if use_qml_3d else "Legacy OpenGL"
        if force_optimized:
            backend_name += " OPTIMIZED"
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
        """Setup Qt Quick 3D full suspension scene"""
        print("    [QML] Загрузка QML файла...")
        
        try:
            self._qquick_widget = QQuickWidget(self)
            self._qquick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
            
            # ✅ ИЗМЕНЕНО: Выбор QML файла - теперь расширенная версия по умолчанию
            if self.force_optimized:
                print(f"    🚀 ПРИНУДИТЕЛЬНЫЙ РЕЖИМ: Обязательная загрузка main_optimized.qml")
                qml_path = Path("assets/qml/main_optimized.qml")
                allow_fallback = False  # В принудительном режиме fallback запрещен
            else:
                print(f"    🌟 АВТОМАТИЧЕСКИЙ РЕЖИМ: Загрузка РАСШИРЕННОЙ версии с IBL системой")
                qml_path = Path("assets/qml/main.qml")  # Расширенная версия теперь по умолчанию
                allow_fallback = True   # Разрешен fallback к main_optimized.qml
            
            print(f"    🔍 ДИАГНОСТИКА ЗАГРУЗКИ QML:")
            print(f"       Целевой файл: {qml_path}")
            print(f"       Файл существует: {qml_path.exists()}")
            print(f"       Fallback разрешен: {allow_fallback}")
            
            if qml_path.exists():
                try:
                    # Проверяем размер файла для дополнительной валидации
                    file_size = qml_path.stat().st_size
                    print(f"       Размер файла: {file_size:,} байт")
                    
                    if qml_path.name == "main.qml":
                        if file_size > 30000:  # main.qml должен быть достаточно большим с IBL
                            print(f"    ✅ Загружаем РАСШИРННУЮ версию с IBL системой!")
                            qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
                        else:
                            raise ValueError(f"Расширенный файл слишком мал ({file_size} байт), возможно поврежден")
                    else:  # main_optimized.qml
                        if file_size > 50000:  # main_optimized.qml должен быть ~57KB
                            print(f"    ✅ Загружаем ОПТИМИЗИРОВАННУЮ версию (v4.1)!")
                            qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
                        else:
                            raise ValueError(f"Оптимизированный файл слишком мал ({file_size} байт), возможно поврежден")
                    
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
            if extended_props >= 1 or len(extended_functions) >= 1:
                print(f"    🌟 ПОДТВЕРДЖДЕНО: загружена РАСШИРЕННАЯ версия с IBL системой!")
                print(f"    ✨ Доступны возможности: IBL система, улучшенные pointer handlers, оптимизированные материалы")
                print(f"    🎨 Поддержка: ExtendedSceneEnvironment, HDR загрузка, современные эффекты")
            elif len(available_functions) >= 8 and optimized_props >= 1:
                print(f"    🚀 ПОДТВЕРДЖДЕНО: загружена ОПТИМИЗИРОВАННАЯ версия (v4.1)")
                print(f"    ✨ Доступны расширенные возможности: IBL, туман, продвинутые эффекты")
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
            
            print(f"    [ERROR] Ошибка загрузки основного файла: {e}")
            print(f"    🔄 Переключаемся на fallback: main_optimized.qml")
            
            # Fallback к оптимизированной версии (только если разрешен)
            try:
                fallback_path = Path("assets/qml/main_optimized.qml")
                
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
                
                print(f"    [FALLBACK] ✅ Загружен main_optimized.qml как запасной вариант")
                print(f"    📝 Используется оптимизированная версия")
                
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

    # Остальные методы продолжают здесь...
