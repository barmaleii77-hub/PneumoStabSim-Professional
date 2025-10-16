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
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from src.ui.charts import ChartWidget
from src.ui.panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel, GraphicsPanel
from ..runtime import SimulationManager, StateSnapshot
from .ibl_logger import get_ibl_logger, log_ibl_event  # ✅ НОВОЕ: Импорт IBL логгера
# ✅ НОВОЕ: EventLogger для логирования QML вызовов
from src.common.event_logger import get_event_logger, EventType


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
        "animation": ("applyAnimationUpdates", "updateAnimation",
                      "applyAnimParamsUpdates", "updateAnimParams"),
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
        
        # ✅ НОВОЕ: Инициализация IBL Signal Logger
        self.ibl_logger = get_ibl_logger()
        log_ibl_event("INFO", "MainWindow", "IBL Logger initialized")
        
        # ✅ НОВОЕ: Инициализируем EventLogger (Python↔QML)
        self.event_logger = get_event_logger()
        self.logger.info("EventLogger initialized in MainWindow")
        
        self.logger.info("MainWindow: Создание SimulationManager...")
        
        # Simulation manager
        try:
            self.simulation_manager = SimulationManager(self)
            self.logger.info("✅ SimulationManager создан (не запущен)")
        except Exception as e:
            self.logger.exception(f"❌ Ошибка создания SimulationManager: {e}")
            raise

        # QML update system
        self._qml_update_queue: Dict[str, Dict[str, Any]] = {}
        self._qml_method_support: Dict[tuple[str, bool], bool] = {}
        self._qml_flush_timer = QTimer()
        self._qml_flush_timer.setSingleShot(True)
        self._qml_flush_timer.timeout.connect(self._flush_qml_updates)
        self._qml_pending_property_supported: Optional[bool] = None
        self._last_batched_updates: Optional[Dict[str, Any]] = None

        # State tracking
        self.current_snapshot: Optional[StateSnapshot] = None
        self.is_simulation_running = False
        self._sim_started = False

        # Geometry converter for Python↔QML integration
        from src.ui.geometry_bridge import create_geometry_converter
        self.geometry_converter = create_geometry_converter()
        self.logger.info("✅ GeometryBridge создан для интеграции Python↔QML")

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

        self.logger.info("MainWindow: Построение UI...")
        
        # Build UI
        self._setup_central()
        self.logger.info("  ✅ Центральный вид Qt Quick 3D настроен")
        
        self._setup_tabs()
        self.logger.info("  ✅ Вкладки настроены")
        
        self._setup_menus()
        self.logger.info("  ✅ Меню настроено")
        
        self._setup_toolbar()
        self.logger.info("  ✅ Панель инструментов настроена")
        
        self._setup_status_bar()
        self.logger.info("  ✅ Строка состояния настроена")
        
        self._connect_simulation_signals()
        self.logger.info("  ✅ Сигналы подключены")

        # Render timer (UI thread ~60 FPS)
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self._update_render)
        self.render_timer.start(16)
        self.logger.info("  ✅ Таймер рендеринга запущен")

        self.logger.info("  ⏸️  SimulationManager запустится после window.show()")

        # Restore settings
        self._restore_settings()
        self.logger.info("  ✅ Настройки восстановлены")

        # ✅ Полная начальная синхронизация, чтобы убрать скрытые дефолты в QML
        self._initial_full_sync()
        self.logger.info("  ✅ Initial full sync completed")

        self.logger.info("Главное окно (Qt Quick 3D) инициализировано")
        self.logger.info("✅ MainWindow.__init__() завершён")

    @Slot(str, str)
    def logQmlEvent(self, event_type: str, name: str) -> None:
        """Слот для QML: регистрирует событие в EventLogger.

        Args:
            event_type: Тип события (например, "signal_received", "function_called")
            name: Имя сигнала/функции
        """
        try:
            etype_norm = (event_type or "").strip().lower()
            if etype_norm == "signal_received":
                etype = EventType.SIGNAL_RECEIVED
            elif etype_norm == "function_called":
                etype = EventType.FUNCTION_CALLED
            elif etype_norm == "property_changed":
                etype = EventType.PROPERTY_CHANGED
            else:
                etype = EventType.FUNCTION_CALLED

            self.event_logger.log_event(
                event_type=etype,
                component="main.qml",
                action=name,
                source="qml",
            )
        except Exception:
            # Защита от любых ошибок в логировании
            pass

    # ------------------------------------------------------------------
    # UI Construction - НОВАЯ СТРУКРАА!
    # ------------------------------------------------------------------
    def _setup_central(self):
        """Создать центральный вид с горизонтальным и вертикальным сплиттерами
        
        Create central view with horizontal and vertical splitters:
        Layout: [3D Scene (top) + Charts (bottom)] | [Control Panels (right)]
        """
        self.logger.debug("_setup_central: Создание системы сплиттеров...")
        
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
        
        self.logger.debug("✅ Система сплиттеров создана (горизонтальный + вертикальный)")

    def _setup_qml_3d_view(self):
        """Setup Qt Quick 3D full suspension scene - теперь загружает ЕДИНЫЙ main.qml"""
        self.logger.info("    [QML] Загрузка ЕДИНОГО QML файла main.qml...")
        
        try:
            self._qquick_widget = QQuickWidget(self)
            self._qquick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
            
            # CRITICAL: Set up QML import paths BEFORE loading any QML
            engine = self._qquick_widget.engine()
            
            # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Устанавливаем контекст ДО загрузки QML!
            context = engine.rootContext()
            context.setContextProperty("window", self)  # Экспонируем MainWindow в QML
            log_ibl_event("INFO", "MainWindow", "IBL Logger registered in QML context (BEFORE QML load)")
            self.logger.info("    ✅ IBL Logger context registered BEFORE QML load")

            # ✅ СИНХРОНИЗАЦИЯ СТАРТОВЫХ ПАРАМЕТРОВ IBL/ФОНА (из сохранённых настроек GraphicsPanel)
            try:
                gp_settings = QSettings("PneumoStabSim", "GraphicsPanel")
                env_raw = gp_settings.value("state/environment", None)
                if env_raw:
                    try:
                        env_state = json.loads(env_raw)
                        def _ctx(name: str, value):
                            context.setContextProperty(name, value)
                            self.logger.debug(f"    🔗 Context property set: {name} = {value}")
                        # Источники HDR
                        if isinstance(env_state.get("ibl_source"), str) and env_state.get("ibl_source"):
                            _ctx("startIblSource", env_state.get("ibl_source"))
                        if isinstance(env_state.get("ibl_fallback"), str) and env_state.get("ibl_fallback"):
                            _ctx("startIblFallback", env_state.get("ibl_fallback"))
                        # Режимы фона / флаги
                        if env_state.get("background_mode"):
                            _ctx("startBackgroundMode", env_state.get("background_mode"))
                        if "ibl_enabled" in env_state:
                            _ctx("startIblEnabled", bool(env_state.get("ibl_enabled")))
                        if "skybox_enabled" in env_state:
                            _ctx("startSkyboxEnabled", bool(env_state.get("skybox_enabled")))
                        # Доп.параметры
                        if "ibl_intensity" in env_state:
                            _ctx("startIblIntensity", float(env_state.get("ibl_intensity")))
                        if "ibl_rotation" in env_state:
                            _ctx("startIblRotation", float(env_state.get("ibl_rotation")))
                    except Exception as ex:
                        self.logger.warning(f"    ⚠️ Failed to parse GraphicsPanel environment settings: {ex}")
            except Exception as ex:
                self.logger.warning(f"    ⚠️ Failed to read GraphicsPanel settings: {ex}")
            
            # Add Qt's QML import path
            from PySide6.QtCore import QLibraryInfo
            qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
            engine.addImportPath(str(qml_path))
            self.logger.debug(f"    🔧 Added QML import path: {qml_path}")
            
            # Also add local paths if they exist
            local_qml_path = Path("assets/qml")
            if local_qml_path.exists():
                engine.addImportPath(str(local_qml_path.absolute()))
                self.logger.debug(f"    🔧 Added local QML path: {local_qml_path.absolute()}")
            
            # ✅ НОВОЕ: Теперь используем только ОДИН файл main.qml
            qml_path = Path("assets/qml/main.qml")
            
            self.logger.debug("    🔍 ДИАГНОСТИКА ЗАГРУЗКИ QML:")
            self.logger.debug(f"       Целевой файл: {qml_path}")
            self.logger.debug(f"       Файл существует: {qml_path.exists()}")
            
            if not qml_path.exists():
                raise FileNotFoundError(f"QML файл не найден: {qml_path}")
            
            file_size = qml_path.stat().st_size
            self.logger.debug(f"       Размер файла: {file_size:,} байт")
            
            qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
            self.logger.debug(f"    📂 Полный путь: {qml_url.toString()}")
            
            # ✅ Устанавливаем базовую директорию QML для разрешения относительных путей
            try:
                self._qml_base_dir = qml_path.parent.resolve()
            except Exception:
                self._qml_base_dir = None
            
            self._qquick_widget.setSource(qml_url)
            
            status = self._qquick_widget.status()
            self.logger.debug(f"    📊 QML статус загрузки: {status}")
            
            if status == QQuickWidget.Status.Error:
                errors = self._qquick_widget.errors()
                error_messages = [str(e) for e in errors]
                error_msg = "\n".join(error_messages)
                self.logger.error("    ❌ ОШИБКИ QML ЗАГРУЗКИ:")
                for i, error in enumerate(error_messages, 1):
                    self.logger.error(f"       {i}. {error}")
                raise RuntimeError(f"Ошибки загрузки QML:\n{error_msg}")
                    
            elif status == QQuickWidget.Status.Loading:
                self.logger.debug(f"    ⏳ QML файл загружается...")
            elif status == QQuickWidget.Status.Ready:
                self.logger.info(f"    ✅ QML файл загружен успешно!")
            
            self._qml_root_object = self._qquick_widget.rootObject()
            if not self._qml_root_object:
                raise RuntimeError("Не удалось получить корневой объект QML")

            # ✅ БАЗОВАЯ ДИРЕКТОРИЯ ДЛЯ РЕЗОЛЮЦИИ ПУТЕЙ (для _resolve_qurl)
            try:
                self._qml_base_dir = qml_path.parent.resolve()
                self.logger.debug(f"    📁 Базовая директория QML: {self._qml_base_dir}")
            except Exception:
                self._qml_base_dir = None
            
            # ✅ Connect QML ACK signal for graphics logger sync
            try:
                self._qml_root_object.batchUpdatesApplied.connect(
                    self._on_qml_batch_ack,
                    Qt.QueuedConnection
                )
                self.logger.info("    ✅ Connected QML batchUpdatesApplied → Python ACK handler")
            except AttributeError:
                self.logger.warning("    ⚠️ QML batchUpdatesApplied signal not found (old QML version?)")
            
            self.logger.info("    [OK] ✅ ЕДИНОЙ QML файл 'main.qml' загружен успешно")
            self.logger.info("    ✨ Версия: Enhanced v5.0 (объединённая, оптимизированная, с IBL)")
            self.logger.info("    🔧 QML import paths настроены для QtQuick3D")

            
        except Exception as e:
            self.logger.exception(f"    [CRITICAL] Ошибка загрузки main.qml: {e}")
            
            fallback = QLabel(
                "КРИТИЧЕСКАЯ ОШИБКА ЗАГРУЗКИ 3D СЦЕНЫ\n\n"
                f"Ошибка: {e}\n\n"
                "Проверьте файл assets/qml/main.qml\n"
                "и убедитесь, что QtQuick3D установлен правильно"
            )
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setStyleSheet("background: #1a1a2e; color: #ff6b6b; font-size: 12px; padding: 20px;")
            self._qquick_widget = fallback
            self.logger.warning(f"    [WARNING] Использован заглушка-виджет")

    def _setup_legacy_opengl_view(self):
        """Setup legacy OpenGL widget"""
        self.logger.debug("_setup_legacy_opengl_view: Загрузка legacy QML...")
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
        self.logger.debug("_setup_tabs: Создание вкладок с ресайзбаром...")
        
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
        self.logger.debug("      ✅ Вкладка 'Геометрия' создана")
        
        # Tab 2: ПНЕВМОСИСТЕМА (Pneumatics)
        self.pneumo_panel = PneumoPanel(self)
        scroll_pneumo = QScrollArea()
        scroll_pneumo.setWidgetResizable(True)
        scroll_pneumo.setWidget(self.pneumo_panel)
        scroll_pneumo.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tab_widget.addTab(scroll_pneumo, "Пневмосистема")
        self.logger.debug("      ✅ Вкладка 'Пневмосистема' создана")
        
        # Tab 3: РЕЖИМЫ СТАБИЛИЗАТОРА (Modes)
        self.modes_panel = ModesPanel(self)
        scroll_modes = QScrollArea()
        scroll_modes.setWidgetResizable(True)
        scroll_modes.setWidget(self.modes_panel)
        scroll_modes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tab_widget.addTab(scroll_modes, "Режимы стабилизатора")
        self.logger.debug("      ✅ Вкладка 'Режимы стабилизатора' создана")
        
        # Tab 4: ГРАФИКА И ВИЗУАЛИЗАЦИЯ (объединенная панель)
        self.graphics_panel = GraphicsPanel(self)
        self._graphics_panel = self.graphics_panel  # ✅ ИСПРАВЛЕНО: Добавляем атрибут для диагностики
        # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: НЕ оборачиваем GraphicsPanel в еще один ScrollArea!
        # Она уже имеет внутренние ScrollArea для каждой вкладки
        self.tab_widget.addTab(self.graphics_panel, "🎨 Графика")
        self.logger.debug("      ✅ Вкладка 'Графика и визуализация' создана")
        
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
        self.logger.debug("      ✅ Вкладка 'Динамика движения' создана (заглушка)")
        
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
        
        self.logger.debug("✅ Вкладки созданы и подключены кHorizont таймеровенному сплиттеру")

    @Slot(int)
    def _on_tab_changed(self, index: int):
        """Сохранить выбранную вкладку / Save selected tab"""
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        settings.setValue(self.SETTINGS_LAST_TAB, index)
        
        tab_names = [
            "Геометрия", "ПневмоСистема", "Режимы стабилизатора",
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
                lambda name, val: self.logger.debug(f"🔧 GeometryPanel: {name}={val}")
            )
            # ИСПРАВЛЕНО: Подключаем geometry_changed сигнал к обработчику QML
            self.geometry_panel.geometry_changed.connect(self._on_geometry_changed_qml)
            self.logger.info("✅ Сигналы GeometryPanel подключены (geometry_changed → QML)")

        # Pneumatic panel
        if self.pneumo_panel:
            # ВРЕМЕННАЯ ЗАГЛУШКА - просто логируем
            self.pneumo_panel.mode_changed.connect(lambda mode_type, new_mode: self.logger.debug(f"🔧 Mode changed: {mode_type} -> {new_mode}"))
            self.pneumo_panel.parameter_changed.connect(lambda name, value: self.logger.debug(f"🔧 Pneumo param: {name} = {value}"))
            self.logger.info("✅ Сигналы PneumoPanel подключены (ЗАГЛУШКА)")

        # Modes panel
        if self.modes_panel:
            # Simulation control
            self.modes_panel.simulation_control.connect(self._on_sim_control)
            self.logger.info("✅ Сигнал simulation_control подключен")
            
            # Mode changes (заглушка)
            self.modes_panel.mode_changed.connect(lambda mode_type, new_mode: self.logger.debug(f"🔧 Mode changed: {mode_type} -> {new_mode}"))
            
            # Parameter changes (заглушка)
            self.modes_panel.parameter_changed.connect(lambda n, v: self.logger.debug(f"🔧 Param: {n} = {v}"))
            
            # ✨ НОВОЕ: Подключаем обработчик изменения параметров анимации
            self.modes_panel.animation_changed.connect(self._on_animation_changed)
            self.logger.info("✅ Сигнал animation_changed подключен к _on_animation_changed")
            
            self.logger.info("✅ Сигналы ModesPanel подключены")

        # ✅ ИСПРАВЛЕНО: Graphics panel подключение сигналов
        if self.graphics_panel:
            self.logger.info("🔧 Подключаем сигналы GraphicsPanel...")
            
            # Lighting changes
            self.graphics_panel.lighting_changed.connect(self._on_lighting_changed)
            self.logger.info("   ✅ Сигнал lighting_changed подключен")
            
            # Material changes
            self.graphics_panel.material_changed.connect(self._on_material_changed)
            self.logger.info("   ✅ Сигнал material_changed подключен")
            
            # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Environment changes
            self.graphics_panel.environment_changed.connect(self._on_environment_changed)  
            self.logger.info("   ✅ Сигнал environment_changed подключен")
            
            # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Quality changes
            self.graphics_panel.quality_changed.connect(self._on_quality_changed)
            self.logger.info("   ✅ Сигнал quality_changed подключен")
            
            # Camera changes
            self.graphics_panel.camera_changed.connect(self._on_camera_changed)
            self.logger.info("   ✅ Сигнал camera_changed подключен")
            
            # Effects changes
            self.graphics_panel.effects_changed.connect(self._on_effects_changed)
            self.logger.info("   ✅ Сигнал effects_changed подключен")
            
            # Preset applied
            self.graphics_panel.preset_applied.connect(self._on_preset_applied)
            self.logger.info("   ✅ Сигнал preset_applied подключен")
            

            self.logger.info("✅ Все сигналы GraphicsPanel подключены")

    # ------------------------------------------------------------------
    # Обработка сигналов от панелей
    # ------------------------------------------------------------------
    @Slot(dict)
    def _on_geometry_changed_qml(self, geometry_params: Dict[str, Any]):
        """Получить обновления геометрии от панели и немедленно применить их в QML.
        Использует прямой вызов QML-функции `applyGeometryUpdates`.
        При недоступности — ставит в очередь как батч.
        """
        if not isinstance(geometry_params, dict):
            self.logger.warning("Geometry update payload is not a dict: %r", geometry_params)
            return

        self.logger.info(
            "Geometry update received (%d keys): %s",
            len(geometry_params),
            list(geometry_params.keys()),
        )

        if self._qml_root_object:
            try:
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt

                # Логируем QML-вызов
                try:
                    self.event_logger.log_qml_invoke("applyGeometryUpdates", geometry_params)
                except Exception:
                    pass

                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "applyGeometryUpdates",
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", geometry_params)
                )

                if success:
                    if hasattr(self, "status_bar"):
                        self.status_bar.showMessage("Геометрия обновлена", 2000)

                    # Логируем изменения через GraphicsLogger как применённые
                    try:
                        from .panels.graphics_logger import get_graphics_logger
                        logger = get_graphics_logger()
                        logger.log_change(
                            parameter_name="geometry_batch",
                            old_value=None,
                            new_value=geometry_params,
                            category="geometry",
                            panel_state=geometry_params,
                            qml_state={"applied": True},
                            applied_to_qml=True
                        )
                    except Exception:
                        pass
                    return
                else:
                    self.logger.warning("Failed to call applyGeometryUpdates(); queueing fallback")
            except Exception as e:
                self.logger.error(f"Geometry update failed: {e}")
                import traceback
                traceback.print_exc()

        # Если QML ещё не готов — ставим в очередь, либо используем батч
        self._queue_qml_update("geometry", geometry_params)

        if self.status_bar:
            self.status_bar.showMessage("Геометрия отправлена в 3D сцену", 2000)

    def _flush_qml_updates(self) -> None:
        """Сбросить накопленные batched-обновления в QML.
        Сначала пытаемся установить свойство `pendingPythonUpdates` (быстро и дёшево),
        если не получится — вызываем соответствующие `applyXxxUpdates` по отдельности.
        """
        if not self._qml_update_queue:
            return

        if not self._qml_root_object:
            # Подождём, пока QML догрузится
            self._qml_flush_timer.start(100)
            return

        pending = self._qml_update_queue
        self._qml_update_queue = {}

        # Попытка batched push через свойство в QML
        if self._push_batched_updates(pending):
            # Сохраняем для последующего учёта после ACK
            self._last_batched_updates = pending
            return

        # Фоллбек: пробуем вызвать функции напрямую
        for key, payload in pending.items():
            methods = self.QML_UPDATE_METHODS.get(key, ())
            for method_name in methods:
                if self._invoke_qml_function(method_name, payload):
                    break

    def _push_batched_updates(self, updates: Dict[str, Any]) -> bool:
        if not updates:
            return True
        if not self._qml_root_object:
            return False

        try:
            sanitized = self._prepare_updates_for_qml(updates)
            self._qml_root_object.setProperty("pendingPythonUpdates", sanitized)
            return True
        except Exception:
            return False

    @staticmethod
    def _prepare_updates_for_qml(value: Any):
        """Подготовить словари/массивы к безопасной передаче в QML."""
        if isinstance(value, dict):
            return {str(k): MainWindow._prepare_updates_for_qml(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [MainWindow._prepare_updates_for_qml(i) for i in value]
        try:
            import numpy as _np  # локальный импорт, чтобы не ломать окружение
            if isinstance(value, _np.generic):
                return value.item()
        except Exception:
            pass
        if hasattr(value, 'tolist') and callable(value.tolist):
            return MainWindow._prepare_updates_for_qml(value.tolist())
        if isinstance(value, Path):
            return str(value)
        return value

    def _invoke_qml_function(self, method_name: str, payload: Optional[Dict[str, Any]] = None) -> bool:
        """Безопасный вызов QML-функции по имени."""
        if not self._qml_root_object:
            return False
        try:
            from PySide6.QtCore import QMetaObject, Q_ARG, Qt
            if payload is None:
                return QMetaObject.invokeMethod(
                    self._qml_root_object,
                    method_name,
                    Qt.ConnectionType.DirectConnection
                )
            else:
                return QMetaObject.invokeMethod(
                    self._qml_root_object,
                    method_name,
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", payload)
                )
        except Exception:
            return False

    @staticmethod
    def _deep_merge_dicts(target: Dict[str, Any], source: Dict[str, Any]) -> None:
        for k, v in source.items():
            if isinstance(v, dict) and isinstance(target.get(k), dict):
                MainWindow._deep_merge_dicts(target[k], v)
            else:
                target[k] = v

    def _queue_qml_update(self, key: str, params: Dict[str, Any]) -> None:
        """Поставить изменения в очередь для батч-отправки в QML."""
        if not params:
            return
        if key not in self._qml_update_queue:
            self._qml_update_queue[key] = {}
        self._deep_merge_dicts(self._qml_update_queue[key], params)
        if not self._qml_flush_timer.isActive():
            self._qml_flush_timer.start(0)

    # ------------------------------------------------------------------
    # АCK из QML
    # ------------------------------------------------------------------
    @Slot(dict)
    def _on_qml_batch_ack(self, summary: Dict[str, Any]) -> None:
        try:
            self.logger.info("QML batch ACK: %s", summary)
            if hasattr(self, "status_bar"):
                self.status_bar.showMessage("Обновления применены в сцене", 1500)

            # Повышаем метрику синхронизации: отмечаем, что все отправленные категории применены
            if self._last_batched_updates:
                for cat, payload in self._last_batched_updates.items():
                    if isinstance(payload, dict) and payload:
                        self._log_graphics_change(str(cat), payload, applied=True)
                self._last_batched_updates = None
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Обработчики сигналов панелей (минимальная реализация)
    # ------------------------------------------------------------------
    @Slot(dict)
    def _on_lighting_changed(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return
        if not self._invoke_qml_function("applyLightingUpdates", params):
            self._queue_qml_update("lighting", params)
            self._log_graphics_change("lighting", params, applied=False)
        else:
            self._log_graphics_change("lighting", params, applied=True)

    @Slot(dict)
    def _on_material_changed(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return
        if not self._invoke_qml_function("applyMaterialUpdates", params):
            self._queue_qml_update("materials", params)
            self._log_graphics_change("materials", params, applied=False)
        else:
            self._log_graphics_change("materials", params, applied=True)

    @Slot(dict)
    def _on_environment_changed(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return
        if not self._invoke_qml_function("applyEnvironmentUpdates", params):
            self._queue_qml_update("environment", params)
            self._log_graphics_change("environment", params, applied=False)
        else:
            self._log_graphics_change("environment", params, applied=True)

    @Slot(dict)
    def _on_quality_changed(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return
        if not self._invoke_qml_function("applyQualityUpdates", params):
            self._queue_qml_update("quality", params)
            self._log_graphics_change("quality", params, applied=False)
        else:
            self._log_graphics_change("quality", params, applied=True)

    @Slot(dict)
    def _on_camera_changed(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return
        if not self._invoke_qml_function("applyCameraUpdates", params):
            self._queue_qml_update("camera", params)
            self._log_graphics_change("camera", params, applied=False)
        else:
            self._log_graphics_change("camera", params, applied=True)

    @Slot(dict)
    def _on_effects_changed(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return
        if not self._invoke_qml_function("applyEffectsUpdates", params):
            self._queue_qml_update("effects", params)
            self._log_graphics_change("effects", params, applied=False)
        else:
            self._log_graphics_change("effects", params, applied=True)

    @Slot(dict)
    def _on_preset_applied(self, full_state: Dict[str, Any]) -> None:
        """Применение пресета графики — отправляем одним батчем."""
        if not isinstance(full_state, dict):
            return
        self._queue_qml_update("environment", full_state.get("environment", {}))
        self._queue_qml_update("lighting", full_state.get("lighting", {}))
        self._queue_qml_update("materials", full_state.get("materials", {}))
        self._queue_qml_update("quality", full_state.get("quality", {}))
        self._queue_qml_update("camera", full_state.get("camera", {}))
        self._queue_qml_update("effects", full_state.get("effects", {}))

    @Slot(dict)
    def _on_animation_changed(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            return
        if not self._invoke_qml_function("applyAnimationUpdates", params):
            self._queue_qml_update("animation", params)
            self._log_graphics_change("animation", params, applied=False)
        else:
            self._log_graphics_change("animation", params, applied=True)

    @Slot(str)
    def _on_sim_control(self, command: str) -> None:
        """Управление симуляцией (минимум)."""
        cmd = (command or "").lower()
        if cmd == "start":
            self.is_simulation_running = True
        elif cmd == "pause":
            self.is_simulation_running = False
        elif cmd == "stop":
            self.is_simulation_running = False
        elif cmd == "reset":
            try:
                self._invoke_qml_function("fullResetView")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Заглушка для обновления 3D из снапшота симуляции
    # ------------------------------------------------------------------
    def _update_3d_from_snapshot(self, snapshot: "StateSnapshot") -> None:
        """Обновление 3D из снапшота — отключено по требованию пользователя (без заглушек)."""
        # Явно ничего не делаем, чтобы не скрывать проблемы во время отладки
        pass

    def _setup_menus(self) -> None:
        """Создать меню приложения (минимальный набор).
        Файл → Выход; Вид → Сбросить расположение.
        """
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

    def _reset_ui_layout(self) -> None:
        """Сбросить размеры сплиттеров к значениям по умолчанию и обновить статус-бар."""
        if self.main_splitter:
            self.main_splitter.setSizes([3, 2])
        if self.main_horizontal_splitter:
            self.main_horizontal_splitter.setSizes([3, 1])
        if hasattr(self, "status_bar") and self.status_bar:
            self.status_bar.showMessage("Макет интерфейса сброшен", 2000)

    def _setup_toolbar(self) -> None:
        """Создать верхнюю панель управления симуляцией (минимальный набор).
        Кнопки: Старт, Пауза, Стоп, Сброс.
        """
        toolbar = self.addToolBar("Основная")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(True)

        actions: list[tuple[str, str]] = [
            ("▶ Старт", "start"),
            ("⏸ Пауза", "pause"),
            ("⏹ Стоп", "stop"),
            ("↺ Сброс", "reset"),
        ]

        for title, command in actions:
            act = QAction(title, self)
            act.triggered.connect(lambda _=False, cmd=command: self._on_sim_control(cmd))
            toolbar.addAction(act)
        

    def _setup_status_bar(self) -> None:
        """Создать строку состояния с диагностикой (симуляция/очередь)."""
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

    def _connect_simulation_signals(self) -> None:
        """Подключить сигналы SimulationManager к обработчикам окна."""
        try:
            bus = self.simulation_manager.state_bus
            bus.state_ready.connect(self._on_state_update, Qt.QueuedConnection)
            bus.physics_error.connect(self._on_physics_error, Qt.QueuedConnection)
        except Exception as e:
            self.logger.error(f"Не удалось подключить сигналы симуляции: {e}")

    @Slot(object)
    def _on_state_update(self, snapshot: StateSnapshot) -> None:
        """Обновить UI и сцену по новому состоянию симуляции."""
        self.current_snapshot = snapshot
        try:
            if snapshot:
                # Обновление метрик в статус-баре
                self.sim_time_label.setText(f"Sim Time: {snapshot.simulation_time:.3f}s")
                self.step_count_label.setText(f"Steps: {snapshot.step_number}")
                if snapshot.aggregates.physics_step_time > 0:
                    fps = 1.0 / snapshot.aggregates.physics_step_time
                    self.fps_label.setText(f"Physics FPS: {fps:.1f}")

                # Обновить 3D (логика реализуется отдельно)
                self._update_3d_from_snapshot(snapshot)

            if self.chart_widget:
                self.chart_widget.update_from_snapshot(snapshot)
        except Exception as e:
            self.logger.error(f"Ошибка обновления состояния UI/3D: {e}")

    @Slot(str)
    def _on_physics_error(self, message: str) -> None:
        """Показать ошибку физического движка пользователю и в лог."""
        self.logger.error(f"Physics engine error: {message}")
        if hasattr(self, "status_bar") and self.status_bar:
            self.status_bar.showMessage(f"Physics error: {message}", 5000)

    def _update_render(self) -> None:
        """Периодический тик UI/анимации (вызывается таймером ~60 FPS)."""
        if not self._qml_root_object:
            return

        # Плавное время анимации в QML
        now = time.perf_counter()
        last_tick = getattr(self, "_last_animation_tick", None)
        self._last_animation_tick = now
        try:
            if bool(self._qml_root_object.property("isRunning")) and last_tick is not None:
                elapsed = now - last_tick
                current = float(self._qml_root_object.property("animationTime") or 0.0)
                self._qml_root_object.setProperty("animationTime", current + float(elapsed))
        except Exception:
            # Не скрываем ошибки, но не падаем по тикам UI
            pass

        # Обновление метрик очереди симуляции (если доступно)
        try:
            if hasattr(self.simulation_manager, "get_queue_stats"):
                stats = self.simulation_manager.get_queue_stats()
                get_c = stats.get("get_count", 0)
                put_c = stats.get("put_count", 0)
                if hasattr(self, "queue_label") and self.queue_label:
                    self.queue_label.setText(f"Queue: {get_c}/{put_c}")
        except Exception:
            if hasattr(self, "queue_label") and self.queue_label:
                self.queue_label.setText("Queue: -/-")

    def _restore_settings(self) -> None:
        """Восстановить геометрию окна, состояние и размеры сплиттеров."""
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)

        geom = settings.value(self.SETTINGS_GEOMETRY)
        if isinstance(geom, QByteArray):
            self.restoreGeometry(geom)
        elif isinstance(geom, (bytes, bytearray)):
            self.restoreGeometry(QByteArray(geom))

        state = settings.value(self.SETTINGS_STATE)
        if isinstance(state, QByteArray):
            self.restoreState(state)
        elif isinstance(state, (bytes, bytearray)):
            self.restoreState(QByteArray(state))

        split = settings.value(self.SETTINGS_SPLITTER)
        if self.main_splitter and isinstance(split, QByteArray):
            self.main_splitter.restoreState(split)
        elif self.main_splitter and isinstance(split, (bytes, bytearray)):
            self.main_splitter.restoreState(QByteArray(split))

        hsplit = settings.value(self.SETTINGS_HORIZONTAL_SPLITTER)
        if self.main_horizontal_splitter and isinstance(hsplit, QByteArray):
            self.main_horizontal_splitter.restoreState(hsplit)
        elif self.main_horizontal_splitter and isinstance(hsplit, (bytes, bytearray)):
            self.main_horizontal_splitter.restoreState(QByteArray(hsplit))

    def _save_settings(self) -> None:
        """Сохранить геометрию окна, состояние и размеры сплиттеров."""
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        settings.setValue(self.SETTINGS_GEOMETRY, self.saveGeometry())
        settings.setValue(self.SETTINGS_STATE, self.saveState())
        if self.main_splitter:
            settings.setValue(self.SETTINGS_SPLITTER, self.main_splitter.saveState())
        if self.main_horizontal_splitter:
            settings.setValue(self.SETTINGS_HORIZONTAL_SPLITTER, self.main_horizontal_splitter.saveState())

    # Сохраняем настройки при закрытии окна
    def closeEvent(self, event) -> None:  # type: ignore[override]
        try:
            self._save_settings()
        except Exception:
            pass
        super().closeEvent(event)

    def _log_graphics_change(self, category: str, payload: Dict[str, Any], applied: bool) -> None:
        """Унифицированное логирование изменений графики для метрик синхронизации."""
        try:
            from .panels.graphics_logger import get_graphics_logger
            logger = get_graphics_logger()
            logger.log_change(
                parameter_name=f"{category}_batch",
                old_value=None,
                new_value=payload,
                category=category,
                panel_state=payload,
                qml_state={"applied": applied},
                applied_to_qml=applied,
            )
        except Exception:
            pass

    def _initial_full_sync(self) -> None:
        """Полная начальная синхронизация состояния Python → QML, чтобы не оставались скрытые дефолты в QML.
        Отправляем все категории настроек из `GraphicsPanel` единым батчем.
        """
        try:
            # Пытаемся предварительно сбросить возможные QML-дефолты, если функция есть
            self._invoke_qml_function("fullResetView")
        except Exception:
            pass

        if not self.graphics_panel:
            return

        try:
            pending: Dict[str, Any] = {}
            # Формируем полный payload по категориям из GraphicsPanel
            pending["lighting"] = self.graphics_panel._prepare_lighting_payload()
            pending["environment"] = self.graphics_panel._prepare_environment_payload()
            pending["materials"] = self.graphics_panel._prepare_materials_payload()
            pending["quality"] = self.graphics_panel._prepare_quality_payload()
            pending["camera"] = self.graphics_panel._prepare_camera_payload()
            pending["effects"] = self.graphics_panel._prepare_effects_payload()

            # Отправляем батчем; при успехе — дождёмся ACK и отметим как applied
            if not self._push_batched_updates(pending):
                # Фоллбек — по одной категории
                for cat, payload in pending.items():
                    methods = self.QML_UPDATE_METHODS.get(cat, ())
                    sent = False
                    for m in methods:
                        if self._invoke_qml_function(m, payload):
                            sent = True
                            break
                    # Логируем отправку; применится после ACK или сразу если прямой вызов
                    self._log_graphics_change(cat, payload, applied=sent)
            else:
                # Сохраним для ACK
                self._last_batched_updates = pending
        except Exception as e:
            self.logger.error(f"Initial full sync failed: {e}")
