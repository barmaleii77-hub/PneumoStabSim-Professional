# -*- coding: utf-8 -*-
"""
Range slider widget with editable min/max bounds
Combines QSlider with QDoubleSpinBox controls for precise range control
ОБНОВЛЕНО: Более мелкие деления шкалы, ширина диапазона без скобок
"""

import math
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                              QSlider, QDoubleSpinBox, QSizePolicy)
from PySide6.QtCore import Signal, Slot, QTimer, Qt
from PySide6.QtGui import QFont, QPalette, QColor


class RangeSlider(QWidget):
    """Slider with editable min/max range and precise value control
    
    ОБНОВЛЕНО:
    - Более мелкие деления шкалы для лучшей точности
    - Отображение "ширина диапазона" полным текстом без скобок
    - Поля МИН, ЗНАЧЕНИЕ, МАКС на одном горизонтальном уровне
    - Шкала слайдера на всю ширину окна (отдельная строка)
    - Индикаторы диапазона и позиции
    - Цветовое кодирование и tooltip'ы
    """
    
    # СИГНАЛЫ:
    # valueChanged - МГНОВЕННОЕ обновление во время движения ползунка (для геометрии)
    # valueEdited - ФИНАЛЬНОЕ обновление после завершения редактирования (с задержкой debounce)
    valueEdited = Signal(float)    # Финальное значение после debounce
    valueChanged = Signal(float)   # Мгновенное значение во время движения
    rangeChanged = Signal(float, float)
    
    def __init__(self, minimum=0.0, maximum=100.0, value=50.0, step=1.0, decimals=2, units="", title="", parent=None):
        super().__init__(parent)
        self._step = step
        self._decimals = decimals
        self._units = units
        
        # УВЕЛИЧЕННОЕ разрешение слайдера для точности 0.001м
        # Для диапазона 4м с шагом 0.001м нужно 4000 позиций
        # Используем 100000 для запаса и плавности
        self._slider_resolution = 100000  # Было 10000, теперь 100000
        self._updating_internally = False
        
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_value_edited)
        self._debounce_delay = 200
        
        self._setup_ui(title)
        self.setRange(minimum, maximum)
        self.setValue(value)
        self._connect_signals()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    def _setup_ui(self, title):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)
        
        if title:
            self.title_label = QLabel(title)
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            font = QFont()
            font.setPointSize(9)
            font.setBold(True)
            self.title_label.setFont(font)
            layout.addWidget(self.title_label)
        
        # ✨ ОБНОВЛЕНО: Индикатор диапазона с шириной диапазона без скобок
        self.range_indicator_label = QLabel("Диапазон: 0.0 — 100.0 ширина диапазона 100.0")
        self.range_indicator_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(7)
        font.setItalic(True)
        self.range_indicator_label.setFont(font)
        # Серый цвет для индикатора
        palette = self.range_indicator_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor(128, 128, 128))
        self.range_indicator_label.setPalette(palette)
        layout.addWidget(self.range_indicator_label)
        
        # 🎯 ОБНОВЛЕНО: ШКАЛА СЛАЙДЕРА с более мелкими делениями
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self._slider_resolution)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        # УМЕНЬШЕНО: Более мелкие деления - было //10, стало //20 (в 2 раза больше делений)
        self.slider.setTickInterval(self._slider_resolution // 20)
        # Задаем минимальную ширину для полного использования пространства
        self.slider.setMinimumWidth(300)
        layout.addWidget(self.slider)
        
        # ✨ Индикатор позиции
        self.position_indicator_label = QLabel("Позиция: 50.0% от диапазона")
        self.position_indicator_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(7)
        self.position_indicator_label.setFont(font)
        layout.addWidget(self.position_indicator_label)
        
        # 🎯 ПОЛЯ ВВОДА - все на одном горизонтальном уровне
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        # Min controls
        min_layout = QVBoxLayout()
        min_layout.setSpacing(1)
        min_label = QLabel("Мин")
        min_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(7)
        min_label.setFont(font)
        min_layout.addWidget(min_label)
        
        self.min_spinbox = QDoubleSpinBox()
        self.min_spinbox.setDecimals(self._decimals)
        self.min_spinbox.setRange(-1e6, 1e6)
        self.min_spinbox.setMinimumWidth(80)
        self.min_spinbox.setMaximumWidth(100)
        self.min_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # ✨ Tooltip для min
        self.min_spinbox.setToolTip("Минимальное значение диапазона")
        min_layout.addWidget(self.min_spinbox)
        controls_layout.addLayout(min_layout)
        
        # Растягивающееся пространство между мин и значением
        controls_layout.addStretch()
        
        # Value controls (ПО ЦЕНТРУ между мин и макс)
        value_layout = QVBoxLayout()
        value_layout.setSpacing(1)
        value_label = QLabel("Значение")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(7)
        font.setBold(True)  # ✨ Выделяем текущее значение жирным
        value_label.setFont(font)
        value_layout.addWidget(value_label)
        
        self.value_spinbox = QDoubleSpinBox()
        self.value_spinbox.setDecimals(self._decimals)
        self.value_spinbox.setMinimumWidth(100)
        self.value_spinbox.setMaximumWidth(120)
        self.value_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # ✨ Выделяем поле значения
        self.value_spinbox.setStyleSheet("QDoubleSpinBox { font-weight: bold; }")
        value_layout.addWidget(self.value_spinbox)
        controls_layout.addLayout(value_layout)
        
        # Units label рядом с полем значения
        if self._units:
            self.units_label = QLabel(self._units)
            font = QFont()
            font.setPointSize(9)
            font.setBold(True)
            self.units_label.setFont(font)
            self.units_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            controls_layout.addWidget(self.units_label)
        
        # Растягивающееся пространство между значением и макс
        controls_layout.addStretch()
        
        # Max controls
        max_layout = QVBoxLayout()
        max_layout.setSpacing(1)
        max_label = QLabel("Макс")
        max_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(7)
        max_label.setFont(font)
        max_layout.addWidget(max_label)
        
        self.max_spinbox = QDoubleSpinBox()
        self.max_spinbox.setDecimals(self._decimals)
        self.max_spinbox.setRange(-1e6, 1e6)
        self.max_spinbox.setMinimumWidth(80)
        self.max_spinbox.setMaximumWidth(100)
        self.max_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # ✨ Tooltip для max
        self.max_spinbox.setToolTip("Максимальное значение диапазона")
        max_layout.addWidget(self.max_spinbox)
        controls_layout.addLayout(max_layout)
        
        layout.addLayout(controls_layout)
    
    def _connect_signals(self):
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.value_spinbox.valueChanged.connect(self._on_value_spinbox_changed)
        self.min_spinbox.valueChanged.connect(self._on_min_changed)
        self.max_spinbox.valueChanged.connect(self._on_max_changed)
    
    def setValue(self, value):
        value = max(self.minimum(), min(self.maximum(), value))
        slider_pos = self._value_to_slider(value)
        self._updating_internally = True
        self.slider.setValue(slider_pos)
        self.value_spinbox.setValue(value)
        self._updating_internally = False
        # ✨ Обновить индикаторы
        self._update_indicators()
    
    def value(self):
        return self.value_spinbox.value()
    
    def setRange(self, minimum, maximum):
        if maximum <= minimum:
            raise ValueError("Maximum must be greater than minimum")
        
        current_value = self.value_spinbox.value() if hasattr(self, 'value_spinbox') else minimum
        self._updating_internally = True
        
        if hasattr(self, 'min_spinbox'):
            self.min_spinbox.blockSignals(True)
            self.max_spinbox.blockSignals(True)
            self.min_spinbox.setValue(minimum)
            self.max_spinbox.setValue(maximum)
            self.min_spinbox.blockSignals(False)
            self.max_spinbox.blockSignals(False)
        
        self._update_spinbox_ranges()
        self._updating_internally = False
        
        if hasattr(self, 'value_spinbox'):
            self.setValue(current_value)
        
        # ✨ Обновить индикаторы диапазона
        self._update_indicators()
    
    def minimum(self):
        return self.min_spinbox.value() if hasattr(self, 'min_spinbox') else 0.0
    
    def maximum(self):
        return self.max_spinbox.value() if hasattr(self, 'max_spinbox') else 100.0
    
    def _value_to_slider(self, value):
        min_val = self.minimum()
        max_val = self.maximum()
        if max_val <= min_val:
            return 0
        value = max(min_val, min(max_val, value))
        ratio = (value - min_val) / (max_val - min_val)
        return int(ratio * self._slider_resolution)
    
    def _slider_to_value(self, slider_pos):
        min_val = self.minimum()
        max_val = self.maximum()
        ratio = slider_pos / self._slider_resolution
        value = min_val + ratio * (max_val - min_val)
        
        # УЛУЧШЕННОЕ округление для дискретности 0.001м
        if self._step > 0:
            # Вычисляем количество шагов от минимума
            steps = round((value - min_val) / self._step)
            value = min_val + steps * self._step
            
            # Дополнительное округление для устранения погрешностей float
            # Для шага 0.001 округляем до 3 знаков после запятой
            if self._step == 0.001:
                value = round(value, 3)
            elif self._step == 0.01:
                value = round(value, 2)
            elif self._step == 0.1:
                value = round(value, 1)
            else:
                # Автоматическое определение точности на основе шага
                decimal_places = max(0, -int(round(math.log10(abs(self._step)))))
                value = round(value, decimal_places)
        
        return max(min_val, min(max_val, value))
    
    # ✨ ОБНОВЛЕННЫЙ МЕТОД для индикаторов с шириной диапазона БЕЗ СКОБОК
    def _update_indicators(self):
        """Обновить индикаторы диапазона, ширины диапазона и позиции"""
        if not hasattr(self, 'range_indicator_label'):
            return
            
        min_val = self.minimum()
        max_val = self.maximum()
        current_val = self.value()
        
        # ✨ ОБНОВЛЕНО: Вычисляем ширину диапазона (абсолютное значение)
        range_width = abs(max_val - min_val)
        
        # ОБНОВЛЕНО: Индикатор диапазона с шириной диапазона БЕЗ СКОБОК
        range_text = f"Диапазон: {min_val:.{self._decimals}f} — {max_val:.{self._decimals}f} ширина диапазона {range_width:.{self._decimals}f}"
        if self._units:
            range_text += f" {self._units}"
        self.range_indicator_label.setText(range_text)
        
        # Обновить индикатор позиции и цвет
        if max_val > min_val:
            position_ratio = (current_val - min_val) / (max_val - min_val)
            position_percent = position_ratio * 100;
            
            position_text = f"Позиция: {position_percent:.1f}% от диапазона"
            self.position_indicator_label.setText(position_text)
            
            # ✨ Цветовое кодирование позиции
            color = self._get_position_color(position_ratio)
            palette = self.position_indicator_label.palette()
            palette.setColor(QPalette.ColorRole.WindowText, color)
            self.position_indicator_label.setPalette(palette)
            
            # ✨ Обновить tooltip с подробной информацией включая ширину диапазона
            tooltip = (f"Текущее значение: {current_val:.{self._decimals}f} {self._units}\n"
                      f"Диапазон: {min_val:.{self._decimals}f} до {max_val:.{self._decimals}f}\n"
                      f"Ширина диапазона: {range_width:.{self._decimals}f} {self._units}\n"
                      f"Позиция: {position_percent:.1f}% от диапазона\n"
                      f"Шаг: {self._step:.{self._decimals}f}")
            self.value_spinbox.setToolTip(tooltip)
    
    def _get_position_color(self, ratio):
        """Получить цвет в зависимости от позиции в диапазоне"""
        if ratio < 0.1 or ratio > 0.9:
            # Красный - близко к краям диапазона
            return QColor(200, 50, 50)
        elif ratio < 0.2 or ratio > 0.8:
            # Оранжевый - довольно близко к краям
            return QColor(200, 120, 50)
        else:
            # Зеленый - в нормальной части диапазона
            return QColor(50, 150, 50)
    
    @Slot(int)
    def _on_slider_changed(self, slider_value):
        if self._updating_internally:
            return
            
        real_value = self._slider_to_value(slider_value)
        
        self._updating_internally = True
        self.value_spinbox.setValue(real_value)
        self._updating_internally = False
        
        # ✨ Обновить индикаторы
        self._update_indicators()
        
        # МГНОВЕННОЕ обновление через valueChanged (без задержки)
        self.valueChanged.emit(real_value)
        
        # Задерженное обновление через valueEdited (для финальных изменений)
        self._debounce_timer.start(self._debounce_delay)
    
    @Slot(float)
    def _on_value_spinbox_changed(self, spinbox_value):
        if self._updating_internally:
            return
        spinbox_value = max(self.minimum(), min(self.maximum(), spinbox_value))
        slider_pos = self._value_to_slider(spinbox_value)
        self._updating_internally = True
        self.slider.setValue(slider_pos)
        self._updating_internally = False
        
        # ✨ Обновить индикаторы
        self._update_indicators()
        
        # МГНОВЕННОЕ обновление через valueChanged (без задержки)
        self.valueChanged.emit(spinbox_value)
        
        # Задерженное обновление через valueEdited (для финальных изменений)
        self._debounce_timer.start(self._debounce_delay)
    
    @Slot(float)
    def _on_min_changed(self, new_min):
        if self._updating_internally:
            return
        current_max = self.maximum()
        current_value = self.value()
        if new_min >= current_max:
            new_max = new_min + max(self._step, 0.01)
            self._updating_internally = True
            self.max_spinbox.setValue(new_max)
            self._updating_internally = False
            current_max = new_max
        self._update_spinbox_ranges()
        if current_value < new_min:
            self.setValue(new_min)
        else:
            self._update_slider_position()
        
        # ✨ Обновить индикаторы при изменении диапазона
        self._update_indicators()
        self.rangeChanged.emit(new_min, current_max)
    
    @Slot(float)
    def _on_max_changed(self, new_max):
        if self._updating_internally:
            return
        current_min = self.minimum()
        current_value = self.value()
        if new_max <= current_min:
            new_min = new_max - max(self._step, 0.01)
            self._updating_internally = True
            self.min_spinbox.setValue(new_min)
            self._updating_internally = False
            current_min = new_min
        self._update_spinbox_ranges()
        if current_value > new_max:
            self.setValue(new_max)
        else:
            self._update_slider_position()
        
        # ✨ Обновить индикаторы при изменении диапазона
        self._update_indicators()
        self.rangeChanged.emit(current_min, new_max)
    
    def _update_spinbox_ranges(self):
        if not hasattr(self, 'min_spinbox'):
            return
        min_val = self.min_spinbox.value()
        max_val = self.max_spinbox.value()
        self.min_spinbox.blockSignals(True)
        self.max_spinbox.blockSignals(True)
        self.min_spinbox.setRange(-1e6, 1e6)
        self.max_spinbox.setRange(-1e6, 1e6)
        self.value_spinbox.setMinimum(min_val)
        self.value_spinbox.setMaximum(max_val)
        self.value_spinbox.setSingleStep(self._step)
        self.min_spinbox.blockSignals(False)
        self.max_spinbox.blockSignals(False)
    
    def _update_slider_position(self):
        current_value = self.value_spinbox.value()
        slider_pos = self._value_to_slider(current_value)
        self._updating_internally = True
        self.slider.setValue(slider_pos)
        self._updating_internally = False
        # ✨ Обновить индикаторы
        self._update_indicators()
    
    @Slot()
    def _emit_value_edited(self):
        self.valueEdited.emit(self.value())
    
    def setDecimals(self, decimals):
        self._decimals = decimals
        if hasattr(self, 'min_spinbox'):
            self.min_spinbox.setDecimals(decimals)
            self.value_spinbox.setDecimals(decimals)
            self.max_spinbox.setDecimals(decimals)
            # ✨ Обновить индикаторы с новой точностью
            self._update_indicators()
    
    def setStep(self, step):
        self._step = step
        if hasattr(self, 'value_spinbox'):
            self.value_spinbox.setSingleStep(step)
            # ✨ Обновить tooltip
            self._update_indicators()
    
    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        if hasattr(self, 'slider'):
            self.slider.setEnabled(enabled)
            self.min_spinbox.setEnabled(enabled)
            self.value_spinbox.setEnabled(enabled)
            self.max_spinbox.setEnabled(enabled)
    
    def __del__(self):
        """Очистка ресурсов при уничтожении виджета"""
        try:
            if hasattr(self, '_debounce_timer') and self._debounce_timer is not None:
                # Проверяем, что объект еще существует в C++
                if hasattr(self._debounce_timer, 'stop'):
                    self._debounce_timer.stop()
                self._debounce_timer = None
        except (RuntimeError, AttributeError):
            # Объект уже удален в C++ или атрибут отсутствует
            pass
    
    def cleanup(self):
        """Явная очистка ресурсов"""
        try:
            if hasattr(self, '_debounce_timer') and self._debounce_timer is not None:
                self._debounce_timer.stop()
                self._debounce_timer.deleteLater()
                self._debounce_timer = None
        except (RuntimeError, AttributeError):
            # Объект уже удален или недоступен
            pass
