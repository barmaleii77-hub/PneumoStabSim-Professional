"""
GraphicsPanel - панель настроек графики и визуализации (РАСШИРЕННАЯ ВЕРСИЯ)
Graphics Panel - comprehensive graphics and visualization settings panel
РУССКИЙ ИНТЕРФЕЙС (Russian UI) + ПОЛНЫЙ НАБОР ПАРАМЕТРОВ
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel, 
    QSlider, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QPushButton,
    QColorDialog, QFrame, QSizePolicy, QScrollArea, QTabWidget, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot, QSettings
from PySide6.QtGui import QColor, QPalette
import logging
from typing import Dict, Any
import json


class ColorButton(QPushButton):
    """Кнопка выбора цвета с предварительным просмотром"""
    
    color_changed = Signal(str)  # Emit hex color string
    
    def __init__(self, initial_color: str = "#ffffff", parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 30)
        self.color = QColor(initial_color)
        self.update_style()
        self.clicked.connect(self.choose_color)
    
    def update_style(self):
        """Обновить стиль кнопки с текущим цветом"""
        self.setStyleSheet(
            f"QPushButton {{ "
            f"background-color: {self.color.name()}; "
            f"border: 2px solid #666; "
            f"border-radius: 4px; "
            f"}} "
            f"QPushButton:hover {{ "
            f"border: 2px solid #aaa; "
            f"}}"
        )
    
    @Slot()
    def choose_color(self):
        """Открыть диалог выбора цвета"""
        color = QColorDialog.getColor(self.color, self, "Выбрать цвет")
        if color.isValid():
            self.color = color
            self.update_style()
            self.color_changed.emit(color.name())
    
    def set_color(self, color_str: str):
        """Установить цвет программно"""
        self.color = QColor(color_str)
        self.update_style()


class GraphicsPanel(QWidget):
    """
    Панель настроек графики и визуализации (РАСШИРЕННАЯ ВЕРСИЯ)
    Comprehensive graphics and visualization settings panel with FULL parameter set
    """
    
    # Сигналы для обновления графики
    lighting_changed = Signal(dict)      # Изменение параметров освещения
    environment_changed = Signal(dict)   # Изменение параметров окружения
    material_changed = Signal(dict)      # Изменение настроек материалов  
    quality_changed = Signal(dict)       # Изменение качества рендеринга
    camera_changed = Signal(dict)        # Изменение настроек камеры
    effects_changed = Signal(dict)       # Изменение визуальных эффектов
    preset_applied = Signal(str)         # Применение пресета освещения
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Настройки
        self.settings = QSettings("PneumoStabSim", "GraphicsPanel")
        
        # ✅ РАСШИРЕННЫЕ текущие параметры графики (ПОЛНЫЙ НАБОР!)
        self.current_graphics = {
            # Освещение
            'key_brightness': 2.8,
            'key_color': '#ffffff',
            'key_angle_x': -30,
            'key_angle_y': -45,
            'fill_brightness': 1.2,
            'fill_color': '#f0f0ff',
            'rim_brightness': 1.5,
            'rim_color': '#ffffcc',
            'point_brightness': 20000,
            'point_color': '#ffffff',
            'point_y': 1800,
            'point_fade': 0.00008,
            
            # Окружение и IBL
            'background_color': '#2a2a2a',
            'fog_enabled': False,
            'fog_color': '#808080',
            'fog_density': 0.1,
            'skybox_enabled': False,
            'skybox_blur': 0.0,
            'ibl_enabled': True,               # ✅ НОВОЕ: IBL
            'ibl_intensity': 1.0,              # ✅ НОВОЕ: Интенсивность IBL
            
            # Качество рендеринга
            'antialiasing': 2,          # 0=None, 1=SSAA, 2=MSAA
            'aa_quality': 2,            # 0=Low, 1=Medium, 2=High
            'shadows_enabled': True,
            'shadow_quality': 1,        # 0=Low, 1=Medium, 2=High
            'shadow_softness': 0.5,     # ✅ НОВОЕ: Мягкость теней
            
            # Материалы
            'metal_roughness': 0.28,
            'metal_metalness': 1.0,
            'metal_clearcoat': 0.25,
            'glass_opacity': 0.35,
            'glass_roughness': 0.05,
            'glass_ior': 1.52,              # ✅ НОВОЕ: Коэффициент преломления!
            'frame_metalness': 0.8,
            'frame_roughness': 0.4,
            
            # Камера
            'camera_fov': 45.0,
            'camera_near': 10.0,
            'camera_far': 50000.0,
            'camera_speed': 1.0,
            'auto_rotate': False,
            'auto_rotate_speed': 0.5,
            
            # Эффекты - РАСШИРЕННЫЕ
            'bloom_enabled': False,
            'bloom_intensity': 0.3,
            'bloom_threshold': 1.0,         # ✅ НОВОЕ: Порог Bloom
            'ssao_enabled': False,
            'ssao_intensity': 0.5,
            'ssao_radius': 8.0,             # ✅ НОВОЕ: Радиус SSAO
            'motion_blur': False,
            'depth_of_field': False,
            'dof_focus_distance': 2000,     # ✅ НОВОЕ: Дистанция фокуса DoF
            'dof_focus_range': 900,         # ✅ НОВОЕ: Диапазон фокуса DoF
            
            # Тонемаппинг
            'tonemap_enabled': True,        # ✅ НОВОЕ: Тонемаппинг
            'tonemap_mode': 3,              # ✅ НОВОЕ: Режим тонемаппинга (0=None, 1=Linear, 2=Reinhard, 3=Filmic)
            
            # Виньетирование
            'vignette_enabled': True,       # ✅ НОВОЕ: Виньетирование
            'vignette_strength': 0.45,      # ✅ НОВОЕ: Сила виньетирования
            
            # Lens Flare
            'lens_flare_enabled': True,     # ✅ НОВОЕ: Lens Flare
        }
        
        # Построение UI с вкладками
        self.setup_ui()
        
        # Загрузить сохраненные настройки
        self.load_settings()
        
        # ✨ ИСПРАВЛЕНО: Отправляем начальные настройки графики в QML!
        print("🎨 GraphicsPanel: Отправка начальных настроек графики...")
        
        # Используем QTimer для отложенной отправки после полной инициализации UI
        from PySide6.QtCore import QTimer
        def send_initial_graphics():
            print("⏰ QTimer: Отправка начальных настроек графики...")
            
            # Отправляем все типы настроек
            self.emit_lighting_update()
            self.emit_material_update()
            self.emit_environment_update()
            self.emit_quality_update()
            self.emit_camera_update()
            self.emit_effects_update()
            
            print(f"  ✅ Все начальные настройки графики отправлены!")
        
        QTimer.singleShot(200, send_initial_graphics)  # Отправить через 200мс
        
        self.logger.info("GraphicsPanel инициализирована (РАСШИРЕННАЯ версия с полным набором параметров)")
    
    def setup_ui(self):
        """Построение пользовательского интерфейса с вкладками"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Заголовок
        title = QLabel("🎨 Графика и визуализация")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c5aa0; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Создать вкладки для разных категорий настроек
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # Вкладка 1: Освещение
        lighting_tab = self.create_lighting_tab()
        self.tab_widget.addTab(lighting_tab, "💡 Освещение")
        
        # Вкладка 2: Материалы
        materials_tab = self.create_materials_tab()
        self.tab_widget.addTab(materials_tab, "🏗️ Материалы")
        
        # Вкладка 3: Окружение
        environment_tab = self.create_environment_tab()
        self.tab_widget.addTab(environment_tab, "🌍 Окружение")
        
        # Вкладка 4: Камера
        camera_tab = self.create_camera_tab()
        self.tab_widget.addTab(camera_tab, "📷 Камера")
        
        # Вкладка 5: Эффекты
        effects_tab = self.create_effects_tab()
        self.tab_widget.addTab(effects_tab, "✨ Эффекты")
        
        layout.addWidget(self.tab_widget)
        
        # Кнопки управления внизу
        self.create_control_buttons(layout)
    
    def create_lighting_tab(self):
        """Создать вкладку освещения"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Key Light (основной свет)
        key_group = QGroupBox("🔆 Основной свет")
        key_layout = QGridLayout(key_group)
        
        # Яркость
        key_layout.addWidget(QLabel("Яркость:"), 0, 0)
        self.key_brightness = QDoubleSpinBox()
        self.key_brightness.setRange(0.0, 10.0)
        self.key_brightness.setSingleStep(0.1)
        self.key_brightness.setDecimals(1)
        self.key_brightness.setValue(self.current_graphics['key_brightness'])
        self.key_brightness.valueChanged.connect(self.on_key_brightness_changed)
        key_layout.addWidget(self.key_brightness, 0, 1)
        
        # Цвет
        key_layout.addWidget(QLabel("Цвет:"), 0, 2)
        self.key_color = ColorButton(self.current_graphics['key_color'])
        self.key_color.color_changed.connect(self.on_key_color_changed)
        key_layout.addWidget(self.key_color, 0, 3)
        
        # Углы
        key_layout.addWidget(QLabel("Наклон X:"), 1, 0)
        self.key_angle_x = QSpinBox()
        self.key_angle_x.setRange(-90, 90)
        self.key_angle_x.setSuffix("°")
        self.key_angle_x.setValue(self.current_graphics['key_angle_x'])
        self.key_angle_x.valueChanged.connect(self.on_key_angle_x_changed)
        key_layout.addWidget(self.key_angle_x, 1, 1)
        
        key_layout.addWidget(QLabel("Поворот Y:"), 1, 2)
        self.key_angle_y = QSpinBox()
        self.key_angle_y.setRange(-180, 180)
        self.key_angle_y.setSuffix("°")
        self.key_angle_y.setValue(self.current_graphics['key_angle_y'])
        self.key_angle_y.valueChanged.connect(self.on_key_angle_y_changed)
        key_layout.addWidget(self.key_angle_y, 1, 3)
        
        layout.addWidget(key_group)
        
        # Fill Light (заполняющий свет)
        fill_group = QGroupBox("🔅 Заполняющий свет")
        fill_layout = QGridLayout(fill_group)
        
        fill_layout.addWidget(QLabel("Яркость:"), 0, 0)
        self.fill_brightness = QDoubleSpinBox()
        self.fill_brightness.setRange(0.0, 5.0)
        self.fill_brightness.setSingleStep(0.1)
        self.fill_brightness.setDecimals(1)
        self.fill_brightness.setValue(self.current_graphics['fill_brightness'])
        self.fill_brightness.valueChanged.connect(self.on_fill_brightness_changed)
        fill_layout.addWidget(self.fill_brightness, 0, 1)
        
        fill_layout.addWidget(QLabel("Цвет:"), 0, 2)
        self.fill_color = ColorButton(self.current_graphics['fill_color'])
        self.fill_color.color_changed.connect(self.on_fill_color_changed)
        fill_layout.addWidget(self.fill_color, 0, 3)
        
        layout.addWidget(fill_group)
        
        # Point Light (точечный свет)
        point_group = QGroupBox("⚡ Точечный свет")
        point_layout = QGridLayout(point_group)
        
        point_layout.addWidget(QLabel("Яркость:"), 0, 0)
        self.point_brightness = QSpinBox()
        self.point_brightness.setRange(0, 100000)
        self.point_brightness.setSingleStep(1000)
        self.point_brightness.setValue(int(self.current_graphics['point_brightness']))
        self.point_brightness.valueChanged.connect(self.on_point_brightness_changed)
        point_layout.addWidget(self.point_brightness, 0, 1)
        
        point_layout.addWidget(QLabel("Высота:"), 0, 2)
        self.point_y = QSpinBox()
        self.point_y.setRange(0, 5000)
        self.point_y.setSingleStep(100)
        self.point_y.setSuffix("мм")
        self.point_y.setValue(int(self.current_graphics['point_y']))
        self.point_y.valueChanged.connect(self.on_point_y_changed)
        point_layout.addWidget(self.point_y, 0, 3)
        
        layout.addWidget(point_group)
        
        # Пресеты освещения
        presets_group = QGroupBox("🎭 Пресеты освещения")
        presets_layout = QHBoxLayout(presets_group)
        
        day_btn = QPushButton("☀️ День")
        day_btn.clicked.connect(lambda: self.apply_preset('day'))
        presets_layout.addWidget(day_btn)
        
        night_btn = QPushButton("🌙 Ночь")
        night_btn.clicked.connect(lambda: self.apply_preset('night'))
        presets_layout.addWidget(night_btn)
        
        industrial_btn = QPushButton("🏭 Промышленное")
        industrial_btn.clicked.connect(lambda: self.apply_preset('industrial'))
        presets_layout.addWidget(industrial_btn)
        
        layout.addWidget(presets_group)
        
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def create_materials_tab(self):
        """Создать вкладку настроек материалов"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Металлические части
        metal_group = QGroupBox("🔩 Металлические части")
        metal_layout = QGridLayout(metal_group)
        
        # Шероховатость металла
        metal_layout.addWidget(QLabel("Шероховатость:"), 0, 0)
        self.metal_roughness = QDoubleSpinBox()
        self.metal_roughness.setRange(0.0, 1.0)
        self.metal_roughness.setSingleStep(0.05)
        self.metal_roughness.setDecimals(2)
        self.metal_roughness.setValue(self.current_graphics['metal_roughness'])
        self.metal_roughness.valueChanged.connect(self.on_metal_roughness_changed)
        metal_layout.addWidget(self.metal_roughness, 0, 1)
        
        # Металличность
        metal_layout.addWidget(QLabel("Металличность:"), 0, 2)
        self.metal_metalness = QDoubleSpinBox()
        self.metal_metalness.setRange(0.0, 1.0)
        self.metal_metalness.setSingleStep(0.1)
        self.metal_metalness.setDecimals(1)
        self.metal_metalness.setValue(self.current_graphics['metal_metalness'])
        self.metal_metalness.valueChanged.connect(self.on_metal_metalness_changed)
        metal_layout.addWidget(self.metal_metalness, 0, 3)
        
        # Прозрачное покрытие
        metal_layout.addWidget(QLabel("Покрытие:"), 1, 0)
        self.metal_clearcoat = QDoubleSpinBox()
        self.metal_clearcoat.setRange(0.0, 1.0)
        self.metal_clearcoat.setSingleStep(0.05)
        self.metal_clearcoat.setDecimals(2)
        self.metal_clearcoat.setValue(self.current_graphics['metal_clearcoat'])
        self.metal_clearcoat.valueChanged.connect(self.on_metal_clearcoat_changed)
        metal_layout.addWidget(self.metal_clearcoat, 1, 1)
        
        layout.addWidget(metal_group)
        
        # ✅ РАСШИРЕННЫЕ Стеклянные части (с коэффициентом преломления!)
        glass_group = QGroupBox("🪟 Стеклянные части")
        glass_layout = QGridLayout(glass_group)
        
        # Прозрачность стекла
        glass_layout.addWidget(QLabel("Прозрачность:"), 0, 0)
        self.glass_opacity = QDoubleSpinBox()
        self.glass_opacity.setRange(0.0, 1.0)
        self.glass_opacity.setSingleStep(0.05)
        self.glass_opacity.setDecimals(2)
        self.glass_opacity.setValue(self.current_graphics['glass_opacity'])
        self.glass_opacity.valueChanged.connect(self.on_glass_opacity_changed)
        glass_layout.addWidget(self.glass_opacity, 0, 1)
        
        # Шероховатость стекла
        glass_layout.addWidget(QLabel("Шероховатость:"), 0, 2)
        self.glass_roughness = QDoubleSpinBox()
        self.glass_roughness.setRange(0.0, 1.0)
        self.glass_roughness.setSingleStep(0.05)
        self.glass_roughness.setDecimals(2)
        self.glass_roughness.setValue(self.current_graphics['glass_roughness']);
        self.glass_roughness.valueChanged.connect(self.on_glass_roughness_changed)
        glass_layout.addWidget(self.glass_roughness, 0, 3)
        
        # ✅ НОВОЕ: Коэффициент преломления (IOR) - КРИТИЧЕСКИ ВАЖНО!
        glass_layout.addWidget(QLabel("Преломление (IOR):"), 1, 0)
        self.glass_ior = QDoubleSpinBox()
        self.glass_ior.setRange(1.0, 3.0)
        self.glass_ior.setSingleStep(0.01)
        self.glass_ior.setDecimals(2)
        self.glass_ior.setValue(self.current_graphics['glass_ior'])
        self.glass_ior.valueChanged.connect(self.on_glass_ior_changed)
        self.glass_ior.setToolTip("Коэффициент преломления: Воздух=1.0, Вода=1.33, Стекло=1.52, Алмаз=2.42")
        glass_layout.addWidget(self.glass_ior, 1, 1)
        
        # Подсказка для IOR
        ior_hint = QLabel("💡 Стекло: 1.52, Вода: 1.33, Воздух: 1.0")
        ior_hint.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        glass_layout.addWidget(ior_hint, 1, 2, 1, 2)
        
        layout.addWidget(glass_group)
        
        # Рама и кузов
        frame_group = QGroupBox("🏗️ Рама и кузов")
        frame_layout = QGridLayout(frame_group)
        
        # Металличность рамы
        frame_layout.addWidget(QLabel("Металличность:"), 0, 0)
        self.frame_metalness = QDoubleSpinBox()
        self.frame_metalness.setRange(0.0, 1.0)
        self.frame_metalness.setSingleStep(0.1)
        self.frame_metalness.setDecimals(1)
        self.frame_metalness.setValue(self.current_graphics['frame_metalness'])
        self.frame_metalness.valueChanged.connect(self.on_frame_metalness_changed)
        frame_layout.addWidget(self.frame_metalness, 0, 1)
        
        # Шероховатость рамы
        frame_layout.addWidget(QLabel("Шероховатость:"), 0, 2)
        self.frame_roughness = QDoubleSpinBox()
        self.frame_roughness.setRange(0.0, 1.0)
        self.frame_roughness.setSingleStep(0.1)
        self.frame_roughness.setDecimals(1)
        self.frame_roughness.setValue(self.current_graphics['frame_roughness'])
        self.frame_roughness.valueChanged.connect(self.on_frame_roughness_changed)
        frame_layout.addWidget(self.frame_roughness, 0, 3)
        
        layout.addWidget(frame_group)
        
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def create_environment_tab(self):
        """Создать вкладку настроек окружения"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Фон и цвет
        bg_group = QGroupBox("🎨 Фон и окружение")
        bg_layout = QGridLayout(bg_group)
        
        # Цвет фона
        bg_layout.addWidget(QLabel("Цвет фона:"), 0, 0)
        self.background_color = ColorButton(self.current_graphics['background_color'])
        self.background_color.color_changed.connect(self.on_background_color_changed)
        bg_layout.addWidget(self.background_color, 0, 1)
        
        # Кнопка сброса фона
        reset_bg = QPushButton("Сброс")
        reset_bg.setMaximumWidth(60)
        reset_bg.clicked.connect(lambda: self.background_color.set_color('#2a2a2a'))
        bg_layout.addWidget(reset_bg, 0, 2)
        
        # Skybox
        self.skybox_enabled = QCheckBox("Включить Skybox")
        self.skybox_enabled.setChecked(self.current_graphics['skybox_enabled'])
        self.skybox_enabled.toggled.connect(self.on_skybox_toggled)
        bg_layout.addWidget(self.skybox_enabled, 1, 0, 1, 2)
        
        layout.addWidget(bg_group)
        
        # ✅ НОВОЕ: IBL (Image Based Lighting) группа
        ibl_group = QGroupBox("💡 IBL (Image Based Lighting)")
        ibl_layout = QGridLayout(ibl_group)
        
        # Включение IBL
        self.ibl_enabled = QCheckBox("Включить IBL")
        self.ibl_enabled.setChecked(self.current_graphics['ibl_enabled'])
        self.ibl_enabled.toggled.connect(self.on_ibl_toggled)
        ibl_layout.addWidget(self.ibl_enabled, 0, 0, 1, 2)
        
        # Интенсивность IBL
        ibl_layout.addWidget(QLabel("Интенсивность:"), 1, 0)
        self.ibl_intensity = QDoubleSpinBox()
        self.ibl_intensity.setRange(0.0, 3.0)
        self.ibl_intensity.setSingleStep(0.1)
        self.ibl_intensity.setDecimals(1)
        self.ibl_intensity.setValue(self.current_graphics['ibl_intensity'])
        self.ibl_intensity.valueChanged.connect(self.on_ibl_intensity_changed)
        ibl_layout.addWidget(self.ibl_intensity, 1, 1)
        
        layout.addWidget(ibl_group)
        
        # Туман (существующий код)
        fog_group = QGroupBox("🌫️ Туман")
        fog_layout = QGridLayout(fog_group)
        
        # Включение тумана
        self.fog_enabled = QCheckBox("Включить туман")
        self.fog_enabled.setChecked(self.current_graphics['fog_enabled'])
        self.fog_enabled.toggled.connect(self.on_fog_toggled)
        fog_layout.addWidget(self.fog_enabled, 0, 0, 1, 2)
        
        # Цвет тумана
        fog_layout.addWidget(QLabel("Цвет тумана:"), 1, 0)
        self.fog_color = ColorButton(self.current_graphics['fog_color'])
        self.fog_color.color_changed.connect(self.on_fog_color_changed)
        fog_layout.addWidget(self.fog_color, 1, 1)
        
        # Плотность тумана
        fog_layout.addWidget(QLabel("Плотность:"), 1, 2)
        self.fog_density = QDoubleSpinBox()
        self.fog_density.setRange(0.0, 1.0)
        self.fog_density.setSingleStep(0.01)
        self.fog_density.setDecimals(2)
        self.fog_density.setValue(self.current_graphics['fog_density'])
        self.fog_density.valueChanged.connect(self.on_fog_density_changed)
        fog_layout.addWidget(self.fog_density, 1, 3)
        
        layout.addWidget(fog_group)
        
        # ✅ РАСШИРЕННОЕ Качество рендеринга (с мягкостью теней)
        quality_group = QGroupBox("⚙️ Качество рендеринга")
        quality_layout = QGridLayout(quality_group)
        
        # Антиалиасинг
        quality_layout.addWidget(QLabel("Сглаживание:"), 0, 0)
        self.antialiasing = QComboBox()
        self.antialiasing.addItems(["Выкл", "SSAA", "MSAA"])
        self.antialiasing.setCurrentIndex(self.current_graphics['antialiasing'])
        self.antialiasing.currentIndexChanged.connect(self.on_antialiasing_changed)
        quality_layout.addWidget(self.antialiasing, 0, 1)
        
        # Качество сглаживания
        quality_layout.addWidget(QLabel("Качество:"), 0, 2)
        self.aa_quality = QComboBox()
        self.aa_quality.addItems(["Низкое", "Среднее", "Высокое"])
        self.aa_quality.setCurrentIndex(self.current_graphics['aa_quality'])
        self.aa_quality.currentIndexChanged.connect(self.on_aa_quality_changed)
        quality_layout.addWidget(self.aa_quality, 0, 3)
        
        # Тени
        self.shadows_enabled = QCheckBox("Включить тени")
        self.shadows_enabled.setChecked(self.current_graphics['shadows_enabled'])
        self.shadows_enabled.toggled.connect(self.on_shadows_toggled)
        quality_layout.addWidget(self.shadows_enabled, 1, 0, 1, 2)
        
        # Качество теней
        quality_layout.addWidget(QLabel("Качество теней:"), 1, 2)
        self.shadow_quality = QComboBox()
        self.shadow_quality.addItems(["Низкое", "Среднее", "Высокое"])
        self.shadow_quality.setCurrentIndex(self.current_graphics['shadow_quality'])
        self.shadow_quality.currentIndexChanged.connect(self.on_shadow_quality_changed)
        quality_layout.addWidget(self.shadow_quality, 1, 3)
        
        # ✅ НОВОЕ: Мягкость теней
        quality_layout.addWidget(QLabel("Мягкость теней:"), 2, 0)
        self.shadow_softness = QDoubleSpinBox()
        self.shadow_softness.setRange(0.0, 2.0)
        self.shadow_softness.setSingleStep(0.1)
        self.shadow_softness.setDecimals(1)
        self.shadow_softness.setValue(self.current_graphics['shadow_softness'])
        self.shadow_softness.valueChanged.connect(self.on_shadow_softness_changed)
        quality_layout.addWidget(self.shadow_softness, 2, 1)
        
        layout.addWidget(quality_group)
        
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def create_effects_tab(self):
        """Создать вкладку визуальных эффектов (РАСШИРЕННАЯ)"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # ✅ РАСШИРЕННЫЕ Пост-эффекты
        post_group = QGroupBox("✨ Пост-эффекты")
        post_layout = QGridLayout(post_group)
        
        # Bloom (свечение)
        self.bloom_enabled = QCheckBox("Bloom (свечение)")
        self.bloom_enabled.setChecked(self.current_graphics['bloom_enabled'])
        self.bloom_enabled.toggled.connect(self.on_bloom_toggled)
        post_layout.addWidget(self.bloom_enabled, 0, 0, 1, 2)
        
        # Интенсивность bloom
        post_layout.addWidget(QLabel("Интенсивность:"), 0, 2)
        self.bloom_intensity = QDoubleSpinBox()
        self.bloom_intensity.setRange(0.0, 2.0)
        self.bloom_intensity.setSingleStep(0.1)
        self.bloom_intensity.setDecimals(1)
        self.bloom_intensity.setValue(self.current_graphics['bloom_intensity'])
        self.bloom_intensity.valueChanged.connect(self.on_bloom_intensity_changed)
        post_layout.addWidget(self.bloom_intensity, 0, 3)
        
        # ✅ НОВОЕ: Порог Bloom
        post_layout.addWidget(QLabel("Порог Bloom:"), 0, 4)
        self.bloom_threshold = QDoubleSpinBox()
        self.bloom_threshold.setRange(0.0, 3.0)
        self.bloom_threshold.setSingleStep(0.1)
        self.bloom_threshold.setDecimals(1)
        self.bloom_threshold.setValue(self.current_graphics['bloom_threshold'])
        self.bloom_threshold.valueChanged.connect(self.on_bloom_threshold_changed)
        post_layout.addWidget(self.bloom_threshold, 0, 5)
        
        # SSAO (Screen Space Ambient Occlusion)
        self.ssao_enabled = QCheckBox("SSAO (затенение)")
        self.ssao_enabled.setChecked(self.current_graphics['ssao_enabled'])
        self.ssao_enabled.toggled.connect(self.on_ssao_toggled)
        post_layout.addWidget(self.ssao_enabled, 1, 0, 1, 2)
        
        # Интенсивность SSAO
        post_layout.addWidget(QLabel("Интенсивность:"), 1, 2)
        self.ssao_intensity = QDoubleSpinBox()
        self.ssao_intensity.setRange(0.0, 2.0)
        self.ssao_intensity.setSingleStep(0.1)
        self.ssao_intensity.setDecimals(1)
        self.ssao_intensity.setValue(self.current_graphics['ssao_intensity'])
        self.ssao_intensity.valueChanged.connect(self.on_ssao_intensity_changed)
        post_layout.addWidget(self.ssao_intensity, 1, 3)
        
        # ✅ НОВОЕ: Радиус SSAO
        post_layout.addWidget(QLabel("Радиус SSAO:"), 1, 4)
        self.ssao_radius = QDoubleSpinBox()
        self.ssao_radius.setRange(1.0, 20.0)
        self.ssao_radius.setSingleStep(1.0)
        self.ssao_radius.setDecimals(1)
        self.ssao_radius.setValue(self.current_graphics['ssao_radius'])
        self.ssao_radius.valueChanged.connect(self.on_ssao_radius_changed)
        post_layout.addWidget(self.ssao_radius, 1, 5)
        
        # Motion Blur
        self.motion_blur = QCheckBox("Motion Blur (размытие движения)")
        self.motion_blur.setChecked(self.current_graphics['motion_blur'])
        self.motion_blur.toggled.connect(self.on_motion_blur_toggled)
        post_layout.addWidget(self.motion_blur, 2, 0, 1, 6)
        
        # Depth of Field
        self.depth_of_field = QCheckBox("Depth of Field (глубина резкости)")
        self.depth_of_field.setChecked(self.current_graphics['depth_of_field'])
        self.depth_of_field.toggled.connect(self.on_depth_of_field_toggled)
        post_layout.addWidget(self.depth_of_field, 3, 0, 1, 2)
        
        # ✅ НОВОЕ: Дистанция фокуса DoF
        post_layout.addWidget(QLabel("Дистанция фокуса:"), 3, 2)
        self.dof_focus_distance = QSpinBox()
        self.dof_focus_distance.setRange(100, 10000)
        self.dof_focus_distance.setSingleStep(100)
        self.dof_focus_distance.setSuffix("мм")
        self.dof_focus_distance.setValue(int(self.current_graphics['dof_focus_distance']))
        self.dof_focus_distance.valueChanged.connect(self.on_dof_focus_distance_changed)
        post_layout.addWidget(self.dof_focus_distance, 3, 3)
        
        # ✅ НОВОЕ: Диапазон фокуса DoF
        post_layout.addWidget(QLabel("Диапазон фокуса:"), 3, 4)
        self.dof_focus_range = QSpinBox()
        self.dof_focus_range.setRange(100, 5000)
        self.dof_focus_range.setSingleStep(100)
        self.dof_focus_range.setSuffix("мм")
        self.dof_focus_range.setValue(int(self.current_graphics['dof_focus_range']))
        self.dof_focus_range.valueChanged.connect(self.on_dof_focus_range_changed)
        post_layout.addWidget(self.dof_focus_range, 3, 5)
        
        layout.addWidget(post_group)
        
        # ✅ НОВОЕ: Тонемаппинг группа
        tonemap_group = QGroupBox("🎨 Тонемаппинг")
        tonemap_layout = QGridLayout(tonemap_group)
        
        # Включение тонемаппинга
        self.tonemap_enabled = QCheckBox("Включить тонемаппинг")
        self.tonemap_enabled.setChecked(self.current_graphics['tonemap_enabled'])
        self.tonemap_enabled.toggled.connect(self.on_tonemap_toggled)
        tonemap_layout.addWidget(self.tonemap_enabled, 0, 0, 1, 2)
        
        # Режим тонемаппинга
        tonemap_layout.addWidget(QLabel("Режим:"), 0, 2)
        self.tonemap_mode = QComboBox()
        self.tonemap_mode.addItems(["None", "Linear", "Reinhard", "Filmic"])
        self.tonemap_mode.setCurrentIndex(self.current_graphics['tonemap_mode'])
        self.tonemap_mode.currentIndexChanged.connect(self.on_tonemap_mode_changed)
        tonemap_layout.addWidget(self.tonemap_mode, 0, 3)
        
        layout.addWidget(tonemap_group)
        
        # ✅ НОВОЕ: Виньетирование группа
        vignette_group = QGroupBox("🖼️ Виньетирование")
        vignette_layout = QGridLayout(vignette_group)
        
        # Включение виньетирования
        self.vignette_enabled = QCheckBox("Включить виньетирование")
        self.vignette_enabled.setChecked(self.current_graphics['vignette_enabled'])
        self.vignette_enabled.toggled.connect(self.on_vignette_toggled)
        vignette_layout.addWidget(self.vignette_enabled, 0, 0, 1, 2)
        
        # Сила виньетирования
        vignette_layout.addWidget(QLabel("Сила:"), 0, 2)
        self.vignette_strength = QDoubleSpinBox()
        self.vignette_strength.setRange(0.0, 1.0)
        self.vignette_strength.setSingleStep(0.05)
        self.vignette_strength.setDecimals(2)
        self.vignette_strength.setValue(self.current_graphics['vignette_strength'])
        self.vignette_strength.valueChanged.connect(self.on_vignette_strength_changed)
        vignette_layout.addWidget(self.vignette_strength, 0, 3)
        
        layout.addWidget(vignette_group)
        
        # ✅ НОВОЕ: Дополнительные эффекты группа
        additional_group = QGroupBox("🌟 Дополнительные эффекты")
        additional_layout = QGridLayout(additional_group)
        
        # Lens Flare
        self.lens_flare_enabled = QCheckBox("Lens Flare (блики)")
        self.lens_flare_enabled.setChecked(self.current_graphics['lens_flare_enabled'])
        self.lens_flare_enabled.toggled.connect(self.on_lens_flare_toggled)
        additional_layout.addWidget(self.lens_flare_enabled, 0, 0, 1, 4)
        
        layout.addWidget(additional_group)
        
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def create_camera_tab(self):
        """Создать вкладку настроек камеры"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        widget = QWidget()
        layout = QVBoxLayout(widget)

        cam_group = QGroupBox("📷 Камера")
        cam_layout = QGridLayout(cam_group)

        # FOV
        cam_layout.addWidget(QLabel("Поле зрения (FOV):"), 0, 0)
        self.camera_fov = QDoubleSpinBox()
        self.camera_fov.setRange(1.0, 120.0)
        self.camera_fov.setSingleStep(1.0)
        self.camera_fov.setDecimals(1)
        self.camera_fov.setValue(self.current_graphics.get('camera_fov', 45.0))
        self.camera_fov.valueChanged.connect(self.on_camera_fov_changed)
        cam_layout.addWidget(self.camera_fov, 0, 1)

        # Near
        cam_layout.addWidget(QLabel("Ближняя плоскость (near):"), 1, 0)
        self.camera_near = QDoubleSpinBox()
        self.camera_near.setRange(0.1, 1000.0)
        self.camera_near.setSingleStep(0.1)
        self.camera_near.setDecimals(1)
        self.camera_near.setValue(self.current_graphics.get('camera_near', 10.0))
        self.camera_near.valueChanged.connect(self.on_camera_near_changed)
        cam_layout.addWidget(self.camera_near, 1, 1)

        # Far
        cam_layout.addWidget(QLabel("Дальняя плоскость (far):"), 2, 0)
        self.camera_far = QSpinBox()
        self.camera_far.setRange(100, 1000000)
        self.camera_far.setSingleStep(100)
        self.camera_far.setValue(int(self.current_graphics.get('camera_far', 50000)))
        self.camera_far.valueChanged.connect(self.on_camera_far_changed)
        cam_layout.addWidget(self.camera_far, 2, 1)

        # Camera speed
        cam_layout.addWidget(QLabel("Скорость камеры:"), 3, 0)
        self.camera_speed = QDoubleSpinBox()
        self.camera_speed.setRange(0.01, 10.0)
        self.camera_speed.setSingleStep(0.1)
        self.camera_speed.setDecimals(2)
        self.camera_speed.setValue(self.current_graphics.get('camera_speed', 1.0))
        self.camera_speed.valueChanged.connect(self.on_camera_speed_changed)
        cam_layout.addWidget(self.camera_speed, 3, 1)

        # Auto-rotate
        self.auto_rotate = QCheckBox("Автовращение")
        self.auto_rotate.setChecked(self.current_graphics.get('auto_rotate', False))
        self.auto_rotate.toggled.connect(self.on_auto_rotate_toggled)
        cam_layout.addWidget(self.auto_rotate, 4, 0, 1, 2)

        # Auto-rotate speed
        cam_layout.addWidget(QLabel("Скорость автовращения:"), 5, 0)
        self.auto_rotate_speed = QDoubleSpinBox()
        self.auto_rotate_speed.setRange(0.01, 10.0)
        self.auto_rotate_speed.setSingleStep(0.1)
        self.auto_rotate_speed.setDecimals(2)
        self.auto_rotate_speed.setValue(self.current_graphics.get('auto_rotate_speed', 0.5))
        self.auto_rotate_speed.valueChanged.connect(self.on_auto_rotate_speed_changed)
        cam_layout.addWidget(self.auto_rotate_speed, 5, 1)

        layout.addWidget(cam_group)
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    # ================================================================= 
    # ✅ НОВЫЕ Обработчики событий (New Event Handlers)
    # =================================================================
    
    # IBL handlers
    @Slot(bool)
    def on_ibl_toggled(self, enabled: bool):
        """Включение/выключение IBL"""
        self.current_graphics['ibl_enabled'] = enabled
        self.emit_environment_update()
    
    @Slot(float)
    def on_ibl_intensity_changed(self, value: float):
        """Изменение интенсивности IBL"""
        self.current_graphics['ibl_intensity'] = value
        self.emit_environment_update()
    
    # Glass IOR handler
    @Slot(float)
    def on_glass_ior_changed(self, value: float):
        """Изменение коэффициента преломления стекла"""
        self.current_graphics['glass_ior'] = value
        self.emit_material_update()
        self.logger.info(f"Glass IOR changed to: {value}")
    
    # Shadow softness handler
    @Slot(float)
    def on_shadow_softness_changed(self, value: float):
        """Изменение мягкости теней"""
        self.current_graphics['shadow_softness'] = value
        self.emit_quality_update()
    
    # Extended Bloom handlers
    @Slot(float)
    def on_bloom_threshold_changed(self, value: float):
        """Изменение порога Bloom"""
        self.current_graphics['bloom_threshold'] = value
        self.emit_effects_update()
    
    # Extended SSAO handlers
    @Slot(float)
    def on_ssao_radius_changed(self, value: float):
        """Изменение радиуса SSAO"""
        self.current_graphics['ssao_radius'] = value
        self.emit_effects_update()
    
    # Tonemap handlers
    @Slot(bool)
    def on_tonemap_toggled(self, enabled: bool):
        """Включение/выключение тонемаппинга"""
        self.current_graphics['tonemap_enabled'] = enabled
        self.emit_effects_update()
    
    @Slot(int)
    def on_tonemap_mode_changed(self, index: int):
        """Изменение режима тонемаппинга"""
        self.current_graphics['tonemap_mode'] = index
        self.emit_effects_update()
    
    # DoF handlers
    @Slot(int)
    def on_dof_focus_distance_changed(self, value: int):
        """Изменение дистанции фокуса DoF"""
        self.current_graphics['dof_focus_distance'] = value
        self.emit_effects_update()
    
    @Slot(int)
    def on_dof_focus_range_changed(self, value: int):
        """Изменение диапазона фокуса DoF"""
        self.current_graphics['dof_focus_range'] = value
        self.emit_effects_update()
    
    # Vignette handlers
    @Slot(bool)
    def on_vignette_toggled(self, enabled: bool):
        """Включение/выключение виньетирования"""
        self.current_graphics['vignette_enabled'] = enabled
        self.emit_effects_update()
    
    @Slot(float)
    def on_vignette_strength_changed(self, value: float):
        """Изменение силы виньетирования"""
        self.current_graphics['vignette_strength'] = value
        self.emit_effects_update()
    
    # Lens Flare handler
    @Slot(bool)
    def on_lens_flare_toggled(self, enabled: bool):
        """Включение/выключение Lens Flare"""
        self.current_graphics['lens_flare_enabled'] = enabled
        self.emit_effects_update()

    # =================================================================
    # Методы генерации сигналов (Signal Emitters)
    # =================================================================
    
    def emit_lighting_update(self):
        """Отправить сигнал об изменении освещения"""
        lighting_params = {
            'key_light': {
                'brightness': self.current_graphics['key_brightness'],
                'color': self.current_graphics['key_color'],
                'angle_x': self.current_graphics['key_angle_x'],
                'angle_y': self.current_graphics['key_angle_y']
            },
            'fill_light': {
                'brightness': self.current_graphics['fill_brightness'],
                'color': self.current_graphics['fill_color']
            },
            'point_light': {
                'brightness': self.current_graphics['point_brightness'],
                'color': self.current_graphics['point_color'],
                'position_y': self.current_graphics['point_y']
            }
        }
        
        self.logger.info(f"Lighting updated: {lighting_params}")
        self.lighting_changed.emit(lighting_params)
    
    def emit_material_update(self):
        """Отправить сигнал об изменении материалов (РАСШИРЕННЫЙ)"""
        material_params = {
            'metal': {
                'roughness': self.current_graphics['metal_roughness'],
                'metalness': self.current_graphics['metal_metalness'],
                'clearcoat': self.current_graphics['metal_clearcoat']
            },
            'glass': {
                'opacity': self.current_graphics['glass_opacity'],
                'roughness': self.current_graphics['glass_roughness'],
                'ior': self.current_graphics['glass_ior']  # ✅ НОВОЕ: IOR
            },
            'frame': {
                'metalness': self.current_graphics['frame_metalness'],
                'roughness': self.current_graphics['frame_roughness']
            }
        }
        
        self.logger.info(f"Materials updated (with IOR): {material_params}")
        self.material_changed.emit(material_params)
    
    def emit_environment_update(self):
        """Отправить сигнал об изменении окружения (РАСШИРЕННЫЙ)"""
        env_params = {
            'background_color': self.current_graphics['background_color'],
            'fog_enabled': self.current_graphics['fog_enabled'],
            'fog_color': self.current_graphics['fog_color'],
            'fog_density': self.current_graphics['fog_density'],
            'skybox_enabled': self.current_graphics['skybox_enabled'],
            'ibl_enabled': self.current_graphics['ibl_enabled'],    # ✅ НОВОЕ: IBL
            'ibl_intensity': self.current_graphics['ibl_intensity']  # ✅ НОВОЕ: IBL
        }
        
        self.logger.info(f"Environment updated (with IBL): {env_params}")
        self.environment_changed.emit(env_params)
    
    def emit_quality_update(self):
        """Отправить сигнал об изменении качества (РАСШИРЕННЫЙ)"""
        quality_params = {
            'antialiasing': self.current_graphics['antialiasing'],
            'aa_quality': self.current_graphics['aa_quality'],
            'shadows_enabled': self.current_graphics['shadows_enabled'],
            'shadow_quality': self.current_graphics['shadow_quality'],
            'shadow_softness': self.current_graphics['shadow_softness']  # ✅ НОВОЕ: Мягкость теней
        }
        
        self.logger.info(f"Quality updated (with shadow softness): {quality_params}")
        self.quality_changed.emit(quality_params)
    
    def emit_camera_update(self):
        """Отправить сигнал об изменении настроек камеры"""
        camera_params = {
            'fov': self.current_graphics['camera_fov'],
            'near': self.current_graphics['camera_near'],
            'far': self.current_graphics['camera_far'],
            'speed': self.current_graphics['camera_speed'],
            'auto_rotate': self.current_graphics['auto_rotate'],
            'auto_rotate_speed': self.current_graphics['auto_rotate_speed']
        }
        
        self.logger.info(f"Camera updated: {camera_params}")
        self.camera_changed.emit(camera_params)
    
    def emit_effects_update(self):
        """Отправить сигнал об изменении эффектов (РАСШИРЕННЫЙ)"""
        effects_params = {
            'bloom_enabled': self.current_graphics['bloom_enabled'],
            'bloom_intensity': self.current_graphics['bloom_intensity'],
            'bloom_threshold': self.current_graphics['bloom_threshold'],  # ✅ НОВОЕ
            'ssao_enabled': self.current_graphics['ssao_enabled'],
            'ssao_intensity': self.current_graphics['ssao_intensity'],
            'ssao_radius': self.current_graphics['ssao_radius'],          # ✅ НОВОЕ
            'motion_blur': self.current_graphics['motion_blur'],
            'depth_of_field': self.current_graphics['depth_of_field'],
            'dof_focus_distance': self.current_graphics['dof_focus_distance'],  # ✅ НОВОЕ
            'dof_focus_range': self.current_graphics['dof_focus_range'],        # ✅ НОВОЕ
            'tonemap_enabled': self.current_graphics['tonemap_enabled'],        # ✅ НОВОЕ
            'tonemap_mode': self.current_graphics['tonemap_mode'],              # ✅ НОВОЕ
            'vignette_enabled': self.current_graphics['vignette_enabled'],      # ✅ НОВОЕ
            'vignette_strength': self.current_graphics['vignette_strength'],    # ✅ НОВОЕ
            'lens_flare_enabled': self.current_graphics['lens_flare_enabled']   # ✅ НОВОЕ
        }
        
        self.logger.info(f"Effects updated (EXPANDED): {effects_params}")
        self.effects_changed.emit(effects_params)

    def update_ui_from_current_settings(self):
        """Обновить UI элементы из текущих настроек (РАСШИРЕННЫЙ)"""
        # Блокируем сигналы во время обновления
        widgets = [
            # Освещение
            self.key_brightness, self.key_color, self.key_angle_x, self.key_angle_y,
            self.fill_brightness, self.fill_color, self.point_brightness, self.point_y,
            # Материалы
            self.metal_roughness, self.metal_metalness, self.metal_clearcoat,
            self.glass_opacity, self.glass_roughness, self.glass_ior,  # ✅ НОВОЕ: IOR
            self.frame_metalness, self.frame_roughness,
            # Окружение
            self.background_color, self.fog_color, self.fog_density,
            self.ibl_intensity,  # ✅ НОВОЕ: IBL
            self.shadow_softness,  # ✅ НОВОЕ: Мягкость теней
            # Камера
            self.camera_fov, self.camera_speed, self.camera_near, self.camera_far,
            self.auto_rotate_speed,
            # Эффекты
            self.bloom_intensity, self.bloom_threshold,  # ✅ НОВОЕ: Порог
            self.ssao_intensity, self.ssao_radius,      # ✅ НОВОЕ: Радиус
            self.dof_focus_distance, self.dof_focus_range,  # ✅ НОВОЕ: DoF
            self.vignette_strength  # ✅ НОВОЕ: Виньетирование
        ]
        
        for widget in widgets:
            if hasattr(widget, 'blockSignals'):
                widget.blockSignals(True)
        
        try:
            # Освещение
            self.key_brightness.setValue(self.current_graphics['key_brightness'])
            self.key_color.set_color(self.current_graphics['key_color'])
            self.key_angle_x.setValue(self.current_graphics['key_angle_x'])
            self.key_angle_y.setValue(self.current_graphics['key_angle_y'])
            self.fill_brightness.setValue(self.current_graphics['fill_brightness'])
            self.fill_color.set_color(self.current_graphics['fill_color'])
            self.point_brightness.setValue(int(self.current_graphics['point_brightness']))
            self.point_y.setValue(int(self.current_graphics['point_y']))
            
            # Материалы
            self.metal_roughness.setValue(self.current_graphics['metal_roughness'])
            self.metal_metalness.setValue(self.current_graphics['metal_metalness'])
            self.metal_clearcoat.setValue(self.current_graphics['metal_clearcoat'])
            self.glass_opacity.setValue(self.current_graphics['glass_opacity'])
            self.glass_roughness.setValue(self.current_graphics['glass_roughness'])
            self.glass_ior.setValue(self.current_graphics['glass_ior'])
            
            # Окружение
            self.background_color.set_color(self.current_graphics['background_color'])
            self.fog_enabled.setChecked(self.current_graphics['fog_enabled'])
            self.fog_color.set_color(self.current_graphics['fog_color'])
            self.fog_density.setValue(self.current_graphics['fog_density'])
            self.skybox_enabled.setChecked(self.current_graphics['skybox_enabled'])
            self.antialiasing.setCurrentIndex(self.current_graphics['antialiasing'])
            self.aa_quality.setCurrentIndex(self.current_graphics['aa_quality'])
            self.shadows_enabled.setChecked(self.current_graphics['shadows_enabled'])
            self.shadow_quality.setCurrentIndex(self.current_graphics['shadow_quality'])
            
            # Камера
            self.camera_fov.setValue(self.current_graphics['camera_fov'])
            self.camera_speed.setValue(self.current_graphics['camera_speed'])
            self.camera_near.setValue(self.current_graphics['camera_near'])
            self.camera_far.setValue(int(self.current_graphics['camera_far']))
            self.auto_rotate.setChecked(self.current_graphics['auto_rotate'])
            self.auto_rotate_speed.setValue(self.current_graphics['auto_rotate_speed'])
            
            # Эффекты
            self.bloom_enabled.setChecked(self.current_graphics['bloom_enabled'])
            self.bloom_intensity.setValue(self.current_graphics['bloom_intensity'])
            self.bloom_threshold.setValue(self.current_graphics['bloom_threshold'])
            self.ssao_enabled.setChecked(self.current_graphics['ssao_enabled'])
            self.ssao_intensity.setValue(self.current_graphics['ssao_intensity'])
            self.ssao_radius.setValue(self.current_graphics['ssao_radius'])
            self.motion_blur.setChecked(self.current_graphics['motion_blur'])
            self.depth_of_field.setChecked(self.current_graphics['depth_of_field'])
            self.dof_focus_distance.setValue(int(self.current_graphics['dof_focus_distance']))
            self.dof_focus_range.setValue(int(self.current_graphics['dof_focus_range']))
            self.tonemap_enabled.setChecked(self.current_graphics['tonemap_enabled'])
            self.tonemap_mode.setCurrentIndex(self.current_graphics['tonemap_mode'])
            self.vignette_enabled.setChecked(self.current_graphics['vignette_enabled'])
            self.vignette_strength.setValue(self.current_graphics['vignette_strength'])
            self.lens_flare_enabled.setChecked(self.current_graphics['lens_flare_enabled'])
            
        finally:
            # Разблокируем сигналы
            for widget in widgets:
                if hasattr(widget, 'blockSignals'):
                    widget.blockSignals(False)

    def reset_to_defaults(self):
        """Сбросить настройки к значениям по умолчанию (РАСШИРЕННЫЙ)"""
        self.logger.info("Resetting graphics to defaults (EXPANDED)")
        
        # ✅ РАСШИРЕННЫЙ сброс к начальным значениям
        self.current_graphics = {
            # Освещение
            'key_brightness': 2.8,
            'key_color': '#ffffff',
            'key_angle_x': -30,
            'key_angle_y': -45,
            'fill_brightness': 1.2,
            'fill_color': '#f0f0ff',
            'rim_brightness': 1.5,
            'rim_color': '#ffffcc',
            'point_brightness': 20000,
            'point_color': '#ffffff',
            'point_y': 1800,
            'point_fade': 0.00008,
            
            # Окружение и IBL
            'background_color': '#2a2a2a',
            'fog_enabled': False,
            'fog_color': '#808080',
            'fog_density': 0.1,
            'skybox_enabled': False,
            'skybox_blur': 0.0,
            'ibl_enabled': True,
            'ibl_intensity': 1.0,
            
            # Качество рендеринга
            'antialiasing': 2,
            'aa_quality': 2,
            'shadows_enabled': True,
            'shadow_quality': 1,
            'shadow_softness': 0.5,
            
            # Материалы
            'metal_roughness': 0.28,
            'metal_metalness': 1.0,
            'metal_clearcoat': 0.25,
            'glass_opacity': 0.35,
            'glass_roughness': 0.05,
            'glass_ior': 1.52,  # ✅ Стекло по умолчанию
            'frame_metalness': 0.8,
            'frame_roughness': 0.4,
            
            # Камера
            'camera_fov': 45.0,
            'camera_near': 10.0,
            'camera_far': 50000.0,
            'camera_speed': 1.0,
            'auto_rotate': False,
            'auto_rotate_speed': 0.5,
            
            # Эффекты - РАСШИРЕННЫЕ
            'bloom_enabled': False,
            'bloom_intensity': 0.3,
            'bloom_threshold': 1.0,
            'ssao_enabled': False,
            'ssao_intensity': 0.5,
            'ssao_radius': 8.0,
            'motion_blur': False,
            'depth_of_field': False,
            'dof_focus_distance': 2000,
            'dof_focus_range': 900,
            'tonemap_enabled': True,
            'tonemap_mode': 3,  # Filmic
            'vignette_enabled': True,
            'vignette_strength': 0.45,
            'lens_flare_enabled': True,
        }
        
        # Обновить UI
        self.update_ui_from_current_settings()
        
        # Отправить все сигналы
        self.emit_lighting_update()
        self.emit_material_update()
        self.emit_environment_update()
        self.emit_quality_update()
        self.emit_camera_update()
        self.emit_effects_update()
    
    def save_settings(self):
        """Сохранить настройки в QSettings"""
        self.logger.info("Saving graphics settings")
        
        for key, value in self.current_graphics.items():
            self.settings.setValue(f"graphics/{key}", value)
        
        self.settings.sync()
        self.logger.info(f"Saved {len(self.current_graphics)} graphics parameters")
    
    def load_settings(self):
        """Загрузить настройки из QSettings (РАСШИРЕННЫЙ)"""
        self.logger.info("Loading graphics settings (EXPANDED)")
        
        for key in self.current_graphics.keys():
            saved_value = self.settings.value(f"graphics/{key}")
            if saved_value is not None:
                # Конвертируем типы для ВСЕХ новых параметров
                if key in ['key_brightness', 'fill_brightness', 'rim_brightness', 'point_fade',
                          'fog_density', 'metal_roughness', 'metal_metalness', 'metal_clearcoat',
                          'glass_opacity', 'glass_roughness', 'glass_ior',  # ✅ НОВОЕ: IOR
                          'frame_metalness', 'frame_roughness',
                          'camera_fov', 'camera_near', 'camera_speed', 'auto_rotate_speed',
                          'bloom_intensity', 'bloom_threshold',  # ✅ НОВОЕ: Threshold
                          'ssao_intensity', 'ssao_radius',      # ✅ НОВОЕ: Radius
                          'shadow_softness',                    # ✅ НОВОЕ: Softness
                          'vignette_strength',                  # ✅ НОВОЕ: Vignette
                          'ibl_intensity']:                     # ✅ НОВОЕ: IBL
                    self.current_graphics[key] = float(saved_value)
                elif key in ['key_angle_x', 'key_angle_y', 'point_brightness', 'point_y',
                            'antialiasing', 'aa_quality', 'shadow_quality', 'camera_far',
                            'tonemap_mode',                      # ✅ НОВОЕ: Tonemap mode
                            'dof_focus_distance', 'dof_focus_range']:  # ✅ НОВОЕ: DoF
                    self.current_graphics[key] = int(saved_value)
                elif key in ['fog_enabled', 'skybox_enabled', 'shadows_enabled', 'auto_rotate',
                            'bloom_enabled', 'ssao_enabled', 'motion_blur', 'depth_of_field',
                            'ibl_enabled',                       # ✅ НОВОЕ: IBL
                            'tonemap_enabled',                   # ✅ НОВОЕ: Tonemap
                            'vignette_enabled',                  # ✅ НОВОЕ: Vignette
                            'lens_flare_enabled']:               # ✅ НОВОЕ: Lens Flare
                    self.current_graphics[key] = bool(saved_value == 'true' or saved_value == True)
                else:
                    self.current_graphics[key] = str(saved_value)
        
        # Обновить UI после загрузки
        if hasattr(self, 'key_brightness'):  # UI уже создан
            self.update_ui_from_current_settings()
    
    @Slot(str)
    def export_graphics_settings(self):
        """Экспорт настроек в файл"""
        from PySide6.QtWidgets import QFileDialog
        import json
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт настроек графики", 
            "graphics_settings.json", 
            "JSON файлы (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_graphics, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Graphics settings exported to {file_path}")
            except Exception as e:
                self.logger.error(f"Export failed: {e}")
    
    @Slot()
    def import_graphics_settings(self):
        """Импорт настроек из файла"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import json
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Импорт настроек графики", 
            "", 
            "JSON файлы (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_settings = json.load(f)
                
                # Применить импортированные настройки
                self.current_graphics.update(imported_settings)
                self.update_ui_from_current_settings()
                
                # Отправить все сигналы
                self.emit_lighting_update()
                self.emit_material_update()
                self.emit_environment_update()
                self.emit_quality_update()
                self.emit_camera_update()
                self.emit_effects_update()
                
                self.logger.info(f"Graphics settings imported from {file_path}")
                QMessageBox.information(self, "Импорт завершен", 
                                      f"Настройки графики успешно импортированы из:\n{file_path}")
                
            except Exception as e:
                self.logger.error(f"Import failed: {e}")
                QMessageBox.critical(self, "Ошибка импорта", 
                                   f"Не удалось импортировать настройки:\n{e}")
    

    # =================================================================
    # Обработчики событий освещения (Event Handlers - Lighting)
    # =================================================================
    
    @Slot(float)
    def on_key_brightness_changed(self, value: float):
        """Изменение яркости основного света"""
        self.current_graphics['key_brightness'] = value
        self.emit_lighting_update()
    
    @Slot(str)
    def on_key_color_changed(self, color: str):
        """Изменение цвета основного света"""
        self.current_graphics['key_color'] = color
        self.emit_lighting_update()
    
    @Slot(int)
    def on_key_angle_x_changed(self, angle: int):
        """Изменение угла наклона основного света"""
        self.current_graphics['key_angle_x'] = angle
        self.emit_lighting_update()
    
    @Slot(int)
    def on_key_angle_y_changed(self, angle: int):
        """Изменение угла поворота основного света"""
        self.current_graphics['key_angle_y'] = angle
        self.emit_lighting_update()
    
    @Slot(float)
    def on_fill_brightness_changed(self, value: float):
        """Изменение яркости заполняющего света"""
        self.current_graphics['fill_brightness'] = value
        self.emit_lighting_update()
    
    @Slot(str)
    def on_fill_color_changed(self, color: str):
        """Изменение цвета заполняющего света"""
        self.current_graphics['fill_color'] = color
        self.emit_lighting_update()
    
    @Slot(int)
    def on_point_brightness_changed(self, value: int):
        """Изменение яркости точечного света"""
        self.current_graphics['point_brightness'] = value
        self.emit_lighting_update()
    
    @Slot(int)
    def on_point_y_changed(self, value: int):
        """Изменение высоты точечного света"""
        self.current_graphics['point_y'] = value
        self.emit_lighting_update()
    
    # =================================================================
    # Обработчики событий материалов (Event Handlers - Materials)
    # =================================================================
    
    @Slot(float)
    def on_metal_roughness_changed(self, value: float):
        """Изменение шероховатости металла"""
        self.current_graphics['metal_roughness'] = value
        self.emit_material_update()
    
    @Slot(float)
    def on_metal_metalness_changed(self, value: float):
        """Изменение металличности"""
        self.current_graphics['metal_metalness'] = value
        self.emit_material_update()
    
    @Slot(float)
    def on_metal_clearcoat_changed(self, value: float):
        """Изменение прозрачного покрытия"""
        self.current_graphics['metal_clearcoat'] = value
        self.emit_material_update()
    
    @Slot(float)
    def on_glass_opacity_changed(self, value: float):
        """Изменение прозрачности стекла"""
        self.current_graphics['glass_opacity'] = value
        self.emit_material_update()
    
    @Slot(float)
    def on_glass_roughness_changed(self, value: float):
        """Изменение шероховатости стекла"""
        self.current_graphics['glass_roughness'] = value
        self.emit_material_update()
    
    @Slot(float)
    def on_frame_metalness_changed(self, value: float):
        """Изменение металличности рамы"""
        self.current_graphics['frame_metalness'] = value
        self.emit_material_update()
    
    @Slot(float)
    def on_frame_roughness_changed(self, value: float):
        """Изменение шероховатости рамы"""
        self.current_graphics['frame_roughness'] = value
        self.emit_material_update()
    
    # =================================================================
    # Обработчики событий окружения (Event Handlers - Environment)
    # =================================================================
    
    @Slot(str)
    def on_background_color_changed(self, color: str):
        """Изменение цвета фона"""
        self.current_graphics['background_color'] = color
        self.emit_environment_update()
    
    @Slot(bool)
    def on_skybox_toggled(self, enabled: bool):
        """Включение/выключение Skybox"""
        self.current_graphics['skybox_enabled'] = enabled
        self.emit_environment_update()
    
    @Slot(bool)
    def on_fog_toggled(self, enabled: bool):
        """Включение/выключение тумана"""
        self.current_graphics['fog_enabled'] = enabled
        self.emit_environment_update()
    
    @Slot(str)
    def on_fog_color_changed(self, color: str):
        """Изменение цвета тумана"""
        self.current_graphics['fog_color'] = color
        self.emit_environment_update()
    
    @Slot(float)
    def on_fog_density_changed(self, value: float):
        """Изменение плотности тумана"""
        self.current_graphics['fog_density'] = value
        self.emit_environment_update()
    
    @Slot(int)
    def on_antialiasing_changed(self, index: int):
        """Изменение типа сглаживания"""
        self.current_graphics['antialiasing'] = index
        self.emit_quality_update()
    
    @Slot(int)
    def on_aa_quality_changed(self, index: int):
        """Изменение качества сглаживания"""
        self.current_graphics['aa_quality'] = index
        self.emit_quality_update()
    
    @Slot(bool)
    def on_shadows_toggled(self, enabled: bool):
        """Включение/выключение теней"""
        self.current_graphics['shadows_enabled'] = enabled
        self.emit_quality_update()
    
    @Slot(int)
    def on_shadow_quality_changed(self, index: int):
        """Изменение качества теней"""
        self.current_graphics['shadow_quality'] = index
        self.emit_quality_update()
    
    # =================================================================
    # Обработчики событий камеры (Event Handlers - Camera)
    # =================================================================
    
    @Slot(float)
    def on_camera_fov_changed(self, value: float):
        """Изменение поля зрения камеры"""
        self.current_graphics['camera_fov'] = value
        self.emit_camera_update()
    
    @Slot(float)
    def on_camera_speed_changed(self, value: float):
        """Изменение скорости камеры"""
        self.current_graphics['camera_speed'] = value
        self.emit_camera_update()
    
    @Slot(float)
    def on_camera_near_changed(self, value: float):
        """Изменение ближней плоскости отсечения"""
        self.current_graphics['camera_near'] = value
        self.emit_camera_update()
    
    @Slot(int)
    def on_camera_far_changed(self, value: int):
        """Изменение дальней плоскости отсечения"""
        self.current_graphics['camera_far'] = value
        self.emit_camera_update()
    
    @Slot(bool)
    def on_auto_rotate_toggled(self, enabled: bool):
        """Включение/выключение автоматического вращения"""
        self.current_graphics['auto_rotate'] = enabled
        self.emit_camera_update()
    
    @Slot(float)
    def on_auto_rotate_speed_changed(self, value: float):
        """Изменение скорости автоматического вращения"""
        self.current_graphics['auto_rotate_speed'] = value
        self.emit_camera_update()
    
    # =================================================================
    # Обработчики событий эффектов (Event Handlers - Effects)
    # =================================================================
    
    @Slot(bool)
    def on_bloom_toggled(self, enabled: bool):
        """Включение/выключение Bloom"""
        self.current_graphics['bloom_enabled'] = enabled
        self.emit_effects_update()
    
    @Slot(float)
    def on_bloom_intensity_changed(self, value: float):
        """Изменение интенсивности Bloom"""
        self.current_graphics['bloom_intensity'] = value
        self.emit_effects_update()
    
    @Slot(bool)
    def on_ssao_toggled(self, enabled: bool):
        """Включение/выключение SSAO"""
        self.current_graphics['ssao_enabled'] = enabled
        self.emit_effects_update()
    
    @Slot(float)
    def on_ssao_intensity_changed(self, value: float):
        """Изменение интенсивности SSAO"""
        self.current_graphics['ssao_intensity'] = value
        self.emit_effects_update()
    
    @Slot(bool)
    def on_motion_blur_toggled(self, enabled: bool):
        """Включение/выключение Motion Blur"""
        self.current_graphics['motion_blur'] = enabled
        self.emit_effects_update()
    
    @Slot(bool)
    def on_depth_of_field_toggled(self, enabled: bool):
        """Включение/выключение Depth of Field"""
        self.current_graphics['depth_of_field'] = enabled
        self.emit_effects_update()
    
    # =================================================================
    # Обработчики пресетов (Preset Handlers)
    # =================================================================
    
    @Slot(str)
    def apply_preset(self, preset_name: str):
        """Применить пресет освещения"""
        presets = {
            'day': {
                'key_brightness': 4.0,
                'key_color': '#ffffff',
                'key_angle_x': -15,
                'key_angle_y': -30,
                'fill_brightness': 2.0,
                'fill_color': '#f8f8ff'
            },
            'night': {
                'key_brightness': 1.0,
                'key_color': '#4444ff',
                'key_angle_x': -45,
                'key_angle_y': -60,
                'fill_brightness': 0.5,
                'fill_color': '#222244'
            },
            'industrial': {
                'key_brightness': 3.5,
                'key_color': '#ffeeaa',
                'key_angle_x': -25,
                'key_angle_y': -40,
                'fill_brightness': 1.5,
                'fill_color': '#fff8e0'
            }
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            # Применяем пресет к текущим настройкам
            self.current_graphics.update(preset)
            
            # Обновляем UI
            self.update_ui_from_current_settings()
            
            # Отправляем обновления
            self.emit_lighting_update()
            
            self.preset_applied.emit(preset_name)
            self.logger.info(f"Applied lighting preset: {preset_name}")
    
    # =================================================================
    # Кнопки управления (Control Buttons)
    # =================================================================
    
    def create_control_buttons(self, layout):
        """Создать кнопки управления внизу панели"""
        control_group = QGroupBox("🛠️ Управление настройками")
        control_layout = QHBoxLayout(control_group)
        
        # Кнопка сброса
        reset_btn = QPushButton("🔄 Сброс")
        reset_btn.setToolTip("Сбросить все настройки к значениям по умолчанию")
        reset_btn.clicked.connect(self.reset_to_defaults)
        control_layout.addWidget(reset_btn)
        
        # Кнопка сохранения
        save_btn = QPushButton("💾 Сохранить")
        save_btn.setToolTip("Сохранить текущие настройки")
        save_btn.clicked.connect(self.save_settings)
        control_layout.addWidget(save_btn)
        
        # Кнопка экспорта
        export_btn = QPushButton("📤 Экспорт")
        export_btn.setToolTip("Экспортировать настройки в файл")
        export_btn.clicked.connect(self.export_graphics_settings)
        control_layout.addWidget(export_btn)
        
        # Кнопка импорта
        import_btn = QPushButton("📥 Импорт")
        import_btn.setToolTip("Импортировать настройки из файла")
        import_btn.clicked.connect(self.import_graphics_settings)
        control_layout.addWidget(import_btn)
        
        control_layout.addStretch()
        
        # Индикатор статуса
        self.status_label = QLabel("✅ Готово")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        control_layout.addWidget(self.status_label)
        
        layout.addWidget(control_group)
