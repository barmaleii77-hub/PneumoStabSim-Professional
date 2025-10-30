# -*- coding: utf-8 -*-
"""
Graphics panel widgets - reusable UI components
Виджеты панели графики - переиспользуемые компоненты UI
"""

from __future__ import annotations


from dataclasses import dataclass
from pathlib import Path

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


@dataclass(frozen=True)
class QuantityDefinition:
    """Simple metadata describing how a quantity can vary."""

    minimal: float
    maximal: float
    decimals: int = 2
    unit: str = ""
    small_step: float | None = None

    def clamp(self, value: float) -> float:
        """Clamp *value* into the allowed range."""

        return max(self.minimal, min(self.maximal, value))


@dataclass
class Quantity:
    """Scalar value bundled with presentation metadata."""

    value: float
    definition: QuantityDefinition

    def __post_init__(self) -> None:
        self.value = self.definition.clamp(float(self.value))


Unit = str


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


class FileCyclerWidget(QWidget):
    """Минималистичный селектор файлов с кнопками «предыдущий/следующий».

    Элемент предназначен для перебора заранее обнаруженных файлов без
    диалогов выбора. Отображает имя текущего файла и эмитит ``currentChanged``
    при смене выбора. Если список пуст, показывает прочерк и отключает кнопки.
    """

    currentChanged = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        placeholder: str = "—",
    ) -> None:
        super().__init__(parent)

        self._placeholder = placeholder
        self._items: list[tuple[str, str]] = []
        self._index: int = -1
        self._custom_entry: tuple[str, str] | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._prev_btn = QPushButton("◀", self)
        self._prev_btn.setFixedWidth(28)
        self._prev_btn.clicked.connect(self._show_previous)
        layout.addWidget(self._prev_btn)

        self._label = QLabel(self)
        self._label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._label.setMinimumWidth(80)
        self._label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        layout.addWidget(self._label, 1)

        self._next_btn = QPushButton("▶", self)
        self._next_btn.setFixedWidth(28)
        self._next_btn.clicked.connect(self._show_next)
        layout.addWidget(self._next_btn)

        self._update_ui(emit=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_items(self, items: list[tuple[str, str]]) -> None:
        """Задать коллекцию доступных файлов.

        ``items`` — список пар ``(label, path)``. Пути нормализуются в POSIX
        представление. При повторном вызове сохраняется текущий выбор, если
        соответствующий путь присутствует в новом списке.
        """

        normalised: list[tuple[str, str]] = []
        seen: set[str] = set()
        for label, path in items:
            try:
                text = (Path(path).as_posix()).strip()
            except Exception:
                text = str(path).strip().replace("\\", "/")
            if not text or text in seen:
                continue
            seen.add(text)
            name = str(label).strip() or Path(text).name or text
            normalised.append((name, text))

        previous_path = self.current_path()
        self._items = normalised

        if previous_path:
            self.set_current_data(previous_path, emit=False)
        elif self._items:
            self._index = 0
            self._custom_entry = None
            self._update_ui(emit=False)
        else:
            self._index = -1
            if self._custom_entry and self._custom_entry[1] not in seen:
                self._custom_entry = None
            self._update_ui(emit=False)

    def set_current_data(self, path: str | None, *, emit: bool = True) -> None:
        """Установить текущий путь. Допускает значения вне списка items."""

        normalised = str(path).strip().replace("\\", "/") if path else ""
        if not normalised:
            changed = self._index != -1 or self._custom_entry is not None
            self._index = -1
            self._custom_entry = None
            self._update_ui(emit=emit and changed)
            return

        for idx, (_, candidate) in enumerate(self._items):
            if candidate == normalised:
                changed = self._index != idx or self._custom_entry is not None
                self._index = idx
                self._custom_entry = None
                self._update_ui(emit=emit and changed)
                return

        label = Path(normalised).name or normalised
        custom_label = f"{label} (config)"
        changed = (
            self._index != -1
            or self._custom_entry is None
            or self._custom_entry[1] != normalised
        )
        self._index = -1
        self._custom_entry = (custom_label, normalised)
        self._update_ui(emit=emit and changed)

    def current_path(self) -> str:
        entry = self._current_entry()
        return entry[1] if entry else ""

    def current_label(self) -> str:
        entry = self._current_entry()
        return entry[0] if entry else self._placeholder

    def is_empty(self) -> bool:
        return not self._items and self._custom_entry is None

    def first_path(self) -> str:
        return self._items[0][1] if self._items else ""

    def setEnabled(self, enabled: bool) -> None:  # noqa: D401 - override QWidget
        super().setEnabled(enabled)
        self._update_ui(emit=False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _current_entry(self) -> tuple[str, str] | None:
        if 0 <= self._index < len(self._items):
            return self._items[self._index]
        if self._custom_entry is not None:
            return self._custom_entry
        return None

    def _update_ui(self, *, emit: bool) -> None:
        entry = self._current_entry()
        if entry:
            label, path = entry
            self._label.setText(label)
        else:
            path = ""
            self._label.setText(self._placeholder)

        multi = len(self._items) > 1
        any_items = bool(self._items)
        enable_buttons = self.isEnabled() and (
            multi or (any_items and self._custom_entry is not None)
        )
        self._prev_btn.setEnabled(enable_buttons)
        self._next_btn.setEnabled(enable_buttons)

        if emit:
            self.currentChanged.emit(path)

    def _show_previous(self) -> None:
        if not self._items:
            return
        if self._custom_entry is not None:
            self._index = len(self._items) - 1
            self._custom_entry = None
        else:
            self._index = (self._index - 1) % len(self._items)
        self._update_ui(emit=True)

    def _show_next(self) -> None:
        if not self._items:
            return
        if self._custom_entry is not None:
            self._index = 0
            self._custom_entry = None
        else:
            self._index = (self._index + 1) % len(self._items)
        self._update_ui(emit=True)


class QuantitySlider(LabeledSlider):
    """Слайдер для изменения Quantity."""

    valueChanged = Signal(object)

    def __init__(
        self,
        title: str,
        quantity: Quantity,
        *,
        parent: QWidget | None = None,
    ) -> None:
        definition = quantity.definition
        self._definition = definition
        super().__init__(
            title,
            definition.minimal,
            definition.maximal,
            definition.small_step or 1.0,
            decimals=definition.decimals,
            unit=definition.unit,
            parent=parent,
        )
        self.set_value(quantity.value)

    def value(self) -> Quantity:
        base_value = super().value()
        return Quantity(base_value, self._definition)

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
            self.valueChanged.emit(Quantity(value, self._definition))

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
            self.valueChanged.emit(Quantity(value, self._definition))
