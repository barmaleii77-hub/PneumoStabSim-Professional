"""Qt panel exposing stabiliser-specific pneumatic controls."""

from __future__ import annotations

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.common.settings_manager import get_settings_manager


class StabilizerPanel(QWidget):
    """Compact widget that surfaces stabiliser coupling controls."""

    couplingDiameterChanged = Signal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = get_settings_manager()
        self._spinbox = QDoubleSpinBox()
        self._setup_ui()
        self.refresh_from_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        group = QGroupBox(self.tr("Настройки стабилизатора"))
        form = QFormLayout(group)
        form.setContentsMargins(8, 8, 8, 8)
        form.setSpacing(6)

        self._spinbox.setRange(0.0, 0.02)
        self._spinbox.setDecimals(4)
        self._spinbox.setSingleStep(0.0001)
        self._spinbox.setSuffix(" м")
        self._spinbox.valueChanged.connect(self._on_spin_changed)

        help_label = QLabel(
            self.tr(
                "Диаметр регулируемого канала между диагоналями. "
                "Значение 0 отключает перетекание."
            )
        )
        help_label.setWordWrap(True)

        form.addRow(self.tr("Дроссель диагоналей"), self._spinbox)
        layout.addWidget(group)
        layout.addWidget(help_label)
        layout.addStretch(1)

    def refresh_from_settings(self) -> None:
        """Reload the spin box from the settings store."""

        value = 0.0
        try:
            stored = self._settings.get("current.pneumatic.diagonal_coupling_dia", 0.0)
            if isinstance(stored, (int, float)):
                value = float(stored)
        except Exception:  # pragma: no cover - defensive path
            value = 0.0
        self._spinbox.blockSignals(True)
        self._spinbox.setValue(value)
        self._spinbox.blockSignals(False)

    def get_parameters(self) -> dict[str, float]:
        """Return a snapshot of the stabiliser coupling configuration."""

        return {"diagonal_coupling_dia": float(self._spinbox.value())}

    def collect_state(self) -> dict[str, float]:
        """Alias for compatibility with other panels' state collectors."""

        return dict(self.get_parameters())

    @Slot(float)
    def _on_spin_changed(self, value: float) -> None:
        numeric = max(0.0, float(value))
        self._settings.set(
            "current.pneumatic.diagonal_coupling_dia", numeric, auto_save=False
        )
        self._settings.save()
        self.couplingDiameterChanged.emit(numeric)
