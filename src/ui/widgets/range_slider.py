# -*- coding: utf-8 -*-
"""Rich range slider widget used throughout the geometry panel.

The widget exposes both live updates (``valueChanged``) and debounced updates
(``valueEdited``) to mirror the behaviour of the historical implementation.

Key refinements introduced during the refactor:

* Более мелкие деления шкалы для более точной подстройки параметров.
* Индикатор ширины диапазона выводится без скобок для наглядности.
* Поля «Мин», «Значение», «Макс» выровнены по горизонтали.
* Шкала слайдера растягивается на всю ширину доступной области.
* Добавлены цветовые подсказки и всплывающие подсказки.
"""

from __future__ import annotations

import math
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSlider,
    QDoubleSpinBox,
    QSizePolicy,
)
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
    valueEdited = Signal(float)  # Финальное значение после debounce
    valueChanged = Signal(float)  # Мгновенное значение во время движения
    rangeChanged = Signal(float, float)

    def __init__(
        self,
        minimum=0.0,
        maximum=100.0,
        value=50.0,
        step=1.0,
        decimals=2,
        units="",
        title="",
        parent=None,
    ):
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

        # ✨ ОБНОВЛЕНО: Индикатор диапазона с ширной диапазона без скобок
        self.range_indicator_label = QLabel(
            "Диапазон: 0.0 — 100.0 ширина диапазона 100.0"
        )
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
        value_label.setFont(font)
        value_layout.addWidget(value_label)

        self.value_spinbox = QDoubleSpinBox()
        self.value_spinbox.setDecimals(self._decimals)
        self.value_spinbox.setRange(-1e6, 1e6)
        self.value_spinbox.setMinimumWidth(100)
        self.value_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # ✨ Tooltip для value
        self.value_spinbox.setToolTip("Текущее значение параметра")
        value_layout.addWidget(self.value_spinbox)
        controls_layout.addLayout(value_layout)

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

        # ✨ Дополнительный индикатор единиц измерения
        self.units_label = QLabel()
        self.units_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(7)
        font.setItalic(True)
        self.units_label.setFont(font)
        layout.addWidget(self.units_label)

    def _connect_signals(self):
        self.slider.valueChanged.connect(self._on_slider_value_changed)
        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderReleased.connect(self._on_slider_released)

        self.value_spinbox.valueChanged.connect(self._on_value_spinbox_changed)
        self.value_spinbox.editingFinished.connect(self._on_value_spinbox_finished)

        self.min_spinbox.valueChanged.connect(self._on_min_spinbox_changed)
        self.max_spinbox.valueChanged.connect(self._on_max_spinbox_changed)

    # =========================================================================
    # CONFIGURATION
    # =========================================================================
    def setDecimals(self, decimals):
        self._decimals = decimals
        self.value_spinbox.setDecimals(decimals)
        self.min_spinbox.setDecimals(decimals)
        self.max_spinbox.setDecimals(decimals)

    def setRange(self, minimum, maximum):
        if minimum >= maximum:
            maximum = minimum + abs(self._step) if self._step else minimum + 0.001

        self._minimum = minimum
        self._maximum = maximum
        self.min_spinbox.blockSignals(True)
        self.max_spinbox.blockSignals(True)
        try:
            self.min_spinbox.setValue(minimum)
            self.max_spinbox.setValue(maximum)
        finally:
            self.min_spinbox.blockSignals(False)
            self.max_spinbox.blockSignals(False)
        self._update_range_indicator()
        self.rangeChanged.emit(minimum, maximum)

    def setUnits(self, units: str):
        self._units = units
        if units:
            self.units_label.setText(f"Единицы: {units}")
        else:
            self.units_label.clear()

    def setTitle(self, title: str):
        if hasattr(self, "title_label"):
            self.title_label.setText(title)
        else:
            self.title_label = QLabel(title)

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================
    def setValue(self, value):
        value = float(value)
        value = max(self._minimum, min(self._maximum, value))
        if math.isclose(value, self.value_spinbox.value(), rel_tol=1e-9, abs_tol=1e-9):
            self._update_slider_position(value)
            return

        self.value_spinbox.blockSignals(True)
        try:
            self.value_spinbox.setValue(value)
        finally:
            self.value_spinbox.blockSignals(False)
        self._update_slider_position(value)

    def value(self):
        return self.value_spinbox.value()

    def minimum(self):
        return self._minimum

    def maximum(self):
        return self._maximum

    def setEnabled(self, enabled):  # noqa: D401 - Qt signature compatibility
        """Enable or disable the slider and its inputs."""

        super().setEnabled(enabled)
        for widget in (
            self.slider,
            self.min_spinbox,
            self.value_spinbox,
            self.max_spinbox,
        ):
            widget.setEnabled(enabled)

    # =========================================================================
    # INTERNAL UPDATES
    # =========================================================================
    def _update_slider_position(self, value):
        if self._maximum == self._minimum:
            position = 0
        else:
            position = int(
                (value - self._minimum)
                / (self._maximum - self._minimum)
                * self._slider_resolution
            )

        self._updating_internally = True
        try:
            self.slider.setValue(position)
        finally:
            self._updating_internally = False
        self._update_position_indicator(position)

    def _update_range_indicator(self):
        width = self._maximum - self._minimum
        self.range_indicator_label.setText(
            f"Диапазон: {self._minimum:.{self._decimals}f} — {self._maximum:.{self._decimals}f} "
            f"ширина диапазона {width:.{self._decimals}f}"
            + (f" {self._units}" if self._units else "")
        )

    def _update_position_indicator(self, position):
        if self._slider_resolution == 0:
            percentage = 0
        else:
            percentage = position / self._slider_resolution * 100
        self.position_indicator_label.setText(
            f"Позиция: {percentage:.1f}% от диапазона"
        )

    # =========================================================================
    # SIGNAL HANDLERS
    # =========================================================================
    @Slot()
    def _on_slider_pressed(self):
        self._debounce_timer.stop()

    @Slot()
    def _on_slider_released(self):
        self._debounce_timer.start(self._debounce_delay)

    @Slot(int)
    def _on_slider_value_changed(self, position):
        if self._updating_internally:
            return

        value = self._minimum + (
            (self._maximum - self._minimum) * position / self._slider_resolution
        )
        value = round(value / self._step) * self._step if self._step else value
        value = max(self._minimum, min(self._maximum, value))

        self.value_spinbox.blockSignals(True)
        try:
            self.value_spinbox.setValue(value)
        finally:
            self.value_spinbox.blockSignals(False)

        self.valueChanged.emit(value)
        self._debounce_timer.start(self._debounce_delay)
        self._update_position_indicator(position)

    @Slot(float)
    def _on_value_spinbox_changed(self, value):
        self._update_slider_position(value)
        self.valueChanged.emit(value)
        self._debounce_timer.start(self._debounce_delay)

    @Slot()
    def _on_value_spinbox_finished(self):
        self._debounce_timer.start(self._debounce_delay)

    @Slot(float)
    def _on_min_spinbox_changed(self, value):
        if value >= self._maximum:
            value = (
                self._maximum - abs(self._step) if self._step else self._maximum - 0.001
            )
            self.min_spinbox.blockSignals(True)
            try:
                self.min_spinbox.setValue(value)
            finally:
                self.min_spinbox.blockSignals(False)

        self._minimum = value
        self._update_range_indicator()
        self._update_slider_position(self.value_spinbox.value())
        self.rangeChanged.emit(self._minimum, self._maximum)

    @Slot(float)
    def _on_max_spinbox_changed(self, value):
        if value <= self._minimum:
            value = (
                self._minimum + abs(self._step) if self._step else self._minimum + 0.001
            )
            self.max_spinbox.blockSignals(True)
            try:
                self.max_spinbox.setValue(value)
            finally:
                self.max_spinbox.blockSignals(False)

        self._maximum = value
        self._update_range_indicator()
        self._update_slider_position(self.value_spinbox.value())
        self.rangeChanged.emit(self._minimum, self._maximum)

    def _emit_value_edited(self):
        value = self.value_spinbox.value()
        self.valueEdited.emit(value)


__all__ = ["RangeSlider"]
