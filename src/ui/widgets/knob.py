"""
Universal knob widget for PySide6
Combines QDial with QDoubleSpinBox for precise value control
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDial,
    QDoubleSpinBox,
    QSizePolicy,
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont, QKeySequence, QShortcut


@dataclass(slots=True)
class AccessibilityShortcut:
    """Metadata describing an announced shortcut for assistive tech."""

    identifier: str
    sequence: str
    description: str


class _UnitsLabel(QLabel):
    """Lazily created label that tracks the requested visibility state."""

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self._requested_visible = True

    def set_units_visibility(self, visible: bool) -> None:
        self._requested_visible = bool(visible)
        super().setVisible(bool(visible))

    def setVisible(self, visible: bool) -> None:  # type: ignore[override]
        super().setVisible(bool(visible))

    def isVisible(self) -> bool:  # type: ignore[override]
        return self._requested_visible


class Knob(QWidget):
    """Universal rotary knob with value display and units

    Combines QDial for intuitive rotation with QDoubleSpinBox for precise input.
    Supports arbitrary float ranges with automatic scaling.
    """

    # Signals
    valueChanged = Signal(float)  # Emitted when value changes

    def __init__(
        self,
        minimum: float = 0.0,
        maximum: float = 100.0,
        value: float = 0.0,
        step: float = 1.0,
        decimals: int = 2,
        units: str = "",
        title: str = "",
        parent=None,
        accessible_name: str | None = None,
        accessible_role: str | None = None,
        increase_shortcut: str = "Ctrl+Alt+Up",
        decrease_shortcut: str = "Ctrl+Alt+Down",
        reset_shortcut: str = "Ctrl+Alt+0",
    ):
        """Initialize knob widget

        Args:
            minimum: Minimum value
            maximum: Maximum value
            value: Initial value
            step: Step size for adjustments
            decimals: Number of decimal places to display
            units: Units string (e.g., "bar", "mm", "deg")
            title: Title label above knob
            parent: Parent widget
        """
        super().__init__(parent)

        # Parameters
        self._minimum = minimum
        self._maximum = maximum
        self._step = step
        self._decimals = decimals
        self._units = units
        self._dial_resolution = 1000  # Internal dial resolution
        self._accessible_role = accessible_role or "dial"
        self._shortcut_metadata: list[AccessibilityShortcut] = []

        # Create UI
        self._setup_ui(title)

        # Accessibility configuration
        self._accessible_label = accessible_name or ""
        self._configure_accessibility(title)
        self._setup_shortcuts(increase_shortcut, decrease_shortcut, reset_shortcut)
        self._refresh_accessible_descriptions()

        # Set initial value
        self.setValue(value)

        # Connect signals
        self._connect_signals()

        # Size policy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def _setup_ui(self, title: str):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(4, 4, 4, 4)

        # Title label
        if title:
            self.title_label = QLabel(title)
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            self.title_label.setFont(font)
            layout.addWidget(self.title_label)
            self.title_label.setAccessibleName(self.tr("%1 title").replace("%1", title))

        # Dial widget
        self.dial = QDial()
        self.dial.setMinimum(0)
        self.dial.setMaximum(self._dial_resolution)
        self.dial.setNotchesVisible(True)
        self.dial.setWrapping(False)
        self.dial.setMinimumSize(80, 80)
        self.dial.setMaximumSize(120, 120)
        layout.addWidget(self.dial)

        # Value display and input
        self._value_layout = QHBoxLayout()
        self._value_layout.setSpacing(2)

        self.spinbox = QDoubleSpinBox()
        self.spinbox.setMinimum(self._minimum)
        self.spinbox.setMaximum(self._maximum)
        self.spinbox.setSingleStep(self._step)
        self.spinbox.setDecimals(self._decimals)
        self.spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinbox.setMaximumWidth(80)

        self._value_layout.addWidget(self.spinbox)

        # Units label (created lazily if units are provided)
        if self._units:
            self._create_or_update_units_label(self._units)

        layout.addLayout(self._value_layout)

    def _configure_accessibility(self, title: str) -> None:
        """Assign accessible metadata for screen readers."""

        display_label = title or self.tr("Value")
        self._display_label = display_label
        if not self._accessible_label:
            self._accessible_label = self.tr("%1 control").replace("%1", display_label)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(self._accessible_label)
        self.setProperty("accessibilityRole", self._accessible_role)
        self._refresh_accessible_descriptions(display_label)

        self.dial.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.dial.setAccessibleName(self.tr("%1 dial").replace("%1", display_label))
        self.dial.setAccessibleDescription(
            self.tr(
                "Rotate to change %1 using the keyboard shortcuts or mouse."
            ).replace("%1", display_label)
        )
        self.dial.setProperty("accessibilityRole", "dial")

        self.spinbox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.spinbox.setAccessibleName(
            self.tr("%1 numeric entry").replace("%1", display_label)
        )
        self.spinbox.setProperty("accessibilityRole", "spinbox")

    def _refresh_accessible_descriptions(
        self, display_label: str | None = None
    ) -> None:
        """Refresh descriptions when range or units change."""

        if display_label is None:
            display_label = getattr(self, "_display_label", None) or self.tr("Value")

        if self._units:
            units_fragment = self.tr("%1.").replace("%1", self._units)
            description = (
                self.tr("Adjust %1 between %2 and %3 %4")
                .replace("%1", display_label)
                .replace("%2", f"{self._minimum:.{self._decimals}f}")
                .replace("%3", f"{self._maximum:.{self._decimals}f}")
                .replace("%4", units_fragment)
            )
        else:
            description = (
                self.tr("Adjust %1 between %2 and %3.")
                .replace("%1", display_label)
                .replace("%2", f"{self._minimum:.{self._decimals}f}")
                .replace("%3", f"{self._maximum:.{self._decimals}f}")
            )

        shortcut_hint = self._compose_shortcut_summary()
        if shortcut_hint:
            description = f"{description} {shortcut_hint}"

        self.setAccessibleDescription(description)
        self.spinbox.setAccessibleDescription(description)

        if hasattr(self, "units_label") and self._units:
            self.units_label.setAccessibleName(
                self.tr("%1 units").replace("%1", display_label)
            )
            self.units_label.setAccessibleDescription(
                self.tr("Displays the measurement units for %1.").replace(
                    "%1", display_label
                )
            )

    def _setup_shortcuts(
        self, increase_shortcut: str, decrease_shortcut: str, reset_shortcut: str
    ) -> None:
        """Provide keyboard shortcuts for screen reader friendly control."""

        self._shortcut_metadata.clear()

        self._increase_shortcut = self._register_shortcut(
            "increase",
            increase_shortcut,
            lambda: self._nudge_value(self._step),
            self.tr("Increase %1 by one step (%2)."),
            {
                "%1": self.accessibleName(),
                "%2": increase_shortcut,
            },
        )

        self._decrease_shortcut = self._register_shortcut(
            "decrease",
            decrease_shortcut,
            lambda: self._nudge_value(-self._step),
            self.tr("Decrease %1 by one step (%2)."),
            {
                "%1": self.accessibleName(),
                "%2": decrease_shortcut,
            },
        )

        self._reset_shortcut = self._register_shortcut(
            "reset",
            reset_shortcut,
            self._reset_to_default,
            self.tr("Reset %1 to its default value (%2)."),
            {
                "%1": self.accessibleName(),
                "%2": reset_shortcut,
            },
        )

    def _register_shortcut(
        self,
        identifier: str,
        sequence_str: str,
        callback,
        description_template: str,
        replacements: dict[str, str] | None = None,
    ) -> QShortcut:
        """Create and register a shortcut with accessibility metadata."""

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
        """Summarise the registered shortcuts for accessible descriptions."""

        if not self._shortcut_metadata:
            return ""

        joined = " ".join(shortcut.description for shortcut in self._shortcut_metadata)
        return self.tr("Keyboard shortcuts: %1").replace("%1", joined)

    def accessibilityRole(self) -> str:
        """Expose the semantic role expected by accessibility tooling."""

        return self._accessible_role

    def accessibilityShortcuts(self) -> list[AccessibilityShortcut]:
        """Return the shortcuts that should be announced to automation."""

        return list(self._shortcut_metadata)

    def _nudge_value(self, delta: float) -> None:
        """Increment or decrement the knob by *delta*."""

        new_value = self.value() + delta
        self.setValue(new_value)
        self.valueChanged.emit(self.value())

    def _reset_to_default(self) -> None:
        """Reset the control to the midpoint of its range."""

        midpoint = self._minimum + (self._maximum - self._minimum) / 2.0
        self.setValue(midpoint)
        self.valueChanged.emit(self.value())

    def _connect_signals(self):
        """Connect internal signals"""
        self.dial.valueChanged.connect(self._on_dial_changed)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)

    def _value_to_dial(self, value: float) -> int:
        """Convert real value to dial position"""
        if self._maximum <= self._minimum:
            return 0

        # Clamp value
        value = max(self._minimum, min(self._maximum, value))

        # Scale to dial range
        ratio = (value - self._minimum) / (self._maximum - self._minimum)
        return int(ratio * self._dial_resolution)

    def _dial_to_value(self, dial_pos: int) -> float:
        """Convert dial position to real value"""
        # Scale from dial range
        ratio = dial_pos / self._dial_resolution
        value = self._minimum + ratio * (self._maximum - self._minimum)

        # Round to step if specified
        if self._step > 0:
            steps = round((value - self._minimum) / self._step)
            value = self._minimum + steps * self._step

        return max(self._minimum, min(self._maximum, value))

    @Slot(int)
    def _on_dial_changed(self, dial_value: int):
        """Handle dial value change"""
        real_value = self._dial_to_value(dial_value)

        # Update spinbox without triggering its signal
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(real_value)
        self.spinbox.blockSignals(False)

        # Emit our signal
        self.valueChanged.emit(real_value)

    @Slot(float)
    def _on_spinbox_changed(self, spinbox_value: float):
        """Handle spinbox value change"""
        # Update dial without triggering its signal
        dial_pos = self._value_to_dial(spinbox_value)
        self.dial.blockSignals(True)
        self.dial.setValue(dial_pos)
        self.dial.blockSignals(False)

        # Emit our signal
        self.valueChanged.emit(spinbox_value)

    def setValue(self, value: float):
        """Set knob value

        Args:
            value: New value
        """
        value = max(self._minimum, min(self._maximum, value))

        # Update both widgets
        dial_pos = self._value_to_dial(value)

        self.dial.blockSignals(True)
        self.spinbox.blockSignals(True)

        self.dial.setValue(dial_pos)
        self.spinbox.setValue(value)

        self.dial.blockSignals(False)
        self.spinbox.blockSignals(False)

    def value(self) -> float:
        """Get current value

        Returns:
            Current value
        """
        return self.spinbox.value()

    def setRange(self, minimum: float, maximum: float, step: float = None):
        """Set value range

        Args:
            minimum: New minimum value
            maximum: New maximum value
            step: New step size (optional)
        """
        if maximum <= minimum:
            raise ValueError("Maximum must be greater than minimum")

        current_value = self.value()

        self._minimum = minimum
        self._maximum = maximum

        if step is not None:
            self._step = step

        # Update spinbox range
        self.spinbox.setMinimum(minimum)
        self.spinbox.setMaximum(maximum)
        if step is not None:
            self.spinbox.setSingleStep(step)

        # Restore value (clamped to new range)
        self.setValue(current_value)
        self._refresh_accessible_descriptions()

    def setDecimals(self, decimals: int):
        """Set number of decimal places

        Args:
            decimals: Number of decimal places
        """
        self._decimals = decimals
        self.spinbox.setDecimals(decimals)

    def _create_or_update_units_label(self, units: str) -> None:
        """Ensure the units label exists and reflects *units*."""

        if hasattr(self, "units_label"):
            self.units_label.setText(units)
            if isinstance(self.units_label, _UnitsLabel):
                self.units_label.set_units_visibility(bool(units))
            else:
                self.units_label.setVisible(bool(units))
            return

        if not units:
            return

        font = QFont()
        font.setPointSize(8)

        self.units_label = _UnitsLabel(units)
        self.units_label.setFont(font)
        self.units_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.units_label.set_units_visibility(True)
        self._value_layout.addWidget(self.units_label)

    def setUnits(self, units: str):
        """Set units label text and visibility."""

        units = units or ""
        self._units = units
        self._create_or_update_units_label(units)
        self._refresh_accessible_descriptions()

    def setEnabled(self, enabled: bool):
        """Enable/disable the knob

        Args:
            enabled: True to enable, False to disable
        """
        super().setEnabled(enabled)
        self.dial.setEnabled(enabled)
        self.spinbox.setEnabled(enabled)

    def minimum(self) -> float:
        """Get minimum value"""
        return self._minimum

    def maximum(self) -> float:
        """Get maximum value"""
        return self._maximum

    def step(self) -> float:
        """Get step size"""
        return self._step
