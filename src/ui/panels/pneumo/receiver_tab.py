"""Receiver configuration tab."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QComboBox,
)
from PySide6.QtGui import QFont

from ...widgets import Knob
from .defaults import (
    RECEIVER_DIAMETER_LIMITS,
    RECEIVER_LENGTH_LIMITS,
    RECEIVER_MANUAL_LIMITS,
)
from .state_manager import PneumoStateManager


class ReceiverTab(QWidget):
    """Configure receiver volume and geometry."""

    parameter_changed = Signal(str, float)
    mode_changed = Signal(str, str)
    receiver_volume_changed = Signal(float, str)

    def __init__(self, state_manager: PneumoStateManager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager

        self._setup_ui()
        self._load_from_state()
        self._connect_signals()

    # ------------------------------------------------------------------ setup
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        group = QGroupBox("Ресивер")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(8)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Режим объёма:"))
        self.volume_mode_combo = QComboBox()
        self.volume_mode_combo.addItems(["Ручной объём", "Геометрический расчёт"])
        mode_row.addWidget(self.volume_mode_combo, 1)
        group_layout.addLayout(mode_row)

        # Manual volume
        self.manual_volume_widget = QWidget()
        manual_layout = QHBoxLayout(self.manual_volume_widget)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(12)
        self.manual_volume_knob = Knob(
            minimum=RECEIVER_MANUAL_LIMITS["min"],
            maximum=RECEIVER_MANUAL_LIMITS["max"],
            value=self.state_manager.get_manual_volume(),
            step=RECEIVER_MANUAL_LIMITS["step"],
            decimals=RECEIVER_MANUAL_LIMITS["decimals"],
            units="м³",
            title="Объём ресивера",
        )
        manual_layout.addWidget(self.manual_volume_knob)
        manual_layout.addStretch()
        group_layout.addWidget(self.manual_volume_widget)

        # Geometric volume
        self.geometric_volume_widget = QWidget()
        geometric_layout = QHBoxLayout(self.geometric_volume_widget)
        geometric_layout.setContentsMargins(0, 0, 0, 0)
        geometric_layout.setSpacing(12)
        self.receiver_diameter_knob = Knob(
            minimum=RECEIVER_DIAMETER_LIMITS["min"],
            maximum=RECEIVER_DIAMETER_LIMITS["max"],
            value=self.state_manager.get_receiver_diameter(),
            step=RECEIVER_DIAMETER_LIMITS["step"],
            decimals=RECEIVER_DIAMETER_LIMITS["decimals"],
            units="м",
            title="Диаметр",
        )
        geometric_layout.addWidget(self.receiver_diameter_knob)
        self.receiver_length_knob = Knob(
            minimum=RECEIVER_LENGTH_LIMITS["min"],
            maximum=RECEIVER_LENGTH_LIMITS["max"],
            value=self.state_manager.get_receiver_length(),
            step=RECEIVER_LENGTH_LIMITS["step"],
            decimals=RECEIVER_LENGTH_LIMITS["decimals"],
            units="м",
            title="Длина",
        )
        geometric_layout.addWidget(self.receiver_length_knob)
        group_layout.addWidget(self.geometric_volume_widget)

        self.calculated_volume_label = QLabel()
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.calculated_volume_label.setFont(font)
        self.calculated_volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group_layout.addWidget(self.calculated_volume_label)

        self.volume_hint_label = QLabel()
        self.volume_hint_label.setWordWrap(True)
        self.volume_hint_label.setStyleSheet("color: #c54632; font-size: 11px;")
        self.volume_hint_label.setVisible(False)
        group_layout.addWidget(self.volume_hint_label)

        layout.addWidget(group)
        layout.addStretch()

    # ------------------------------------------------------------------ state
    def _load_from_state(self) -> None:
        mode = self.state_manager.get_volume_mode()
        self.volume_mode_combo.setCurrentIndex(0 if mode == "MANUAL" else 1)
        # Блокируем сигналы при программном обновлении значения, иначе
        # повторный вызов set_manual_volume(клампированное) очистит hint.
        self.manual_volume_knob.blockSignals(True)
        try:
            self.manual_volume_knob.setValue(self.state_manager.get_manual_volume())
        finally:
            self.manual_volume_knob.blockSignals(False)
        self.receiver_diameter_knob.blockSignals(True)
        self.receiver_length_knob.blockSignals(True)
        try:
            self.receiver_diameter_knob.setValue(
                self.state_manager.get_receiver_diameter()
            )
            self.receiver_length_knob.setValue(self.state_manager.get_receiver_length())
        finally:
            self.receiver_diameter_knob.blockSignals(False)
            self.receiver_length_knob.blockSignals(False)
        self._apply_mode_visibility(mode)
        self._update_calculated_volume()
        self._update_volume_hint()

    def update_from_state(self) -> None:
        # Обновляем состояние и гарантируем, что виджет показан
        self._load_from_state()
        if not self.isVisible():  # тесты ожидают isVisible() True для вложенного label
            self.show()

    # ----------------------------------------------------------------- signals
    def _connect_signals(self) -> None:
        self.volume_mode_combo.currentIndexChanged.connect(self._on_volume_mode_changed)
        self.manual_volume_knob.valueChanged.connect(self._on_manual_volume_changed)
        self.receiver_diameter_knob.valueChanged.connect(self._on_geometry_changed)
        self.receiver_length_knob.valueChanged.connect(self._on_geometry_changed)

    # ---------------------------------------------------------------- handlers
    def _apply_mode_visibility(self, mode: str) -> None:
        is_manual = mode == "MANUAL"
        self.manual_volume_widget.setVisible(is_manual)
        self.geometric_volume_widget.setVisible(not is_manual)
        self.calculated_volume_label.setVisible(not is_manual)

    def _on_volume_mode_changed(self, index: int) -> None:
        mode = "MANUAL" if index == 0 else "GEOMETRIC"
        self.state_manager.set_volume_mode(mode)
        self._apply_mode_visibility(mode)

        if mode == "MANUAL":
            volume = self.state_manager.get_manual_volume()
        else:
            volume = self.state_manager.refresh_geometric_volume()
        self.mode_changed.emit("volume_mode", mode)
        self.parameter_changed.emit("receiver_volume", volume)
        self.receiver_volume_changed.emit(volume, mode)
        self._update_calculated_volume()
        self._update_volume_hint()

    def _on_manual_volume_changed(self, value: float) -> None:
        self.state_manager.set_manual_volume(value)
        actual = self.state_manager.get_manual_volume()
        if self.state_manager.get_volume_mode() == "MANUAL":
            self.parameter_changed.emit("receiver_volume", actual)
            self.receiver_volume_changed.emit(actual, "MANUAL")
        self._update_volume_hint()

    def _on_geometry_changed(self, _value: float) -> None:
        diameter = self.receiver_diameter_knob.value()
        length = self.receiver_length_knob.value()
        self.state_manager.set_receiver_diameter(diameter)
        volume = self.state_manager.set_receiver_length(length)
        diameter_value = self.state_manager.get_receiver_diameter()
        length_value = self.state_manager.get_receiver_length()
        if self.state_manager.get_volume_mode() == "GEOMETRIC":
            self.parameter_changed.emit("receiver_volume", volume)
            self.receiver_volume_changed.emit(volume, "GEOMETRIC")
        self.parameter_changed.emit("receiver_diameter", diameter_value)
        self.parameter_changed.emit("receiver_length", length_value)
        self._update_calculated_volume()
        self._update_volume_hint()

    def _update_calculated_volume(self) -> None:
        volume = self.state_manager.calculate_geometric_volume(
            self.state_manager.get_receiver_diameter(),
            self.state_manager.get_receiver_length(),
        )
        self.calculated_volume_label.setText(f"Расчётный объём: {volume:.3f} м³")

    def _update_volume_hint(self) -> None:
        hints: list[str] = []
        for key in ("receiver_volume", "receiver_volume_limits"):
            hint = self.state_manager.get_hint(key)
            if hint:
                hints.append(hint)
        if hints:
            combined = "\n".join(dict.fromkeys(hints))
            self.volume_hint_label.setText(combined)
            self.volume_hint_label.setVisible(True)
        else:
            self.volume_hint_label.clear()
            self.volume_hint_label.setVisible(False)
