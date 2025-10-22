# -*- coding: utf-8 -*-
"""
Graphics panel widgets - reusable UI components
Виджеты панели графики - переиспользуемые компоненты UI
"""
from __future__ import annotations


from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...core.units import Quantity, Unit


class ColorButton(QPushButton):
    """Небольшая кнопка предпросмотра цвета, транслирующая изменения из QColorDialog."""

    color_changed = Signal(str)

    def __init__(
        self, initial_color: str = "#ffffff", parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setFixedSize(42, 28)
        self._color = QColor(initial_color)
        self._dialog: QColorDialog | None = None
        self._user_triggered = False  # Флаг пользовательского действия
        self._update_swatch()
        self.clicked.connect(self._open_dialog)

    def color(self) -> QColor:
        return self._color

    def set_color(self, color_str: str) -> None:
        """Программное изменение цвета (без логирования)."""
        self._color = QColor(color_str)
        self._update_swatch()

    def _update_swatch(self) -> None:
        self.setStyleSheet(
            "QPushButton {"
            f"background-color: {self._color.name()};"
            "border: 2px solid #5c5c5c;"
            "border-radius: 4px;"
            "}"
            "QPushButton:hover { border: 2px solid #9a9a9a; }"
        )

    @Slot()
    def _open_dialog(self) -> None:
        # Пользователь кликнул на кнопку
        self._user_triggered = True
        if self._dialog:
            return
        dialog = QColorDialog(self._color, self)
        dialog.setOption(QColorDialog.DontUseNativeDialog, True)
        dialog.setOption(QColorDialog.ShowAlphaChannel, False)
        dialog.currentColorChanged.connect(self._on_color_changed)
        dialog.colorSelected.connect(self._on_color_changed)
        dialog.finished.connect(self._close_dialog)
        dialog.open()
        self._dialog = dialog

    @Slot(QColor)
    def _on_color_changed(self, color: QColor) -> None:
        if not color.isValid():
            return
        self._color = color
        self._update_swatch()
        if self._user_triggered:
            self.color_changed.emit(color.name())

    @Slot()
    def _close_dialog(self) -> None:
        if self._dialog:
            self._dialog.deleteLater()
        self._dialog = None
        self._user_triggered = False


class LabeledSlider(QWidget):
    """Пара слайдер + спинбокс с подписью и единицами измерения."""

    valueChanged = Signal(float)

    def __init__(
        self,
        title: str,
        minimum: float,
        maximum: float,
        step: float,
        *,
        decimals: int = 2,
        unit: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._min = minimum
        self._max = maximum
        self._step = step
        self._decimals = decimals
        self._unit = unit or ""
        self._updating = False
        self._user_triggered = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._label = QLabel(self)
        layout.addWidget(self._label)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        layout.addLayout(row)

        # Используем QtWidgets.QSlider для надёжности
        from PySide6 import QtWidgets

        self._slider = QtWidgets.QSlider(Qt.Horizontal, self)
        steps = max(1, int(round((self._max - self._min) / self._step)))
        self._slider.setRange(0, steps)
        self._slider.sliderPressed.connect(self._on_slider_pressed)
        self._slider.sliderReleased.connect(self._on_slider_released)
        self._slider.valueChanged.connect(self._handle_slider)
        row.addWidget(self._slider, 1)

        self._spin = QDoubleSpinBox(self)
        self._spin.setDecimals(self._decimals)
        self._spin.setRange(self._min, self._max)
        self._spin.setSingleStep(self._step)
        self._spin.installEventFilter(self)
        self._spin.valueChanged.connect(self._handle_spin)
        row.addWidget(self._spin)

        self.set_value(self._min)

    def eventFilter(self, obj, event) -> bool:
        if obj == self._spin:
            if event.type() == event.Type.FocusIn:
                self._user_triggered = True
            elif event.type() == event.Type.FocusOut:
                self._user_triggered = False
        return super().eventFilter(obj, event)

    @Slot()
    def _on_slider_pressed(self) -> None:
        self._user_triggered = True

    @Slot()
    def _on_slider_released(self) -> None:
        self._user_triggered = False

    def set_enabled(self, enabled: bool) -> None:
        self.setEnabled(enabled)

    def value(self) -> float:
        return round(self._spin.value(), self._decimals)

    def set_value(self, value: float) -> None:
        value = max(self._min, min(self._max, value))
        slider_value = int(round((value - self._min) / self._step))
        self._updating = True
        self._slider.setValue(slider_value)
        self._spin.setValue(value)
        self._update_label(value)
        self._updating = False

    def _update_label(self, value: float) -> None:
        formatted = f"{value:.{self._decimals}f}"
        if self._unit:
            formatted = f"{formatted} {self._unit}"
        self._label.setText(f"{self._title}: {formatted}")

    @Slot(int)
    def _handle_slider(self, slider_value: int) -> None:
        if self._updating:
            return
        value = self._min + slider_value * self._step
        value = max(self._min, min(self._max, value))
        self._updating = True
        self._spin.setValue(value)
        self._update_label(value)
        self._updating = False
        if self._user_triggered:
            self.valueChanged.emit(round(value, self._decimals))

    @Slot(float)
    def _handle_spin(self, value: float) -> None:
        if self._updating:
            return
        slider_value = int(round((value - self._min) / self._step))
        self._updating = True
        self._slider.setValue(slider_value)
        self._update_label(value)
        self._updating = False
        if self._user_triggered:
            self.valueChanged.emit(round(value, self._decimals))


class QuantitySlider(LabeledSlider):
    """Слайдер для изменения Quantity."""

    valueChanged = Signal(Quantity)

    def __init__(
        self,
        title: str,
        quantity: Quantity,
        *,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            title,
            quantity.definition.minimal.value,
            quantity.definition.maximal.value,
            quantity.definition.small_step or 1.0,
            decimals=quantity.definition.decimals,
            unit=quantity.definition.unit,
            parent=parent,
        )
        self.set_value(quantity.value)

    def value(self) -> Quantity:
        base_value = super().value()
        return Quantity(base_value, self._unit)

    def set_value(self, value: Quantity | float) -> None:
        if isinstance(value, Quantity):
            value = value.value
        super().set_value(value)

    @Slot()
    def _handle_slider(self, slider_value: int) -> None:
        if self._updating:
            return
        value = self._min + slider_value * self._step
        value = max(self._min, min(self._max, value))
        self._updating = True
        self._spin.setValue(value)
        self._update_label(value)
        self._updating = False
        if self._user_triggered:
            self.valueChanged.emit(Quantity(value, self._unit))

    @Slot(float)
    def _handle_spin(self, value: float) -> None:
        if self._updating:
            return
        slider_value = int(round((value - self._min) / self._step))
        self._updating = True
        self._slider.setValue(slider_value)
        self._update_label(value)
        self._updating = False
        if self._user_triggered:
            self.valueChanged.emit(Quantity(value, self._unit))
