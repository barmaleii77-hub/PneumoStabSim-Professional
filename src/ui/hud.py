"""
HUD components for pressure visualization
Includes pressure scale widget and tank overlay
"""

import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, Signal, Slot
from PySide6.QtGui import (
    QPainter,
    QLinearGradient,
    QColor,
    QPen,
    QBrush,
    QFont,
)

# ИСПРАВЛЕНО: Изменен относительный импорт на абсолютный
try:
    from src.runtime.state import StateSnapshot
except ImportError:
    # Fallback for different import contexts
    try:
        from runtime.state import StateSnapshot
    except ImportError:
        # Create a mock StateSnapshot for standalone testing
        class StateSnapshot:
            def __init__(self):
                self.tank = type(
                    "Tank",
                    (),
                    {
                        "pressure": 101325.0,
                        "relief_min_open": False,
                        "relief_stiff_open": False,
                        "relief_safety_open": False,
                    },
                )()

            def get_pressure_array(self):
                return np.array([101325.0, 101325.0, 101325.0, 101325.0])


class PressureScaleWidget(QWidget):
    """Vertical pressure scale with gradient and markers"""

    # Signals
    range_changed = Signal(float, float)  # min_pressure, max_pressure

    def __init__(self, parent=None):
        super().__init__(parent)

        # Pressure range (Pa)
        self.p_min = 0.0  # Minimum pressure on scale
        self.p_max = 1000000.0  # Maximum pressure (10 bar default)

        # Reference pressures (Pa)
        self.p_atm = 101325.0  # Atmospheric
        self.p_min_relief = 250000.0  # Min relief valve
        self.p_stiff = 1500000.0  # Stiffness relief
        self.p_safety = 5000000.0  # Safety relief

        # Current tank pressure
        self.p_tank = 101325.0

        # Line pressures
        self.p_lines = [101325.0] * 4  # A1, B1, A2, B2

        # Valve states
        self.valve_states = {"min": False, "stiff": False, "safety": False}

        # Overdrive values (for mini-bars)
        self.overdrive_values = {"min": 0.0, "stiff": 0.0, "safety": 0.0}

        # Visual parameters
        self.setMinimumWidth(80)
        self.setMaximumWidth(120)

        # Gradient stops (pressure ? color)
        self.gradient_stops = [
            (0.0, QColor(0, 0, 180)),  # Dark blue (low)
            (0.25, QColor(0, 120, 255)),  # Blue
            (0.5, QColor(0, 255, 0)),  # Green (mid)
            (0.75, QColor(255, 200, 0)),  # Orange
            (1.0, QColor(255, 0, 0)),  # Red (high)
        ]

    def set_range(self, p_min: float, p_max: float) -> None:
        """Set pressure range for scale

        Args:
            p_min: Minimum pressure (Pa)
            p_max: Maximum pressure (Pa)
        """
        # Validate range
        if p_max <= p_min:
            return

        # Safety limits
        p_min = max(p_min, -self.p_atm)  # No lower than absolute vacuum
        p_max = max(p_max, 1.2 * self.p_safety)  # At least 20% above safety

        self.p_min = p_min
        self.p_max = p_max

        self.range_changed.emit(p_min, p_max)
        self.update()

    def set_markers(
        self, p_atm: float, p_min: float, p_stiff: float, p_safety: float
    ) -> None:
        """Set reference pressure markers

        Args:
            p_atm: Atmospheric pressure
            p_min: Minimum relief pressure
            p_stiff: Stiffness relief pressure
            p_safety: Safety relief pressure
        """
        self.p_atm = p_atm
        self.p_min_relief = p_min
        self.p_stiff = p_stiff
        self.p_safety = p_safety
        self.update()

    @Slot(object)
    def update_from_snapshot(self, snapshot: "StateSnapshot") -> None:
        """Update from simulation snapshot

        Args:
            snapshot: Current state
        """
        if not snapshot:
            return

        # Update tank pressure
        self.p_tank = snapshot.tank.pressure

        # Update line pressures
        pressures = snapshot.get_pressure_array()
        self.p_lines = pressures.tolist()

        # Update valve states
        self.valve_states = {
            "min": snapshot.tank.relief_min_open,
            "stiff": snapshot.tank.relief_stiff_open,
            "safety": snapshot.tank.relief_safety_open,
        }

        # Calculate overdrive values (how much above setpoint)
        self.overdrive_values = {
            "min": max(0, self.p_tank - self.p_min_relief),
            "stiff": max(0, self.p_tank - self.p_stiff),
            "safety": max(0, self.p_tank - self.p_safety),
        }

        self.update()

    def map_pressure_to_height(self, pressure: float) -> float:
        """Map pressure to Y coordinate on scale

        Args:
            pressure: Pressure value (Pa)

        Returns:
            Y coordinate (0 = top, height = bottom)
        """
        if self.p_max <= self.p_min:
            return self.height() / 2

        # Normalize to [0, 1]
        norm = (pressure - self.p_min) / (self.p_max - self.p_min)
        norm = np.clip(norm, 0.0, 1.0)

        # Invert (0 = bottom, 1 = top) and map to widget height
        margin = 40  # Top/bottom margins
        scale_height = self.height() - 2 * margin

        y = margin + scale_height * (1.0 - norm)
        return y

    def paintEvent(self, event) -> None:  # type: ignore[override]
        """Paint the pressure scale"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        height = self.height()

        # Margins
        margin = 40
        scale_x = 20
        scale_width = 30
        scale_height = height - 2 * margin

        # Create gradient
        gradient = QLinearGradient(scale_x, margin + scale_height, scale_x, margin)
        for pos, color in self.gradient_stops:
            gradient.setColorAt(pos, color)

        # Draw gradient bar
        painter.fillRect(scale_x, margin, scale_width, scale_height, QBrush(gradient))

        # Draw scale border
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.drawRect(scale_x, margin, scale_width, scale_height)

        # Draw tick marks and labels
        painter.setFont(QFont("Arial", 8))

        # Major ticks (every 1 bar = 100kPa)
        tick_interval = 100000.0  # 1 bar
        p = self.p_min
        while p <= self.p_max:
            y = self.map_pressure_to_height(p)

            # Tick mark
            painter.setPen(QPen(Qt.GlobalColor.white, 1))
            painter.drawLine(
                scale_x + scale_width, int(y), scale_x + scale_width + 5, int(y)
            )

            # Label (in bar)
            label = f"{p / 100000:.1f}"
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(scale_x + scale_width + 8, int(y) + 4, label)

            p += tick_interval

        # Draw reference markers
        self._draw_marker(
            painter, self.p_atm, "Patm", QColor(150, 150, 150), scale_x, scale_width
        )
        self._draw_marker(
            painter,
            self.p_min_relief,
            "Min",
            QColor(100, 200, 100),
            scale_x,
            scale_width,
        )
        self._draw_marker(
            painter, self.p_stiff, "Stiff", QColor(255, 200, 0), scale_x, scale_width
        )
        self._draw_marker(
            painter, self.p_safety, "Safe", QColor(255, 100, 100), scale_x, scale_width
        )

        # Draw tank pressure indicator
        y_tank = self.map_pressure_to_height(self.p_tank)
        painter.setPen(QPen(QColor(255, 255, 0), 3))
        painter.drawLine(
            scale_x - 5, int(y_tank), scale_x + scale_width + 5, int(y_tank)
        )

        # Draw title
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(5, 20, "Pressure")
        painter.drawText(10, 35, "(bar)")

    def _draw_marker(
        self,
        painter: QPainter,
        pressure: float,
        label: str,
        color: QColor,
        x: int,
        width: int,
    ) -> None:
        """Draw a reference pressure marker

        Args:
            painter: QPainter instance
            pressure: Pressure value
            label: Marker label
            color: Marker color
            x: Scale X position
            width: Scale width
        """
        y = self.map_pressure_to_height(pressure)

        # Draw line
        painter.setPen(QPen(color, 2, Qt.PenStyle.DashLine))
        painter.drawLine(x, int(y), x + width, int(y))

        # Draw label background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        painter.drawRect(x - 5, int(y) - 10, 30, 14)

        # Draw label text
        painter.setPen(color)
        painter.setFont(QFont("Arial", 7))
        painter.drawText(x - 3, int(y), label)


class TankOverlayHUD:
    """HUD overlay for tank visualization in OpenGL"""

    def __init__(self) -> None:
        """Initialize tank HUD"""
        # Tank parameters (in screen coordinates)
        self.x = 0
        self.y = 0
        self.width = 60
        self.height = 300

        # Pressure range
        self.p_min = 0.0
        self.p_max = 1000000.0

        # Current state
        self.p_tank = 101325.0
        self.p_lines = [101325.0] * 4

        # Valve positions and states
        self.valve_markers = {
            "min": (0, False, 0.0),  # (y_pos, is_open, overdrive)
            "stiff": (0, False, 0.0),
            "safety": (0, False, 0.0),
        }

    def set_position(self, x: int, y: int) -> None:
        """Set HUD position on screen

        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.x = x
        self.y = y

    def update_from_snapshot(self, snapshot: "StateSnapshot") -> None:
        """Update from simulation snapshot

        Args:
            snapshot: Current state
        """
        if not snapshot:
            return

        self.p_tank = snapshot.tank.pressure
        self.p_lines = snapshot.get_pressure_array().tolist()

        # Update valve markers (calculate Y positions)
        # This will be implemented in render method

    def map_pressure_to_height(self, pressure: float) -> float:
        """Map pressure to height within tank

        Args:
            pressure: Pressure value (Pa)

        Returns:
            Height from bottom of tank
        """
        if self.p_max <= self.p_min:
            return self.height / 2

        norm = (pressure - self.p_min) / (self.p_max - self.p_min)
        norm = np.clip(norm, 0.0, 1.0)

        return norm * self.height

    def render(self, painter: QPainter, screen_width: int, screen_height: int) -> None:
        """Render tank HUD using QPainter

        Args:
            painter: QPainter instance
            screen_width: Screen width
            screen_height: Screen height
        """
        # Position tank at right side
        x = screen_width - self.width - 150
        y = (screen_height - self.height) // 2

        # Draw tank outline (glass cylinder)
        painter.setPen(QPen(QColor(200, 200, 255, 200), 2))
        painter.setBrush(QBrush(QColor(180, 180, 255, 50)))
        painter.drawRect(x, y, self.width, self.height)

        # Draw fill level
        fill_height = self.map_pressure_to_height(self.p_tank)
        fill_y = y + self.height - fill_height

        # Gradient fill
        gradient = QLinearGradient(x, y + self.height, x, y)
        gradient.setColorAt(0.0, QColor(0, 100, 255, 150))
        gradient.setColorAt(0.5, QColor(0, 200, 255, 120))
        gradient.setColorAt(1.0, QColor(100, 255, 255, 100))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(x + 2, int(fill_y), self.width - 4, int(fill_height))

        # Draw pressure spheres (4 lines)
        sphere_radius = 8
        for i, p_line in enumerate(self.p_lines):
            sphere_y = y + self.height - self.map_pressure_to_height(p_line)
            sphere_x = x + self.width // 2

            # Color based on pressure
            color = self._pressure_to_color(p_line)
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(
                QPointF(sphere_x, sphere_y), sphere_radius, sphere_radius
            )

        # Draw tank pressure label
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(QFont("Arial", 10))
        p_bar = self.p_tank / 100000.0
        painter.drawText(x - 50, y - 10, f"Tank: {p_bar:.2f} bar")

    def _pressure_to_color(self, pressure: float) -> QColor:
        """Convert pressure to gradient color

        Args:
            pressure: Pressure value (Pa)

        Returns:
            QColor
        """
        # Normalize pressure
        if self.p_max <= self.p_min:
            return QColor(128, 128, 128)

        norm = (pressure - self.p_min) / (self.p_max - self.p_min)
        norm = np.clip(norm, 0.0, 1.0)

        # Simple gradient: blue ? green ? red
        if norm < 0.5:
            # Blue to green
            t = norm * 2
            r = int(0 * (1 - t) + 0 * t)
            g = int(0 * (1 - t) + 255 * t)
            b = int(255 * (1 - t) + 0 * t)
        else:
            # Green to red
            t = (norm - 0.5) * 2
            r = int(0 * (1 - t) + 255 * t)
            g = int(255 * (1 - t) + 0 * t)
            b = int(0 * (1 - t) + 0 * t)

        return QColor(r, g, b, 200)
