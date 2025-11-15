"""Rich range slider widget used throughout the geometry panel.

The widget exposes both live updates (``valueChanged``) and debounced updates
(""valueEdited"") to mirror the behaviour of the historical implementation.

Key refinements introduced during the refactor:

* Более мелкие деления шкалы для более точной подстройки параметров.
* Индикатор ширины диапазона выводится без скобок для наглядности.
* Поля «Мин», «Значение», «Макс» выровнены по горизонтали.
* Шкала слайдера растягивается на всю ширину доступной области.
* Добавлены цветовые подсказки и всплывающие подсказки.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSlider,
    QDoubleSpinBox,
    QSizePolicy,
    QSpinBox,
    QLineEdit,
)
from PySide6.QtCore import Signal, Slot, QTimer, Qt
from PySide6.QtGui import QFont, QPalette, QColor, QKeySequence, QShortcut, QKeyEvent


ShortcutCallback = Callable[[], None]
SpinBoxTriple = tuple[QDoubleSpinBox, QDoubleSpinBox, QDoubleSpinBox]


@dataclass(slots=True)
class AccessibilityShortcut:
    """Shortcut metadata surfaced for assistive tooling."""

    identifier: str
    sequence: str
    description: str


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
    # Добавляем сигналы мета-параметров для внешней сериализации
    stepChanged = Signal(float)
    decimalsChanged = Signal(int)
    unitsChanged = Signal(str)

    def __init__(
        self,
        minimum: float = 0.0,
        maximum: float = 100.0,
        value: float = 50.0,
        step: float = 1.0,
        decimals: int = 2,
        units: str = "",
        title: str = "",
        parent: QWidget | None = None,
        accessible_name: str | None = None,
        accessible_role: str | None = None,
        increase_shortcut: str = "Ctrl+Alt+Right",
        decrease_shortcut: str = "Ctrl+Alt+Left",
        focus_min_shortcut: str = "Ctrl+Alt+1",
        focus_value_shortcut: str = "Ctrl+Alt+2",
        focus_max_shortcut: str = "Ctrl+Alt+3",
    ) -> None:
        super().__init__(parent)
        self._step = step
        self._decimals = decimals
        self._units = units
        self._accessible_label = accessible_name or ""
        self._accessible_role = accessible_role or "range-slider"
        self._shortcut_metadata: list[AccessibilityShortcut] = []

        self.title_label: QLabel | None = None
        self.range_indicator_label: QLabel
        self.slider: QSlider
        self.position_indicator_label: QLabel
        self.min_spinbox: QDoubleSpinBox
        self.value_spinbox: QDoubleSpinBox
        self.max_spinbox: QDoubleSpinBox
        self.units_label: QLabel
        self.step_spinbox: QDoubleSpinBox
        self.decimals_spinbox: QSpinBox
        self.units_edit: QLineEdit

        # УВЕЛИЧЕННОЕ разрешение слайдера для точности 0.001м
        # Для диапазона 4м с шагом 0.001м нужно 4000 позиций
        # Используем 100000 для запаса и плавности
        self._slider_resolution = 100000
        self._updating_internally = False

        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_value_edited)
        self._debounce_delay = 200

        self._setup_ui(title)
        self._configure_accessibility(title)
        self.setRange(minimum, maximum)
        self.setStepSize(step)
        self.setValue(value)
        self._connect_signals()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._setup_shortcuts(
            increase_shortcut,
            decrease_shortcut,
            focus_min_shortcut,
            focus_value_shortcut,
            focus_max_shortcut,
        )
        self._refresh_accessibility_descriptions()

    def _setup_ui(self, title: str) -> None:
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
            self.title_label.setAccessibleName(self.tr("%1 title").replace("%1", title))

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
        self.slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

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

        # ✨ Редактируемые параметры шага, точности и единиц
        params_layout = QHBoxLayout()
        params_layout.setSpacing(6)

        step_box = QVBoxLayout()
        step_label = QLabel("Шаг")
        step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont()
        f.setPointSize(7)
        step_label.setFont(f)
        step_box.addWidget(step_label)
        self.step_spinbox = QDoubleSpinBox()
        self.step_spinbox.setRange(1e-12, 1e6)
        self.step_spinbox.setDecimals(6)
        self.step_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_spinbox.setToolTip("Логический шаг квантования и клавиатурного нуджа")
        step_box.addWidget(self.step_spinbox)
        params_layout.addLayout(step_box)

        dec_box = QVBoxLayout()
        dec_label = QLabel("Точность")
        dec_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dec_label.setFont(f)
        dec_box.addWidget(dec_label)
        self.decimals_spinbox = QSpinBox()
        self.decimals_spinbox.setRange(0, 10)
        self.decimals_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.decimals_spinbox.setToolTip("Количество знаков после запятой")
        dec_box.addWidget(self.decimals_spinbox)
        params_layout.addLayout(dec_box)

        units_box = QVBoxLayout()
        units_label = QLabel("Ед. изм.")
        units_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        units_label.setFont(f)
        units_box.addWidget(units_label)
        self.units_edit = QLineEdit()
        self.units_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.units_edit.setPlaceholderText("мм / м / ...")
        self.units_edit.setToolTip("Единицы измерения для подписи")
        units_box.addWidget(self.units_edit)
        params_layout.addLayout(units_box)

        layout.addLayout(params_layout)

        # Инициализация значений параметров из текущего состояния
        self.step_spinbox.setValue(max(self._step, 1e-12))
        self.decimals_spinbox.setValue(self._decimals)
        self.units_edit.setText(self._units)

        # Связи сигналов UI → поведение виджета
        self.step_spinbox.valueChanged.connect(lambda v: self.setStepSize(float(v)))
        self.decimals_spinbox.valueChanged.connect(self.setDecimals)
        self.units_edit.editingFinished.connect(
            lambda: self.setUnits(self.units_edit.text() or "")
        )

    def _configure_accessibility(self, title: str) -> None:
        """Configure accessibility metadata for assistive technologies."""

        display_label = title or self.tr("Range")
        self._display_label = display_label
        if not self._accessible_label:
            self._accessible_label = self.tr("%1 range slider").replace(
                "%1", display_label
            )

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(self._accessible_label)
        self.setProperty("accessibilityRole", self._accessible_role)
        self._refresh_accessibility_descriptions()

        self.slider.setAccessibleName(
            self.tr("%1 slider track").replace("%1", display_label)
        )
        self.slider.setProperty("accessibilityRole", "slider")

        self.min_spinbox.setAccessibleName(
            self.tr("%1 minimum value").replace("%1", display_label)
        )
        self.min_spinbox.setProperty("accessibilityRole", "spinbox")
        self.value_spinbox.setAccessibleName(
            self.tr("%1 current value").replace("%1", display_label)
        )
        self.value_spinbox.setProperty("accessibilityRole", "spinbox")
        self.max_spinbox.setAccessibleName(
            self.tr("%1 maximum value").replace("%1", display_label)
        )
        self.max_spinbox.setProperty("accessibilityRole", "spinbox")

        for widget in (self.min_spinbox, self.value_spinbox, self.max_spinbox):
            widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        if self.title_label is not None:
            self.title_label.setAccessibleDescription(
                self.tr("Heading for the %1 controls.").replace("%1", display_label)
            )

    def _refresh_accessibility_descriptions(self) -> None:
        """Update descriptions when range or units change."""

        min_value = getattr(self, "_minimum", 0.0)
        max_value = getattr(self, "_maximum", 0.0)
        width = max_value - min_value
        units_suffix = self.tr(" %1").replace("%1", self._units) if self._units else ""

        slider_description = (
            self.tr("Adjust %1 between %2 and %3%4.")
            .replace("%1", self._display_label)
            .replace("%2", f"{min_value:.{self._decimals}f}")
            .replace("%3", f"{max_value:.{self._decimals}f}")
            .replace("%4", units_suffix)
        )
        shortcut_hint = self._compose_shortcut_summary()
        if shortcut_hint:
            slider_description = f"{slider_description} {shortcut_hint}"
        self.setAccessibleDescription(slider_description)
        self.slider.setAccessibleDescription(slider_description)
        self.value_spinbox.setAccessibleDescription(slider_description)

        min_description = self.tr("Sets the minimum bound for %1.").replace(
            "%1", self._display_label
        )
        max_description = self.tr("Sets the maximum bound for %1.").replace(
            "%1", self._display_label
        )
        self.min_spinbox.setAccessibleDescription(min_description)
        self.max_spinbox.setAccessibleDescription(max_description)

        if self.units_label:
            if self._units:
                self.units_label.setAccessibleName(
                    self.tr("Units label for %1").replace("%1", self._display_label)
                )
                self.units_label.setAccessibleDescription(
                    self.tr("Displays the measurement units applied to %1.").replace(
                        "%1", self._display_label
                    )
                )
            else:
                self.units_label.setAccessibleName("")
                self.units_label.setAccessibleDescription("")

        self.range_indicator_label.setAccessibleName(
            self.tr("%1 range summary").replace("%1", self._display_label)
        )
        self.range_indicator_label.setAccessibleDescription(
            self.tr("Current limits span %1 to %2 with a width of %3%4.")
            .replace("%1", f"{min_value:.{self._decimals}f}")
            .replace("%2", f"{max_value:.{self._decimals}f}")
            .replace("%3", f"{width:.{self._decimals}f}")
            .replace("%4", units_suffix)
        )

        self.position_indicator_label.setAccessibleName(
            self.tr("%1 position indicator").replace("%1", self._display_label)
        )

    def _setup_shortcuts(
        self,
        increase_shortcut: str,
        decrease_shortcut: str,
        focus_min_shortcut: str,
        focus_value_shortcut: str,
        focus_max_shortcut: str,
    ) -> None:
        """Expose keyboard shortcuts mirroring pointer interactions."""

        self._shortcut_metadata.clear()

        self._increase_shortcut = self._register_shortcut(
            "increase",
            increase_shortcut,
            lambda: self._nudge_slider(self._step),
            self.tr("Increase %1 by one step (%2)."),
            {
                "%1": self._display_label,
                "%2": increase_shortcut,
            },
        )

        self._decrease_shortcut = self._register_shortcut(
            "decrease",
            decrease_shortcut,
            lambda: self._nudge_slider(-self._step),
            self.tr("Decrease %1 by one step (%2)."),
            {
                "%1": self._display_label,
                "%2": decrease_shortcut,
            },
        )

        self._focus_min_shortcut = self._register_shortcut(
            "focus-min",
            focus_min_shortcut,
            self.min_spinbox.setFocus,
            self.tr("Focus minimum value field (%1)."),
            {"%1": focus_min_shortcut},
        )

        self._focus_value_shortcut = self._register_shortcut(
            "focus-value",
            focus_value_shortcut,
            self.value_spinbox.setFocus,
            self.tr("Focus current value field (%1)."),
            {"%1": focus_value_shortcut},
        )

        self._focus_max_shortcut = self._register_shortcut(
            "focus-max",
            focus_max_shortcut,
            self.max_spinbox.setFocus,
            self.tr("Focus maximum value field (%1)."),
            {"%1": focus_max_shortcut},
        )

    def _register_shortcut(
        self,
        identifier: str,
        sequence_str: str,
        callback: ShortcutCallback,
        description_template: str,
        replacements: dict[str, str] | None = None,
    ) -> QShortcut:
        """Create a shortcut and store metadata for accessibility consumers."""

        shortcut = QShortcut(QKeySequence(sequence_str), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(callback)

        description = description_template
        if replacements:
            for placeholder, value in replacements.items():
                description = description.replace(placeholder, value)
        shortcut.setWhatsThis(description)

        sequence_text = shortcut.key().toString(QKeySequence.SequenceFormat.NativeText)
        self._shortcut_metadata.append(
            AccessibilityShortcut(identifier, sequence_text, description)
        )
        return shortcut

    def _compose_shortcut_summary(self) -> str:
        """Summarise registered shortcuts for accessible descriptions."""

        if not self._shortcut_metadata:
            return ""

        joined = " ".join(shortcut.description for shortcut in self._shortcut_metadata)
        return self.tr("Keyboard shortcuts: %1").replace("%1", joined)

    def accessibilityRole(self) -> str:
        """Expose the semantic role for automated accessibility audits."""

        return self._accessible_role

    def accessibilityShortcuts(self) -> list[AccessibilityShortcut]:
        """Return the shortcuts exposed by the widget."""

        return list(self._shortcut_metadata)

    def _nudge_slider(self, delta: float) -> None:
        """Increment the slider value by *delta*.

        Полностью полагаемся на setValue для эмиссии сигналов и debounce,
        чтобы избежать двойной эмиссии valueChanged.
        """
        target_value = self.value() + delta
        self.setValue(target_value)

    def _connect_signals(self) -> None:
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
    def setDecimals(self, decimals: int) -> None:
        self._decimals = decimals
        self.value_spinbox.setDecimals(decimals)
        self.min_spinbox.setDecimals(decimals)
        self.max_spinbox.setDecimals(decimals)
        # Обновляем UI-спинбокс точности
        try:
            self.decimals_spinbox.blockSignals(True)
            self.decimals_spinbox.setValue(decimals)
        finally:
            self.decimals_spinbox.blockSignals(False)
        self.decimalsChanged.emit(decimals)
        self._update_range_indicator()
        self._refresh_accessibility_descriptions()

    def setRange(self, minimum: float, maximum: float) -> None:
        if minimum >= maximum:
            maximum = minimum + abs(self._step) if self._step else minimum + 0.001

        # Если диапазон не изменился, не выполняем лишние обновления и не эмитим сигнал
        try:
            prev_min = getattr(self, "_minimum")
            prev_max = getattr(self, "_maximum")
        except Exception:
            prev_min = None
            prev_max = None
        if (
            prev_min is not None
            and prev_max is not None
            and math.isclose(prev_min, minimum, rel_tol=1e-12, abs_tol=1e-12)
            and math.isclose(prev_max, maximum, rel_tol=1e-12, abs_tol=1e-12)
        ):
            return

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
        self._refresh_accessibility_descriptions()

    def setUnits(self, units: str) -> None:
        self._units = units
        if units:
            self.units_label.setText(f"Единицы: {units}")
        else:
            self.units_label.clear()
        try:
            self.units_edit.blockSignals(True)
            self.units_edit.setText(units)
        finally:
            self.units_edit.blockSignals(False)
        # Перерисовываем индикатор диапазона с суффиксом единиц
        self._update_range_indicator()
        self.unitsChanged.emit(units)
        self._refresh_accessibility_descriptions()

    def setStepSize(self, step: float) -> None:
        """Обновить логический шаг с жёсткой нормализацией > 0.

        Правила:
        - NaN/inf → 0.001
        - отрицательный или нулевой → abs(value) или 0.001 минимум
        - синхронизируем singleStep всех спинбоксов и значение UI step
        """
        raw_step = float(step)
        if not math.isfinite(raw_step):
            raw_step = 0.001
        if raw_step <= 0.0:
            raw_step = abs(raw_step) if raw_step != 0.0 else 0.001
        if raw_step == 0.0:
            raw_step = 0.001
        # Логический шаг всегда > 0
        self._step = raw_step
        for spinbox in (self.min_spinbox, self.value_spinbox, self.max_spinbox):
            spinbox.setSingleStep(self._step)
        try:
            self.step_spinbox.blockSignals(True)
            self.step_spinbox.setValue(self._step)
        finally:
            self.step_spinbox.blockSignals(False)
        self.stepChanged.emit(self._step)

    def stepSize(self) -> float:
        """Вернуть нормализованный шаг квантования/нуджа."""
        return float(self._step)

    @property
    def step(self) -> float:
        return float(self._step)

    @step.setter
    def step(self, value: float) -> None:
        self.setStepSize(value)

    @property
    def step_size(self) -> float:
        return float(self._step)

    @step_size.setter
    def step_size(self, value: float) -> None:
        self.setStepSize(value)

    def setTitle(self, title: str) -> None:
        """Изменить заголовок и обновить a11y-метаданные под новый label."""
        if self.title_label is not None:
            self.title_label.setText(title)
            self.title_label.setAccessibleName(self.tr("%1 title").replace("%1", title))
        else:
            self.title_label = QLabel(title)
        # Обновляем отображаемую метку для a11y и имена контролов
        self._display_label = title or self.tr("Range")
        self.setAccessibleName(
            self.tr("%1 range slider").replace("%1", self._display_label)
        )
        self.slider.setAccessibleName(
            self.tr("%1 slider track").replace("%1", self._display_label)
        )
        self.min_spinbox.setAccessibleName(
            self.tr("%1 minimum value").replace("%1", self._display_label)
        )
        self.value_spinbox.setAccessibleName(
            self.tr("%1 current value").replace("%1", self._display_label)
        )
        self.max_spinbox.setAccessibleName(
            self.tr("%1 maximum value").replace("%1", self._display_label)
        )
        self._refresh_accessibility_descriptions()

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================
    def setValue(self, value: float) -> None:
        value = float(value)
        value = max(self._minimum, min(self._maximum, value))
        # Если фактическое значение не изменилось, ограничимся синхронизацией
        # позиции слайдера и индикаторов без эмиссии сигналов.
        if math.isclose(value, self.value_spinbox.value(), rel_tol=1e-9, abs_tol=1e-9):
            self._update_slider_position(value)
            return

        self.value_spinbox.blockSignals(True)
        try:
            self.value_spinbox.setValue(value)
        finally:
            self.value_spinbox.blockSignals(False)
        self._update_slider_position(value)
        # Эмитим сигнал только при реальном изменении.
        self.valueChanged.emit(value)
        self._debounce_timer.start(self._debounce_delay)

    def value(self) -> float:
        return float(self.value_spinbox.value())

    def _emit_value_edited(self) -> None:
        """Сигнализировать о завершении редактирования со значением из спинбокса."""
        try:
            value = float(self.value_spinbox.value())
        except Exception:
            value = self.value()
        self.valueEdited.emit(value)

    def minimum(self) -> float:
        return float(self._minimum)

    def maximum(self) -> float:
        return float(self._maximum)

    def setEnabled(self, enabled: bool) -> None:  # noqa: D401 - Qt signature compatibility
        """Enable or disable the slider and its inputs."""

        super().setEnabled(enabled)
        spinboxes: SpinBoxTriple = (
            self.min_spinbox,
            self.value_spinbox,
            self.max_spinbox,
        )
        for widget in (self.slider, *spinboxes):
            widget.setEnabled(enabled)

    # =========================================================================
    # INTERNAL UPDATES
    # =========================================================================
    def _update_slider_position(self, value: float) -> None:
        """Обновить позицию внутреннего QSlider согласно значению."""
        try:
            if self._maximum == self._minimum:
                position = 0
            else:
                # Пересчёт из значения в позицию слайдера
                ratio = (float(value) - self._minimum) / (self._maximum - self._minimum)
                ratio = min(max(ratio, 0.0), 1.0)
                position = int(ratio * self._slider_resolution)

            self._updating_internally = True
            try:
                self.slider.setValue(position)
            finally:
                self._updating_internally = False
            # Обновляем текстовый индикатор позиции
            self._update_position_indicator(position)
        except Exception:
            # Defensive: не даём падать UI при граничных случаях
            pass

    def _update_range_indicator(self) -> None:
        width = self._maximum - self._minimum
        self.range_indicator_label.setText(
            f"Диапазон: {self._minimum:.{self._decimals}f} — {self._maximum:.{self._decimals}f} "
            f"ширина диапазона {width:.{self._decimals}f}" + (f" {self._units}" if self._units else "")
        )

    def _update_position_indicator(self, position: int) -> None:
        if self._slider_resolution == 0:
            percentage = 0.0
        else:
            percentage = position / self._slider_resolution * 100
        self.position_indicator_label.setText(
            f"Позиция: {percentage:.1f}% от диапазона"
        )
        self.position_indicator_label.setAccessibleDescription(
            self.tr("Current value positioned at %1 percent of the span.").replace(
                "%1", f"{percentage:.1f}"
            )
        )

    # =========================================================================
    # SIGNAL HANDLERS
    # =========================================================================
    @Slot()
    def _on_slider_pressed(self) -> None:
        self._debounce_timer.stop()

    @Slot()
    def _on_slider_released(self) -> None:
        self._debounce_timer.start(self._debounce_delay)

    @Slot(int)
    def _on_slider_value_changed(self, position: int) -> None:
        if self._updating_internally:
            return

        # Вычисляем значение из позиции слайдера
        if self._slider_resolution == 0:
            value = self._minimum
        else:
            span = self._maximum - self._minimum
            value = self._minimum + (span * position / self._slider_resolution)
        # Квантование по шагу (шаг всегда > 0)
        if self._step > 0.0:
            value = round(value / self._step) * self._step
        value = max(self._minimum, min(self._maximum, value))

        # Обновляем spinbox без рекурсивных сигналов
        self.value_spinbox.blockSignals(True)
        try:
            self.value_spinbox.setValue(value)
        finally:
            self.value_spinbox.blockSignals(False)

        self._update_position_indicator(position)
        self.valueChanged.emit(value)
        self._debounce_timer.start(self._debounce_delay)

    @Slot(float)
    def _on_value_spinbox_changed(self, value: float) -> None:
        # Синхронизация ползунка с вручную введённым значением
        self._update_slider_position(value)
        self.valueChanged.emit(float(value))
        self._debounce_timer.start(self._debounce_delay)

    @Slot()
    def _on_value_spinbox_finished(self) -> None:
        # Отложенная фиксация редактирования
        self._debounce_timer.start(self._debounce_delay)

    @Slot(float)
    def _on_min_spinbox_changed(self, value: float) -> None:
        # Предотвращаем инверсию диапазона
        if value >= self._maximum:
            value = (
                (self._maximum - abs(self._step))
                if self._step
                else (self._maximum - 0.001)
            )
            self.min_spinbox.blockSignals(True)
            try:
                self.min_spinbox.setValue(value)
            finally:
                self.min_spinbox.blockSignals(False)

        self._minimum = float(value)
        self._update_range_indicator()
        self._update_slider_position(self.value())
        self.rangeChanged.emit(self._minimum, self._maximum)

    @Slot(float)
    def _on_max_spinbox_changed(self, value: float) -> None:
        if value <= self._minimum:
            value = (
                (self._minimum + abs(self._step))
                if self._step
                else (self._minimum + 0.001)
            )
            self.max_spinbox.blockSignals(True)
            try:
                self.max_spinbox.setValue(value)
            finally:
                self.max_spinbox.blockSignals(False)

        self._maximum = float(value)
        self._update_range_indicator()
        self._update_slider_position(self.value())
        self.rangeChanged.emit(self._minimum, self._maximum)

    # =========================================================================
    # KEYBOARD HANDLING (fallback in addition to QShortcut)
    # =========================================================================
    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        """Обработка клавиатуры как резерв к QShortcut.

        Актуализировано: устраняем двойное срабатывание нуджа.
        Стрелки с Ctrl+Alt обрабатываются ТОЛЬКО через QShortcut. Здесь
        реализуем fallback ТОЛЬКО для фокуса по Ctrl+Alt+1..3 или если
        шорткаты по какой-то причине отключены.
        """
        if (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
            and event.modifiers() & Qt.KeyboardModifier.AltModifier
        ):
            key = event.key()
            # Fallback для стрелок только если шорткаты недоступны
            if key in (Qt.Key_Right, Qt.Key_Left):
                shortcuts_active = (
                    getattr(self, "_increase_shortcut", None) is not None
                    and self._increase_shortcut.isEnabled()
                    and getattr(self, "_decrease_shortcut", None) is not None
                    and self._decrease_shortcut.isEnabled()
                )
                if not shortcuts_active:
                    if key == Qt.Key_Right:
                        self._nudge_slider(self._step)
                        event.accept()
                        return
                    if key == Qt.Key_Left:
                        self._nudge_slider(-self._step)
                        event.accept()
                        return
                # В противном случае даём событию пройти к QShortcut
            if key == Qt.Key_1:
                self.min_spinbox.setFocus()
                event.accept()
                return
            if key == Qt.Key_2:
                self.value_spinbox.setFocus()
                event.accept()
                return
            if key == Qt.Key_3:
                self.max_spinbox.setFocus()
                event.accept()
                return
        super().keyPressEvent(event)
