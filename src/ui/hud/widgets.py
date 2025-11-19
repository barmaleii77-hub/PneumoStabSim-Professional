"""
HUD components for pressure visualization and camera diagnostics.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Callable, Mapping

import numpy as np

from .telemetry import CameraHudTelemetry as _CameraHudTelemetry, _coerce_float

CameraHudTelemetry = _CameraHudTelemetry

try:  # pragma: no cover - fallback for headless test environments
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
except Exception:  # pragma: no cover - PySide6 missing or fails to initialise


def _install_qt_fallbacks() -> None:  # pragma: no cover - PySide6 missing/headless
    class _QtFallback:
        AlignLeft = 0

    class _SignalFallback:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self._handlers: list[Callable[..., None]] = []

        def connect(self, handler: Callable[..., None]) -> None:
            self._handlers.append(handler)

        def disconnect(self, handler: Callable[..., None]) -> None:
            try:
                self._handlers.remove(handler)
            except ValueError:
                return None

        def emit(self, *args: object, **kwargs: object) -> None:
            for callback in list(self._handlers):
                callback(*args, **kwargs)

    def _slot_fallback(*_args: object, **_kwargs: object):  # type: ignore[override]
        def decorator(func):
            return func

        return decorator

    class _QWidgetFallback:  # noqa: D401 - simple shim
        pass

    global \
        QWidget, \
        Qt, \
        QPointF, \
        Signal, \
        Slot, \
        QPainter, \
        QLinearGradient, \
        QColor, \
        QPen, \
        QBrush, \
        QFont

    QWidget = _QWidgetFallback  # type: ignore[assignment]
    Qt = _QtFallback()  # type: ignore[assignment]
    QPointF = object  # type: ignore[assignment]
    Signal = _SignalFallback  # type: ignore[assignment]
    Slot = _slot_fallback  # type: ignore[assignment]
    QPainter = QLinearGradient = QColor = QPen = QBrush = QFont = object  # type: ignore[assignment]


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

        # Relief valve flow telemetry
        self.relief_flows = {"min": 0.0, "stiff": 0.0, "safety": 0.0}
        self.relief_flow_peaks = {"min": 1.0, "stiff": 1.0, "safety": 1.0}

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
    def update_from_snapshot(self, snapshot: StateSnapshot) -> None:
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

        relief_samples = {
            "min": float(getattr(snapshot.tank, "flow_min", 0.0)),
            "stiff": float(getattr(snapshot.tank, "flow_stiff", 0.0)),
            "safety": float(getattr(snapshot.tank, "flow_safety", 0.0)),
        }
        for key, value in relief_samples.items():
            magnitude = abs(float(value))
            self.relief_flows[key] = float(value)
            peak = max(self.relief_flow_peaks.get(key, 1.0), magnitude, 1e-6)
            self.relief_flow_peaks[key] = peak

        # Calculate overdrive values (how much above setpoint)
        self.overdrive_values = {
            "min": max(0, self.p_tank - self.p_min_relief),
            "stiff": max(0, self.p_tank - self.p_stiff),
            "safety": max(0, self.p_tank - self.p_safety),
        }

        self.update()

    def apply_flow_payload(self, payload: Mapping[str, Any] | None) -> None:
        """Update widget state from a SceneBridge flow payload."""

        if not isinstance(payload, Mapping):
            return

        tank_payload = payload.get("tank")
        if isinstance(tank_payload, Mapping):
            self.p_tank = _coerce_float(tank_payload.get("pressure"), self.p_tank)
            valve_map = tank_payload.get("valves")
            if isinstance(valve_map, Mapping):
                self.valve_states = {
                    "min": bool(
                        valve_map.get("min", self.valve_states.get("min", False))
                    ),
                    "stiff": bool(
                        valve_map.get("stiff", self.valve_states.get("stiff", False))
                    ),
                    "safety": bool(
                        valve_map.get("safety", self.valve_states.get("safety", False))
                    ),
                }

        relief_payload = payload.get("relief")
        if isinstance(relief_payload, Mapping):
            for key in ("min", "stiff", "safety"):
                entry = relief_payload.get(key)
                if not isinstance(entry, Mapping):
                    continue
                flow_value = _coerce_float(
                    entry.get("flow"), self.relief_flows.get(key, 0.0)
                )
                self.relief_flows[key] = flow_value
                magnitude = abs(flow_value)
                peak = max(self.relief_flow_peaks.get(key, 1.0), magnitude, 1e-6)
                self.relief_flow_peaks[key] = peak
                if "open" in entry:
                    self.valve_states[key] = bool(entry.get("open"))

        line_section = payload.get("lines")
        if isinstance(line_section, Mapping):
            pressures: list[float] = []
            for key in ("a1", "b1", "a2", "b2"):
                entry = line_section.get(key)
                if isinstance(entry, Mapping):
                    pressures.append(_coerce_float(entry.get("pressure"), 0.0))
            if pressures:
                while len(pressures) < 4:
                    pressures.append(pressures[-1])
                self.p_lines = pressures[:4]

        self.overdrive_values = {
            "min": max(0.0, self.p_tank - self.p_min_relief),
            "stiff": max(0.0, self.p_tank - self.p_stiff),
            "safety": max(0.0, self.p_tank - self.p_safety),
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
        """Paint the pressure scale with valve overlays."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        height = self.height()

        margin = 40
        scale_x = 20
        scale_width = 30
        scale_height = height - 2 * margin

        gradient = QLinearGradient(scale_x, margin + scale_height, scale_x, margin)
        for pos, color in self.gradient_stops:
            gradient.setColorAt(pos, color)

        painter.fillRect(scale_x, margin, scale_width, scale_height, QBrush(gradient))

        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.drawRect(scale_x, margin, scale_width, scale_height)

        painter.setFont(QFont("Arial", 8))

        tick_interval = 100000.0
        p = self.p_min
        while p <= self.p_max:
            y = self.map_pressure_to_height(p)
            painter.setPen(QPen(Qt.GlobalColor.white, 1))
            painter.drawLine(
                scale_x + scale_width, int(y), scale_x + scale_width + 5, int(y)
            )
            label = f"{p / 100000:.1f}"
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(scale_x + scale_width + 8, int(y) + 4, label)
            p += tick_interval

        valve_config = [
            ("min", self.p_min_relief, QColor(100, 200, 100), "Min"),
            ("stiff", self.p_stiff, QColor(255, 200, 0), "Stiff"),
            ("safety", self.p_safety, QColor(255, 100, 100), "Safe"),
        ]
        for key, threshold, color, label in valve_config:
            intensity = self._valve_intensity(key, threshold)
            is_open = bool(self.valve_states.get(key, False))
            self._draw_valve_band(
                painter,
                key,
                threshold,
                color,
                scale_x,
                scale_width,
                intensity,
                is_open,
            )
            self._draw_compression_scale(
                painter,
                key,
                threshold,
                color,
                scale_x,
                is_open,
            )
            self._draw_marker(
                painter,
                threshold,
                label,
                color,
                scale_x,
                scale_width,
                active=is_open,
                intensity=intensity,
            )

        self._draw_marker(
            painter,
            self.p_atm,
            "Patm",
            QColor(150, 150, 150),
            scale_x,
            scale_width,
        )

        y_tank = self.map_pressure_to_height(self.p_tank)
        painter.setPen(QPen(QColor(255, 255, 0), 3))
        painter.drawLine(
            scale_x - 5, int(y_tank), scale_x + scale_width + 5, int(y_tank)
        )

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
        *,
        active: bool = False,
        intensity: float = 0.0,
    ) -> None:
        """Draw a reference pressure marker."""

        y = self.map_pressure_to_height(pressure)
        highlight = QColor(color)
        highlight.setAlpha(255)
        clamped_intensity = max(0.0, min(1.0, float(intensity)))
        if active:
            highlight = highlight.lighter(130 + int(40 * clamped_intensity))

        painter.setPen(QPen(highlight if active else color, 2, Qt.PenStyle.DashLine))
        painter.drawLine(x, int(y), x + width, int(y))

        painter.setPen(Qt.PenStyle.NoPen)
        label_bg = QColor(0, 0, 0, 220 if active else 180)
        painter.setBrush(QBrush(label_bg))
        painter.drawRoundedRect(x - 6, int(y) - 10, 36, 14, 3, 3)

        painter.setPen(highlight if active else color)
        font = QFont("Arial", 7, QFont.Weight.Bold if active else QFont.Weight.Normal)
        painter.setFont(font)
        painter.drawText(x - 3, int(y), label)

    def _draw_valve_band(
        self,
        painter: QPainter,
        key: str,
        threshold: float,
        color: QColor,
        x: int,
        width: int,
        intensity: float,
        is_open: bool,
    ) -> None:
        """Render a translucent band showing valve activity."""

        clamped = max(0.0, min(1.0, float(intensity)))
        flow_component = self._flow_ratio(key)
        effective = max(clamped, flow_component)
        if effective <= 0.0 and is_open:
            effective = 0.2
        y = self.map_pressure_to_height(threshold)
        band_width = int(12 + 22 * effective)
        rect_x = x - band_width - 10
        rect_width = band_width

        fill_color = QColor(color)
        alpha = 70 + int(150 * effective)
        if is_open:
            alpha = 100 + int(120 * effective)
        fill_color.setAlpha(max(30, min(220, alpha)))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(fill_color))
        painter.drawRoundedRect(rect_x, int(y) - 7, rect_width, 14, 4, 4)

        if is_open:
            glow = QColor(color)
            glow.setAlpha(min(255, 80 + int(160 * effective)))
            painter.setPen(QPen(glow, 2))
            painter.drawRoundedRect(rect_x - 2, int(y) - 9, rect_width + 4, 18, 6, 6)

    def _draw_compression_scale(
        self,
        painter: QPainter,
        key: str,
        threshold: float,
        color: QColor,
        scale_x: int,
        is_open: bool,
    ) -> None:
        """Draw a small gauge showing relief valve compression/flow."""

        ratio = self._flow_ratio(key)
        if ratio <= 0.0 and not is_open:
            return

        base_x = scale_x - 28
        bar_width = 14
        bar_height = 44
        y = int(self.map_pressure_to_height(threshold))
        top = y - bar_height // 2

        painter.save()
        try:
            background = QColor(35, 35, 40, 180)
            painter.setPen(QPen(QColor(80, 80, 90, 200), 1))
            painter.setBrush(QBrush(background))
            painter.drawRoundedRect(base_x, top, bar_width, bar_height, 3, 3)

            fill_height = int(bar_height * max(0.0, min(1.0, ratio)))
            if fill_height > 0:
                direction = 1 if self.relief_flows.get(key, 0.0) >= 0 else -1
                fill_color = QColor(color)
                alpha = 90 + int(120 * ratio)
                if is_open:
                    alpha = 140 + int(90 * ratio)
                fill_color.setAlpha(max(60, min(240, alpha)))
                painter.setBrush(QBrush(fill_color))
                painter.setPen(Qt.PenStyle.NoPen)
                if direction >= 0:
                    fill_top = top + (bar_height - fill_height)
                else:
                    fill_top = top
                painter.drawRoundedRect(
                    base_x + 2,
                    fill_top,
                    bar_width - 4,
                    fill_height,
                    2,
                    2,
                )

            painter.setPen(QPen(QColor(200, 200, 210, 180), 1))
            arrow_x = base_x - 6
            arrow_y = y
            if self.relief_flows.get(key, 0.0) >= 0:
                painter.drawLine(arrow_x, arrow_y, arrow_x + 6, arrow_y - 5)
                painter.drawLine(arrow_x, arrow_y, arrow_x + 6, arrow_y + 5)
            else:
                painter.drawLine(arrow_x + 6, arrow_y - 5, arrow_x, arrow_y)
                painter.drawLine(arrow_x + 6, arrow_y + 5, arrow_x, arrow_y)
        finally:
            painter.restore()

    def _valve_intensity(self, key: str, threshold: float) -> float:
        """Return a 0..1 ratio representing valve overdrive."""

        overdrive = float(self.overdrive_values.get(key, 0.0))
        reference = max(1.0, abs(threshold) * 0.25)
        return float(np.clip(overdrive / reference, 0.0, 1.0))

    def _flow_ratio(self, key: str) -> float:
        """Return normalised flow magnitude for a relief valve."""

        magnitude = abs(float(self.relief_flows.get(key, 0.0)))
        peak = max(1e-6, float(self.relief_flow_peaks.get(key, 1.0)))
        return float(np.clip(magnitude / peak, 0.0, 1.0))


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

    def update_from_snapshot(self, snapshot: StateSnapshot) -> None:
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
