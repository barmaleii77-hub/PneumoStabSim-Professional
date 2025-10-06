# -*- coding: utf-8 -*-
"""
Geometry configuration panel - РУССКИЙ ИНТЕРФЕЙС
Controls for vehicle geometry parameters with dependency management
Панель конфигурации геометрии с управлением зависимостями
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                              QCheckBox, QPushButton, QLabel, QMessageBox,
                              QSizePolicy, QComboBox)  # NEW: QComboBox for presets
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont

from ..widgets import RangeSlider


class GeometryPanel(QWidget):
    """Панель конфигурации параметров геометрии
    
    Panel for geometry parameter configuration (Russian UI)
    
    Provides controls for / Управление:
    - Wheelbase and track dimensions / База и колея
    - Lever geometry / Геометрия рычагов
    - Cylinder dimensions / Размеры цилиндров
    - Dead zones and clearances / Мёртвые зоны и зазоры
    """
    
    # Signals for parameter changes
    parameter_changed = Signal(str, float)  # parameter_name, new_value
    geometry_updated = Signal(dict)         # Complete geometry dictionary
    geometry_changed = Signal(dict)         # 3D scene geometry update
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Parameter storage
        self.parameters = {}
        
        # Dependency resolution state
        self._resolving_conflict = False
        
        # Setup UI
        self._setup_ui()
        
        # Set default values
        self._set_default_values()
        
        # Connect signals
        self._connect_signals()
        
        # Size policy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        # ✨ ИСПРАВЛЕНО: Отправляем начальные параметры геометрии в QML!
        print("🔧 GeometryPanel: Отправка начальных параметров геометрии...")
        
        # Формируем полную геометрию для QML (как в _get_fast_geometry_update)
        initial_geometry = self._get_fast_geometry_update("init", 0.0)
        self.geometry_changed.emit(initial_geometry)
        self.geometry_updated.emit(self.parameters.copy())
        
        print("  ✅ Начальная геометрия отправлена в QML")
        print(f"  📐 rodPosition = {self.parameters.get('rod_position', 0.6)} (критический параметр!)")
    
    def _setup_ui(self):
        """Настроить интерфейс / Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title (Russian)
        title_label = QLabel("Геометрия автомобиля")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Preset selector (NEW!)
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Пресет:")
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Стандартный грузовик",
            "Лёгкий коммерческий",
            "Тяжёлый грузовик",
            "Пользовательский"
        ])
        self.preset_combo.setCurrentIndex(0)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo, stretch=1)
        layout.addLayout(preset_layout)
        
        # Frame dimensions group
        frame_group = self._create_frame_group()
        layout.addWidget(frame_group)
        
        # Suspension geometry group
        suspension_group = self._create_suspension_group()
        layout.addWidget(suspension_group)
        
        # Cylinder geometry group
        cylinder_group = self._create_cylinder_group()
        layout.addWidget(cylinder_group)
        
        # Options group
        options_group = self._create_options_group()
        layout.addWidget(options_group)
        
        # Control buttons
        buttons_layout = self._create_buttons()
        layout.addLayout(buttons_layout)
        
        layout.addStretch()
    
    def _create_frame_group(self) -> QGroupBox:
        """Создать группу размеров рамы / Create frame dimensions group"""
        group = QGroupBox("Размеры рамы")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Wheelbase (База) - ДИСКРЕТНОСТЬ 0.001м (1мм)
        self.wheelbase_slider = RangeSlider(
            minimum=2.0, maximum=4.0, value=3.2, step=0.001,
            decimals=3, units="м", title="База (колёсная)"
        )
        layout.addWidget(self.wheelbase_slider)
        
        # Track width (Колея) - ДИСКРЕТНОСТЬ 0.001м (1мм)
        self.track_slider = RangeSlider(
            minimum=1.0, maximum=2.5, value=1.6, step=0.001,
            decimals=3, units="м", title="Колея"
        )
        layout.addWidget(self.track_slider)
        
        return group
    
    def _create_suspension_group(self) -> QGroupBox:
        """Создать группу геометрии подвески / Create suspension geometry group"""
        group = QGroupBox("Геометрия подвески")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Distance from frame to lever pivot - ДИСКРЕТНОСТЬ 0.001м (1мм)
        self.frame_to_pivot_slider = RangeSlider(
            minimum=0.3, maximum=1.0, value=0.6, step=0.001,
            decimals=3, units="м", title="Расстояние рама → ось рычага"
        )
        layout.addWidget(self.frame_to_pivot_slider)
        
        # Lever length - ДИСКРЕТНОСТЬ 0.001м (1мм)
        self.lever_length_slider = RangeSlider(
            minimum=0.5, maximum=1.5, value=0.8, step=0.001,
            decimals=3, units="м", title="Длина рычага"
        )
        layout.addWidget(self.lever_length_slider)
        
        # Rod attachment position (доли остаются с меньшим шагом)
        self.rod_position_slider = RangeSlider(
            minimum=0.3, maximum=0.9, value=0.6, step=0.001,
            decimals=3, units="", title="Положение крепления штока (доля)"
        )
        layout.addWidget(self.rod_position_slider)
        
        return group
    
    def _create_cylinder_group(self) -> QGroupBox:
        """Создать группу размеров цилиндра / Create cylinder geometry group"""
        group = QGroupBox("Размеры цилиндра")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Cylinder length - ДИСКРЕТНОСТЬ 0.001м (1мм)
        self.cylinder_length_slider = RangeSlider(
            minimum=0.3, maximum=0.8, value=0.5, step=0.001,
            decimals=3, units="м", title="Длина цилиндра"
        )
        layout.addWidget(self.cylinder_length_slider)
        
        # МШ-1: Единый диаметр цилиндра - УЖЕ 0.001м
        self.cyl_diam_m_slider = RangeSlider(
            minimum=0.030, maximum=0.150, value=0.080, step=0.001,
            decimals=3, units="м", title="Диаметр цилиндра"
        )
        layout.addWidget(self.cyl_diam_m_slider)
        
        # МШ-1: Ход поршня - УЖЕ 0.001м
        self.stroke_m_slider = RangeSlider(
            minimum=0.100, maximum=0.500, value=0.300, step=0.001,
            decimals=3, units="м", title="Ход поршня"
        )
        layout.addWidget(self.stroke_m_slider)
        
        # МШ-1: Мёртвый зазор - УЖЕ 0.001м
        self.dead_gap_m_slider = RangeSlider(
            minimum=0.000, maximum=0.020, value=0.005, step=0.001,
            decimals=3, units="м", title="Мёртвый зазор"
        )
        layout.addWidget(self.dead_gap_m_slider)
        
        # МШ-2: Rod diameter - УЖЕ 0.001м
        self.rod_diameter_m_slider = RangeSlider(
            minimum=0.020, maximum=0.060, value=0.035, step=0.001,
            decimals=3, units="м", title="Диаметр штока"
        )
        layout.addWidget(self.rod_diameter_m_slider)
        
        # МШ-2: Piston rod length - УЖЕ 0.001м
        self.piston_rod_length_m_slider = RangeSlider(
            minimum=0.100, maximum=0.500, value=0.200, step=0.001,
            decimals=3, units="м", title="Длина штока поршня"
        )
        layout.addWidget(self.piston_rod_length_m_slider)
        
        # МШ-2: Piston thickness - УЖЕ 0.001м
        self.piston_thickness_m_slider = RangeSlider(
            minimum=0.010, maximum=0.050, value=0.025, step=0.001,
            decimals=3, units="м", title="Толщина поршня"
        )
        layout.addWidget(self.piston_thickness_m_slider)
        
        return group
    
    def _create_options_group(self) -> QGroupBox:
        """Создать группу опций / Create options group"""
        group = QGroupBox("Опции")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Interference checking (Проверка пересечений)
        self.interference_check = QCheckBox("Проверять пересечения геометрии")
        self.interference_check.setChecked(True)
        layout.addWidget(self.interference_check)
        
        # Link rod diameters (Связать диаметры штоков)
        self.link_rod_diameters = QCheckBox("Связать диаметры штоков передних/задних колёс")
        self.link_rod_diameters.setChecked(False)
        layout.addWidget(self.link_rod_diameters)
        
        return group
    
    def _create_buttons(self) -> QHBoxLayout:
        """Создать кнопки управления / Create control buttons"""
        layout = QHBoxLayout()
        layout.setSpacing(4)
        
        # Reset to defaults (Сбросить к значениям по умолчанию)
        self.reset_button = QPushButton("Сбросить")
        self.reset_button.setToolTip("Сбросить к значениям по умолчанию")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        layout.addWidget(self.reset_button)
        
        # Validate geometry (Проверить геометрию)
        self.validate_button = QPushButton("Проверить")
        self.validate_button.setToolTip("Проверить корректность геометрии")
        self.validate_button.clicked.connect(self._validate_geometry)
        layout.addWidget(self.validate_button)
        
        layout.addStretch()
        
        return layout
    
    @Slot(int)
    def _on_preset_changed(self, index: int):
        """Обработать выбор пресета / Handle preset selection"""
        presets = {
            0: {  # Стандартный грузовик
                'wheelbase': 3.2, 'track': 1.6, 'lever_length': 0.8,
                'cyl_diam_m': 0.080, 'rod_diameter_m': 0.035  # МШ-2: изменено
            },
            1: {  # Лёгкий коммерческий
                'wheelbase': 2.8, 'track': 1.4, 'lever_length': 0.7,
                'cyl_diam_m': 0.065, 'rod_diameter_m': 0.028  # МШ-2: изменено
            },
            2: {  # Тяжёлый грузовик
                'wheelbase': 3.8, 'track': 1.9, 'lever_length': 0.95,
                'cyl_diam_m': 0.100, 'rod_diameter_m': 0.045  # МШ-2: изменено
            },
            3: {}  # Пользовательский (no changes)
        }
        
        if index < 3:  # Don't change for "Пользовательский"
            preset = presets.get(index, {})
            if preset:
                self.set_parameters(preset)
                self.geometry_updated.emit(self.parameters.copy())
    
    def _set_default_values(self):
        """Set default parameter values"""
        defaults = {
            'wheelbase': 3.2,
            'track': 1.6,
            'frame_to_pivot': 0.6,
            'lever_length': 0.8,
            'rod_position': 0.6,
            'cylinder_length': 0.5,
            'cyl_diam_m': 0.080,          # МШ-1: Единый диаметр цилиндра (м)
            'stroke_m': 0.300,            # МШ-1: Ход поршня (м)
            'dead_gap_m': 0.005,          # МШ-1: Мёртвый зазор (м)
            'rod_diameter_m': 0.035,      # МШ-2: Диаметр штока (м)
            'piston_rod_length_m': 0.200, # МШ-2: Длина штока поршня (м)
            'piston_thickness_m': 0.025   # МШ-2: Толщина поршня (м)
        }
        
        self.parameters.update(defaults)
    
    def _connect_signals(self):
        """Connect widget signals"""
        # Frame dimensions - МГНОВЕННОЕ ОБНОВЛЕНИЕ во время движения
        self.wheelbase_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed('wheelbase', v))
        self.track_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed('track', v))
        
        # Suspension geometry - МГНОВЕННОЕ ОБНОВЛЕНИЕ во время движения
        self.frame_to_pivot_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed('frame_to_pivot', v))
        self.lever_length_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed('lever_length', v))
        self.rod_position_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed('rod_position', v))
        
        # Cylinder dimensions - МГНОВЕННОЕ ОБНОВЛЕНИЕ во время движения
        self.cylinder_length_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed('cylinder_length', v))
        # МШ-1: Подключение новых слайдеров - МГНОВЕННОЕ ОБНОВЛЕНИЕ
        self.cyl_diam_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed('cyl_diam_m', v))
        self.stroke_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed('stroke_m', v))
        self.dead_gap_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed('dead_gap_m', v))
        # МШ-2: Подключение слайдеров в метрах - МГНОВЕННОЕ ОБНОВЛЕНИЕ
        self.rod_diameter_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed('rod_diameter_m', v))
        self.piston_rod_length_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed('piston_rod_length_m', v))
        self.piston_thickness_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_changed('piston_thickness_m', v))
        
        # Options
        self.link_rod_diameters.toggled.connect(self._on_link_rod_diameters_toggled)
        
        print("🔧 GeometryPanel: Сигналы подключены для МГНОВЕННОГО обновления (valueChanged)")
    
    @Slot(bool)
    def _on_link_rod_diameters_toggled(self, checked: bool):
        """Handle link rod diameters checkbox toggle
        
        Args:
            checked: True if checkbox is checked
        """
        print(f"🔗 GeometryPanel: Link rod diameters {'enabled' if checked else 'disabled'}")
        # Store the setting
        self.parameters['link_rod_diameters'] = checked
        
        # If enabled, synchronize rod diameters
        if checked:
            # Use current rod_diameter as the common value
            common_diameter = self.parameters.get('rod_diameter', 35.0)
            print(f"   Synchronizing all rod diameters to {common_diameter}mm")
            
        # Emit update
        self.geometry_updated.emit(self.parameters.copy())
    
    def _set_parameter_value(self, param_name: str, value: float):
        """Set value for a specific parameter widget
        
        Args:
            param_name: Name of parameter
            value: New value to set
        """
        widget_map = {
            'wheelbase': self.wheelbase_slider,
            'track': self.track_slider,
            'frame_to_pivot': self.frame_to_pivot_slider,
            'lever_length': self.lever_length_slider,
            'rod_position': self.rod_position_slider,
            'cylinder_length': self.cylinder_length_slider,
            'cyl_diam_m': self.cyl_diam_m_slider,                # МШ-1
            'stroke_m': self.stroke_m_slider,                    # МШ-1
            'dead_gap_m': self.dead_gap_m_slider,                # МШ-1
            'rod_diameter_m': self.rod_diameter_m_slider,        # МШ-2
            'piston_rod_length_m': self.piston_rod_length_m_slider,  # МШ-2
            'piston_thickness_m': self.piston_thickness_m_slider     # МШ-2
        }
        
        widget = widget_map.get(param_name)
        if widget:
            widget.setValue(value)
    
    @Slot(str, float)
    def _on_parameter_changed(self, param_name: str, value: float):
        """Handle parameter change with dependency resolution
        
        Args:
            param_name: Name of changed parameter
            value: New value
        """
        print(f"🔧 GeometryPanel._on_parameter_changed: {param_name} = {value}")
        
        if self._resolving_conflict:
            print(f"   ⏸️ Пропуск - идет разрешение конфликта")
            return
        
        # Store new value
        old_value = self.parameters.get(param_name, 0.0)
        self.parameters[param_name] = value
        print(f"   💾 Параметр сохранен: {param_name} {old_value} → {value}")
        
        # БЫСТРАЯ ПРОВЕРКА конфликтов только для критических параметров
        critical_conflicts = self._check_critical_dependencies(param_name, value, old_value)
        
        if critical_conflicts:
            print(f"   ⚠️ Обнаружен критический конфликт: {critical_conflicts.get('type', 'неизвестный')}")
            # Показываем конфликты только для критических проблем
            self._resolve_conflict(critical_conflicts)
        else:
            print(f"   ✅ Конфликтов нет, отправляем сигналы...")
            # МГНОВЕННОЕ обновление без задержек
            self.parameter_changed.emit(param_name, value)
            print(f"   📡 parameter_changed отправлен")
            
            self.geometry_updated.emit(self.parameters.copy())
            print(f"   📡 geometry_updated отправлен")
            
            # БЫСТРОЕ обновление 3D сцены для видимых параметров
            if param_name in ['wheelbase', 'track', 'lever_length', 'cylinder_length', 'frame_to_pivot', 'rod_position', 
                             'cyl_diam_m', 'stroke_m', 'dead_gap_m', 'rod_diameter_m', 'piston_rod_length_m', 'piston_thickness_m']:
                print(f"   🎬 Параметр {param_name} требует обновления 3D сцены")
                # Конвертируем только измененный параметр для быстроты
                geometry_3d = self._get_fast_geometry_update(param_name, value)
                self.geometry_changed.emit(geometry_3d)
                print(f"   📡 geometry_changed отправлен с rodPosition = {geometry_3d.get('rodPosition', 'НЕ НАЙДЕН')}")
            else:
                print(f"   ⏭️ Параметр {param_name} не требует обновления 3D сцены")
    
    @Slot()
    def _reset_to_defaults(self):
        """Сбросить все параметры к значениям по умолчанию / Reset all parameters to defaults"""
        print("🔄 GeometryPanel: Сброс к значениям по умолчанию")
        self._set_default_values()
        
        # Update all widgets
        self.wheelbase_slider.setValue(self.parameters['wheelbase'])
        self.track_slider.setValue(self.parameters['track'])
        self.frame_to_pivot_slider.setValue(self.parameters['frame_to_pivot'])
        self.lever_length_slider.setValue(self.parameters['lever_length'])
        self.rod_position_slider.setValue(self.parameters['rod_position'])
        self.cylinder_length_slider.setValue(self.parameters['cylinder_length'])
        # МШ-1: Параметры цилиндра
        self.cyl_diam_m_slider.setValue(self.parameters['cyl_diam_m'])
        self.stroke_m_slider.setValue(self.parameters['stroke_m'])
        self.dead_gap_m_slider.setValue(self.parameters['dead_gap_m'])
        # МШ-2: Параметры штока и поршня в метрах
        self.rod_diameter_m_slider.setValue(self.parameters['rod_diameter_m'])
        self.piston_rod_length_m_slider.setValue(self.parameters['piston_rod_length_m'])
        self.piston_thickness_m_slider.setValue(self.parameters['piston_thickness_m'])
        
        # Reset checkboxes
        self.interference_check.setChecked(True)
        self.link_rod_diameters.setChecked(False)
        
        # Reset preset combo to "Стандартный грузовик"
        self.preset_combo.setCurrentIndex(0)
        
        # Emit update
        self.geometry_updated.emit(self.parameters.copy())
        print("✅ Параметры сброшены")
    
    @Slot()
    def _validate_geometry(self):
        """Проверить текущие настройки геометрии / Validate current geometry settings"""
        errors = []
        warnings = []
        
        # Check geometric constraints
        wheelbase = self.parameters['wheelbase']
        lever_length = self.parameters['lever_length']
        frame_to_pivot = self.parameters['frame_to_pivot']
        
        max_lever_reach = wheelbase / 2.0 - 0.1
        if frame_to_pivot + lever_length > max_lever_reach:
            errors.append(f"Геометрия рычага превышает доступное пространство: {frame_to_pivot + lever_length:.2f} > {max_lever_reach:.2f}м")
        
        # МШ-2: Обновлённая проверка гидравлических ограничений (оба параметра в метрах)
        rod_diameter_m = self.parameters.get('rod_diameter_m', 0.035)  # м
        cyl_diam_m = self.parameters.get('cyl_diam_m', 0.080)          # м
        
        if rod_diameter_m >= cyl_diam_m * 0.8:
            errors.append(f"Диаметр штока слишком велик: {rod_diameter_m*1000:.1f}мм >= 80% от {cyl_diam_m*1000:.1f}мм цилиндра")
        elif rod_diameter_m >= cyl_diam_m * 0.7:
            warnings.append(f"Диаметр штока близок к пределу: {rod_diameter_m*1000:.1f}мм vs {cyl_diam_m*1000:.1f}мм цилиндра")
        
        # Show results
        if errors:
            QMessageBox.critical(self, 'Ошибки геометрии', 
                               'Обнаружены ошибки:\n' + '\n'.join(errors))
        elif warnings:
            QMessageBox.warning(self, 'Предупреждения геометрии',
                              'Предупреждения:\n' + '\n'.join(warnings))
        else:
            QMessageBox.information(self, 'Проверка геометрии', 
                                  'Все параметры геометрии корректны.')
    
    def get_parameters(self) -> dict:
        """Get current parameter values
        
        Returns:
            Dictionary of current parameters
        """
        return self.parameters.copy()
    
    def set_parameters(self, params: dict):
        """Set parameter values from dictionary
        
        Args:
            params: Dictionary of parameter values
        """
        self._resolving_conflict = True
        
        try:
            # Update internal storage
            self.parameters.update(params)
            
            # Update widgets
            for param_name, value in params.items():
                self._set_parameter_value(param_name, value)
        
        finally:
            self._resolving_conflict = False
    
    def _get_fast_geometry_update(self, param_name: str, value: float) -> dict:
        """Получить быстрое обновление геометрии только для изменённого параметра
        
        Args:
            param_name: Имя параметра
            value: Новое значение
            
        Returns:
            Словарь с обновленной геометрией
        """
        # ПОЛНАЯ геометрия с ВСЕМИ параметрами для 3D сцены
        geometry_3d = {
            # ОСНОВНЫЕ РАЗМЕРЫ РАМЫ (из метров в мм)
            'frameLength': self.parameters.get('wheelbase', 3.2) * 1000,  # м -> мм
            'frameHeight': 650.0,  # Фиксированное значение пока (TODO: добавить параметр)
            'frameBeamSize': 120.0,  # Фиксированное значение пока (TODO: добавить параметр)
            'leverLength': self.parameters.get('lever_length', 0.8) * 1000,  # м -> мм
            'cylinderBodyLength': self.parameters.get('cylinder_length', 0.5) * 1000,  # м -> мм
            'tailRodLength': 100.0,  # Фиксированное значение пока (TODO: добавить параметр)
            
            # ДОПОЛНИТЕЛЬНЫЕ ПАРАМЕТРЫ ГЕОМЕТРИИ (из метров в мм)
            'trackWidth': self.parameters.get('track', 1.6) * 1000,  # м -> мм
            'frameToPivot': self.parameters.get('frame_to_pivot', 0.6) * 1000,  # м -> мм
            'rodPosition': self.parameters.get('rod_position', 0.6),  # доля 0-1 (без изменений)
            
            # СОВМЕСТИМОСТЬ: Старые параметры цилиндра (устаревшие, но поддерживаем)
            'boreHead': self.parameters.get('cyl_diam_m', 0.080) * 1000,  # NEW: используем новый параметр
            'boreRod': self.parameters.get('cyl_diam_m', 0.080) * 1000,   # NEW: используем новый параметр
            'rodDiameter': self.parameters.get('rod_diameter_m', 0.035) * 1000,  # NEW: используем новый параметр
            'pistonThickness': self.parameters.get('piston_thickness_m', 0.025) * 1000,  # NEW: используем новый параметр
            'pistonRodLength': self.parameters.get('piston_rod_length_m', 0.200) * 1000,  # NEW: используем новый параметр
            
            # ✨ НОВЫЕ ПАРАМЕТРЫ (МШ-1 и МШ-2): Все в мм для QML
            'cylDiamM': self.parameters.get('cyl_diam_m', 0.080) * 1000,        # м -> мм: диаметр цилиндра
            'strokeM': self.parameters.get('stroke_m', 0.300) * 1000,            # м -> мм: ход поршня
            'deadGapM': self.parameters.get('dead_gap_m', 0.005) * 1000,         # м -> мм: мертвый зазор
            'rodDiameterM': self.parameters.get('rod_diameter_m', 0.035) * 1000, # м -> мм: диаметр штока
            'pistonRodLengthM': self.parameters.get('piston_rod_length_m', 0.200) * 1000,  # м -> мм: длина штока
            'pistonThicknessM': self.parameters.get('piston_thickness_m', 0.025) * 1000,   # м -> мм: толщина поршня
        }
        
        print(f"🔄 GeometryPanel: Отправка ПОЛНОЙ геометрии в QML (изменён параметр: {param_name} = {value})")
        print(f"   📐 Основные: frameLength={geometry_3d['frameLength']:.1f}мм, leverLength={geometry_3d['leverLength']:.1f}мм")
        print(f"   📐 Цилиндр: cylDiam={geometry_3d['cylDiamM']:.1f}мм, stroke={geometry_3d['strokeM']:.1f}мм")
        print(f"   📐 Шток: diameter={geometry_3d['rodDiameterM']:.1f}мм, length={geometry_3d['pistonRodLengthM']:.1f}мм")
        print(f"   🎯 rodPosition = {geometry_3d['rodPosition']} (КРИТИЧЕСКИЙ параметр)")
        
        return geometry_3d

    def _check_critical_dependencies(self, param_name: str, new_value: float, old_value: float) -> dict:
        """Быстрая проверка только критических зависимостей
        
        Args:
            param_name: Имя изменённого параметра
            new_value: Новое значение
            old_value: Предыдущее значение
            
        Returns:
            Словарь с информацией о конфликте или None
        """
        # Проверяем только самые критические конфликты для быстроты
        
        # МШ-2: Критический конфликт - диаметр штока vs цилиндра
        if param_name in ['rod_diameter_m', 'cyl_diam_m']:
            rod_diameter_m = self.parameters.get('rod_diameter_m', 0.035)  # м
            cyl_diam_m = self.parameters.get('cyl_diam_m', 0.080)          # м
            
            if rod_diameter_m >= cyl_diam_m * 0.8:  # Критический предел
                return {
                    'type': 'hydraulic_constraint',
                    'message': f'Диаметр штока слишком велик относительно цилиндра.\n'
                              f'Шток: {rod_diameter_m*1000:.1f}мм\n'
                              f'Цилиндр: {cyl_diam_m*1000:.1f}мм',
                    'options': [
                        ('Уменьшить диаметр штока', 'rod_diameter_m', cyl_diam_m * 0.7),
                        ('Увеличить диаметр цилиндра', 'cyl_diam_m', rod_diameter_m / 0.7),
                    ],
                    'changed_param': param_name
                }
        
        # Остальные конфликты пропускаем для скорости
        return None

    def _resolve_conflict(self, conflict_info: dict):
        """Показать диалог разрешения конфликта / Show conflict resolution dialog
        
        Args:
            conflict_info: Информация о конфликте / Conflict information dictionary
        """
        self._resolving_conflict = True
        
        try:
            # Create message box with options
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('Конфликт параметров')
            msg_box.setText(conflict_info['message'])
            msg_box.setInformativeText('Как вы хотите разрешить этот конфликт?')
            
            # Add buttons for each resolution option
            buttons = []
            for option_text, param_name, suggested_value in conflict_info['options']:
                button = msg_box.addButton(option_text, QMessageBox.ButtonRole.ActionRole)
                buttons.append((button, param_name, suggested_value))
            
            # Add cancel button
            cancel_button = msg_box.addButton('Отмена', QMessageBox.ButtonRole.RejectRole)
            
            # Show dialog
            msg_box.exec()
            clicked_button = msg_box.clickedButton()
            
            if clicked_button == cancel_button:
                # Revert to old value
                changed_param = conflict_info['changed_param']
                old_value = self._get_widget_for_parameter(changed_param)
                self._set_parameter_value(changed_param, old_value)
            else:
                # Apply selected resolution
                for button, param_name, suggested_value in buttons:
                    if clicked_button == button:
                        self._set_parameter_value(param_name, suggested_value)
                        self.parameters[param_name] = suggested_value
                        break
                
                # Emit update signals
                self.geometry_updated.emit(self.parameters.copy())
        
        finally:
            self._resolving_conflict = False
