"""
GraphicsPanel - панель настроек графики и визуализации
Graphics Panel - comprehensive graphics and visualization settings panel
РУССКИЙ ИНТЕРФЕЙС (Russian UI)
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
    Панель настроек графики и визуализации
    Comprehensive graphics and visualization settings panel
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
        
        # Текущие параметры графики (расширенные)
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
            
            # Окружение
            'background_color': '#2a2a2a',
            'fog_enabled': False,
            'fog_color': '#808080',
            'fog_density': 0.1,
            'skybox_enabled': False,
            'skybox_blur': 0.0,
            
            # Качество рендеринга
            'antialiasing': 2,          # 0=None, 1=SSAA, 2=MSAA
            'aa_quality': 2,            # 0=Low, 1=Medium, 2=High
            'shadows_enabled': True,
            'shadow_quality': 1,        # 0=Low, 1=Medium, 2=High
            'shadow_softness': 0.5,
            
            # Материалы
            'metal_roughness': 0.28,
            'metal_metalness': 1.0,
            'metal_clearcoat': 0.25,
            'glass_opacity': 0.35,
            'glass_roughness': 0.05,
            'frame_metalness': 0.8,
            'frame_roughness': 0.4,
            
            # Камера
            'camera_fov': 45.0,
            'camera_near': 10.0,
            'camera_far': 50000.0,
            'camera_speed': 1.0,
            'auto_rotate': False,
            'auto_rotate_speed': 0.5,
            
            # Эффекты
            'bloom_enabled': False,
            'bloom_intensity': 0.3,
            'ssao_enabled': False,
            'ssao_intensity': 0.5,
            'motion_blur': False,
            'depth_of_field': False,
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
        
        self.logger.info("GraphicsPanel инициализирована (расширенная версия)")
    
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
        
        # Стеклянные части
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
        
        # Туман
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
        
        # Качество рендеринга
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
        
        layout.addWidget(quality_group)
        
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
        
        # Настройки камеры
        cam_group = QGroupBox("📷 Настройки камеры")
        cam_layout = QGridLayout(cam_group)
        
        # Поле зрения (FOV)
        cam_layout.addWidget(QLabel("Поле зрения:"), 0, 0)
        self.camera_fov = QDoubleSpinBox()
        self.camera_fov.setRange(10.0, 120.0)
        self.camera_fov.setSingleStep(5.0)
        self.camera_fov.setSuffix("°")
        self.camera_fov.setValue(self.current_graphics['camera_fov'])
        self.camera_fov.valueChanged.connect(self.on_camera_fov_changed)
        cam_layout.addWidget(self.camera_fov, 0, 1)
        
        # Скорость движения
        cam_layout.addWidget(QLabel("Скорость:"), 0, 2)
        self.camera_speed = QDoubleSpinBox()
        self.camera_speed.setRange(0.1, 5.0)
        self.camera_speed.setSingleStep(0.1)
        self.camera_speed.setDecimals(1)
        self.camera_speed.setValue(self.current_graphics['camera_speed'])
        self.camera_speed.valueChanged.connect(self.on_camera_speed_changed)
        cam_layout.addWidget(self.camera_speed, 0, 3)
        
        # Ближняя плоскость отсечения
        cam_layout.addWidget(QLabel("Ближняя граница:"), 1, 0)
        self.camera_near = QDoubleSpinBox()
        self.camera_near.setRange(1.0, 100.0)
        self.camera_near.setSingleStep(1.0)
        self.camera_near.setSuffix("мм")
        self.camera_near.setValue(self.current_graphics['camera_near'])
        self.camera_near.valueChanged.connect(self.on_camera_near_changed)
        cam_layout.addWidget(self.camera_near, 1, 1)
        
        # Дальшая плоскость отсечения
        cam_layout.addWidget(QLabel("Дальняя граница:"), 1, 2)
        self.camera_far = QSpinBox()
        self.camera_far.setRange(1000, 100000)
        self.camera_far.setSingleStep(1000)
        self.camera_far.setSuffix("мм")
        self.camera_far.setValue(int(self.current_graphics['camera_far']))
        self.camera_far.valueChanged.connect(self.on_camera_far_changed)
        cam_layout.addWidget(self.camera_far, 1, 3)
        
        layout.addWidget(cam_group)
        
        # Автоматическое вращение
        auto_group = QGroupBox("🔄 Автоматическое вращение")
        auto_layout = QGridLayout(auto_group)
        
        # Включение авто-вращения
        self.auto_rotate = QCheckBox("Включить автоматическое вращение")
        self.auto_rotate.setChecked(self.current_graphics['auto_rotate'])
        self.auto_rotate.toggled.connect(self.on_auto_rotate_toggled)
        auto_layout.addWidget(self.auto_rotate, 0, 0, 1, 3)
        
        # Скорость вращения
        auto_layout.addWidget(QLabel("Скорость вращения:"), 1, 0)
        self.auto_rotate_speed = QDoubleSpinBox()
        self.auto_rotate_speed.setRange(0.1, 3.0)
        self.auto_rotate_speed.setSingleStep(0.1)
        self.auto_rotate_speed.setDecimals(1)
        self.auto_rotate_speed.setValue(self.current_graphics['auto_rotate_speed'])
        self.auto_rotate_speed.valueChanged.connect(self.on_auto_rotate_speed_changed)  # ИСПРАВЛЕНО: Подключаем сигнал!
        auto_layout.addWidget(self.auto_rotate_speed, 1, 1)
        
        layout.addWidget(auto_group)
        
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def create_effects_tab(self):
        """Создать вкладку визуальных эффектов"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Пост-эффекты
        post_group = QGroupBox("✨ Пост-эффекты")
        post_layout = QGridLayout(post_group)
        
        # Bloom (свечение)
        self.bloom_enabled = QCheckBox("Bloom (свечение)")
        self.bloom_enabled.setChecked(self.current_graphics['bloom_enabled'])
        self.bloom_enabled.toggled.connect(self.on_bloom_toggled)
        post_layout.addWidget(self.bloom_enabled, 0, 0, 1, 2)
        
        # Интенсивность bloom
        post_layout.addWidget(QLabel("Интенсивность bloom:"), 0, 2)
        self.bloom_intensity = QDoubleSpinBox()
        self.bloom_intensity.setRange(0.0, 2.0)
        self.bloom_intensity.setSingleStep(0.1)
        self.bloom_intensity.setDecimals(1)
        self.bloom_intensity.setValue(self.current_graphics['bloom_intensity'])
        self.bloom_intensity.valueChanged.connect(self.on_bloom_intensity_changed)
        post_layout.addWidget(self.bloom_intensity, 0, 3)
        
        # SSAO (Screen Space Ambient Occlusion)
        self.ssao_enabled = QCheckBox("SSAO (затенение)")
        self.ssao_enabled.setChecked(self.current_graphics['ssao_enabled'])
        self.ssao_enabled.toggled.connect(self.on_ssao_toggled)
        post_layout.addWidget(self.ssao_enabled, 1, 0, 1, 2)
        
        # Интенсивность SSAO
        post_layout.addWidget(QLabel("Интенсивность SSAO:"), 1, 2)
        self.ssao_intensity = QDoubleSpinBox()
        self.ssao_intensity.setRange(0.0, 2.0)
        self.ssao_intensity.setSingleStep(0.1)
        self.ssao_intensity.setDecimals(1)
        self.ssao_intensity.setValue(self.current_graphics['ssao_intensity'])
        self.ssao_intensity.valueChanged.connect(self.on_ssao_intensity_changed)
        post_layout.addWidget(self.ssao_intensity, 1, 3)
        
        # Motion Blur
        self.motion_blur = QCheckBox("Motion Blur (размытие движения)")
        self.motion_blur.setChecked(self.current_graphics['motion_blur'])
        self.motion_blur.toggled.connect(self.on_motion_blur_toggled)
        post_layout.addWidget(self.motion_blur, 2, 0, 1, 4)
        
        # Depth of Field
        self.depth_of_field = QCheckBox("Depth of Field (глубина резкости)")
        self.depth_of_field.setChecked(self.current_graphics['depth_of_field'])
        self.depth_of_field.toggled.connect(self.on_depth_of_field_toggled)
        post_layout.addWidget(self.depth_of_field, 3, 0, 1, 4)
        
        layout.addWidget(post_group)
        
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def create_control_buttons(self, parent_layout):
        """Создать кнопки управления внизу панели"""
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        # Сохранить настройки
        save_btn = QPushButton("💾 Сохранить")
        save_btn.clicked.connect(self.save_settings)
        control_layout.addWidget(save_btn)
        
        # Сброс к умолчанию
        reset_btn = QPushButton("🔄 Сброс")
        reset_btn.clicked.connect(self.reset_to_defaults)
        control_layout.addWidget(reset_btn)
        
        # Экспорт настроек
        export_btn = QPushButton("📤 Экспорт")
        export_btn.clicked.connect(self.export_graphics_settings)
        control_layout.addWidget(export_btn)
        
        # Импорт настроек
        import_btn = QPushButton("📥 Импорт")
        import_btn.clicked.connect(self.import_graphics_settings)
        control_layout.addWidget(import_btn)
        
        parent_layout.addWidget(control_frame)
    
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
        """Отправить сигнал об изменении материалов"""
        material_params = {
            'metal': {
                'roughness': self.current_graphics['metal_roughness'],
                'metalness': self.current_graphics['metal_metalness'],
                'clearcoat': self.current_graphics['metal_clearcoat']
            },
            'glass': {
                'opacity': self.current_graphics['glass_opacity'],
                'roughness': self.current_graphics['glass_roughness']
            },
            'frame': {
                'metalness': self.current_graphics['frame_metalness'],
                'roughness': self.current_graphics['frame_roughness']
            }
        }
        
        self.logger.info(f"Materials updated: {material_params}")
        self.material_changed.emit(material_params)
    
    def emit_environment_update(self):
        """Отправить сигнал об изменении окружения"""
        env_params = {
            'background_color': self.current_graphics['background_color'],
            'fog_enabled': self.current_graphics['fog_enabled'],
            'fog_color': self.current_graphics['fog_color'],
            'fog_density': self.current_graphics['fog_density'],
            'skybox_enabled': self.current_graphics['skybox_enabled']
        }
        
        self.logger.info(f"Environment updated: {env_params}")
        self.environment_changed.emit(env_params)
    
    def emit_quality_update(self):
        """Отправить сигнал об изменении качества"""
        quality_params = {
            'antialiasing': self.current_graphics['antialiasing'],
            'aa_quality': self.current_graphics['aa_quality'],
            'shadows_enabled': self.current_graphics['shadows_enabled'],
            'shadow_quality': self.current_graphics['shadow_quality']
        }
        
        self.logger.info(f"Quality updated: {quality_params}")
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
        """Отправить сигнал об изменении эффектов"""
        effects_params = {
            'bloom_enabled': self.current_graphics['bloom_enabled'],
            'bloom_intensity': self.current_graphics['bloom_intensity'],
            'ssao_enabled': self.current_graphics['ssao_enabled'],
            'ssao_intensity': self.current_graphics['ssao_intensity'],
            'motion_blur': self.current_graphics['motion_blur'],
            'depth_of_field': self.current_graphics['depth_of_field']
        }
        
        self.logger.info(f"Effects updated: {effects_params}")
        self.effects_changed.emit(effects_params)
    
    # =================================================================
    # Пресеты и управление настройками (Presets & Settings Management)
    # =================================================================
    
    @Slot(str)
    def apply_preset(self, preset_name: str):
        """Применить пресет освещения"""
        self.logger.info(f"Applying lighting preset: {preset_name}")
        
        if preset_name == 'day':
            # Дневное освещение
            self.current_graphics.update({
                'key_brightness': 3.2,
                'key_color': '#fff8e1',
                'key_angle_x': -25,
                'key_angle_y': -30,
                'fill_brightness': 1.8,
                'fill_color': '#f0f0ff',
                'point_brightness': 15000,
                'background_color': '#87ceeb',
                'fog_enabled': False,
                'skybox_enabled': True
            })
            
        elif preset_name == 'night':
            # Ночное освещение
            self.current_graphics.update({
                'key_brightness': 1.8,
                'key_color': '#b3c6ff',
                'key_angle_x': -60,
                'key_angle_y': 45,
                'fill_brightness': 0.8,
                'fill_color': '#ccccff',
                'point_brightness': 8000,
                'background_color': '#0f0f23',
                'fog_enabled': True,
                'fog_density': 0.2
            })
            
        elif preset_name == 'industrial':
            # Промышленное освещение
            self.current_graphics.update({
                'key_brightness': 4.0,
                'key_color': '#f0f0f0',
                'key_angle_x': -20,
                'key_angle_y': 0,
                'fill_brightness': 2.5,
                'fill_color': '#ffffff',
                'point_brightness': 25000,
                'background_color': '#404040',
                'fog_enabled': False,
                'skybox_enabled': False
            })
        
        # Обновить UI элементы
        self.update_ui_from_current_settings()
        
        # Отправить сигналы об изменениях
        self.emit_lighting_update()
        self.emit_environment_update()
        
        self.preset_applied.emit(preset_name)
    
    def update_ui_from_current_settings(self):
        """Обновить UI элементы из текущих настроек"""
        # Блокируем сигналы во время обновления
        widgets = [
            # Освещение
            self.key_brightness, self.key_color, self.key_angle_x, self.key_angle_y,
            self.fill_brightness, self.fill_color, self.point_brightness, self.point_y,
            # Материалы
            self.metal_roughness, self.metal_metalness, self.metal_clearcoat,
            self.glass_opacity, self.glass_roughness,
            self.frame_metalness, self.frame_roughness,
            # Окружение
            self.background_color, self.fog_color, self.fog_density,
            # Камера
            self.camera_fov, self.camera_speed, self.camera_near, self.camera_far,
            self.auto_rotate_speed,
            # Эффекты
            self.bloom_intensity, self.ssao_intensity
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
            self.frame_metalness.setValue(self.current_graphics['frame_metalness'])
            self.frame_roughness.setValue(self.current_graphics['frame_roughness'])
            
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
            self.ssao_enabled.setChecked(self.current_graphics['ssao_enabled'])
            self.ssao_intensity.setValue(self.current_graphics['ssao_intensity'])
            self.motion_blur.setChecked(self.current_graphics['motion_blur'])
            self.depth_of_field.setChecked(self.current_graphics['depth_of_field'])
            
        finally:
            # Разблокируем сигналы
            for widget in widgets:
                if hasattr(widget, 'blockSignals'):
                    widget.blockSignals(False)
    
    @Slot()
    def reset_to_defaults(self):
        """Сбросить настройки к значениям по умолчанию"""
        self.logger.info("Resetting graphics to defaults")
        
        # Сбросить к начальным значениям (расширенный список)
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
            
            # Окружение
            'background_color': '#2a2a2a',
            'fog_enabled': False,
            'fog_color': '#808080',
            'fog_density': 0.1,
            'skybox_enabled': False,
            'skybox_blur': 0.0,
            
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
            'frame_metalness': 0.8,
            'frame_roughness': 0.4,
            
            # Камера
            'camera_fov': 45.0,
            'camera_near': 10.0,
            'camera_far': 50000.0,
            'camera_speed': 1.0,
            'auto_rotate': False,
            'auto_rotate_speed': 0.5,
            
            # Эффекты
            'bloom_enabled': False,
            'bloom_intensity': 0.3,
            'ssao_enabled': False,
            'ssao_intensity': 0.5,
            'motion_blur': False,
            'depth_of_field': False,
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
        """Загрузить настройки из QSettings"""
        self.logger.info("Loading graphics settings")
        
        for key in self.current_graphics.keys():
            saved_value = self.settings.value(f"graphics/{key}")
            if saved_value is not None:
                # Конвертируем типы
                if key in ['key_brightness', 'fill_brightness', 'rim_brightness', 'point_fade',
                          'fog_density', 'metal_roughness', 'metal_metalness', 'metal_clearcoat',
                          'glass_opacity', 'glass_roughness', 'frame_metalness', 'frame_roughness',
                          'camera_fov', 'camera_near', 'camera_speed', 'auto_rotate_speed',
                          'bloom_intensity', 'ssao_intensity']:
                    self.current_graphics[key] = float(saved_value)
                elif key in ['key_angle_x', 'key_angle_y', 'point_brightness', 'point_y',
                            'antialiasing', 'aa_quality', 'shadow_quality', 'camera_far']:
                    self.current_graphics[key] = int(saved_value)
                elif key in ['fog_enabled', 'skybox_enabled', 'shadows_enabled', 'auto_rotate',
                            'bloom_enabled', 'ssao_enabled', 'motion_blur', 'depth_of_field']:
                    self.current_graphics[key] = bool(saved_value == 'true' or saved_value == True)
                else:
                    self.current_graphics[key] = str(saved_value)
        
        # Обновить UI после загрузки
        if hasattr(self, 'key_brightness'):  # UI уже создан
            self.update_ui_from_current_settings()
    
    @Slot()
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
