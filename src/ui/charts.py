"""
Charts widget using QtCharts for real-time data visualization
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor
from collections import deque

from src.runtime.state import StateSnapshot


class ChartWidget(QWidget):
    """Widget containing QtCharts for real-time data visualization"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Data buffers (limited size for performance)
        self.max_points = 5000
        self.time_buffer = deque(maxlen=self.max_points)

        # Pressure data buffers
        self.pressure_buffers = {
            "A1": deque(maxlen=self.max_points),
            "B1": deque(maxlen=self.max_points),
            "A2": deque(maxlen=self.max_points),
            "B2": deque(maxlen=self.max_points),
            "Tank": deque(maxlen=self.max_points),
        }

        # Frame dynamics buffers
        self.frame_buffers = {
            "heave": deque(maxlen=self.max_points),
            "roll": deque(maxlen=self.max_points),
            "pitch": deque(maxlen=self.max_points),
        }

        # Flow buffers
        self.flow_buffers = {
            "inflow": deque(maxlen=self.max_points),
            "outflow": deque(maxlen=self.max_points),
            "tank_relief": deque(maxlen=self.max_points),
        }

        # Setup UI
        self._setup_ui()

        # Update counter for performance
        self.update_counter = 0
        self.update_interval = 5  # Update every 5 snapshots

    def _setup_ui(self):
        """Setup chart UI with tabs"""
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create individual chart tabs
        self._create_pressure_chart()
        self._create_dynamics_chart()
        self._create_flow_chart()

    def _create_pressure_chart(self):
        """Create pressure monitoring chart"""
        # Create chart
        chart = QChart()
        chart.setTitle("System Pressures")
        chart.setAnimationOptions(
            QChart.AnimationOption.NoAnimation
        )  # Disable for performance

        # Set background colors for better visibility
        chart.setBackgroundBrush(QColor(30, 30, 40))  # Dark gray background
        chart.setTitleBrush(QColor(255, 255, 255))  # White title

        # Create series for each pressure
        self.pressure_series = {}
        colors = [
            QColor(255, 100, 100),  # Red for A1
            QColor(100, 255, 100),  # Green for B1
            QColor(100, 100, 255),  # Blue for A2
            QColor(255, 255, 100),  # Yellow for B2
            QColor(255, 100, 255),  # Magenta for Tank
        ]

        for i, name in enumerate(["A1", "B1", "A2", "B2", "Tank"]):
            series = QLineSeries()
            series.setName(f"Line {name}" if name != "Tank" else "Tank")
            series.setColor(colors[i])
            self.pressure_series[name] = series
            chart.addSeries(series)

        # Create axes
        self.pressure_x_axis = QValueAxis()
        self.pressure_x_axis.setTitleText("Time (s)")
        self.pressure_x_axis.setRange(0, 10)

        self.pressure_y_axis = QValueAxis()
        self.pressure_y_axis.setTitleText("Pressure (Pa)")
        self.pressure_y_axis.setRange(100000, 200000)  # 1-2 bar range

        chart.addAxis(self.pressure_x_axis, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(self.pressure_y_axis, Qt.AlignmentFlag.AlignLeft)

        # Attach series to axes
        for series in self.pressure_series.values():
            series.attachAxis(self.pressure_x_axis)
            series.attachAxis(self.pressure_y_axis)

        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Add to tab widget
        self.tab_widget.addTab(chart_view, "Pressures")

    def _create_dynamics_chart(self):
        """Create frame dynamics chart"""
        # Create chart
        chart = QChart()
        chart.setTitle("Frame Dynamics")
        chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)

        # Set background colors for better visibility
        chart.setBackgroundBrush(QColor(30, 30, 40))  # Dark gray background
        chart.setTitleBrush(QColor(255, 255, 255))  # White title

        # Create series
        self.dynamics_series = {}
        colors = [
            QColor(255, 100, 100),  # Red for heave
            QColor(100, 255, 100),  # Green for roll
            QColor(100, 100, 255),  # Blue for pitch
        ]

        for i, name in enumerate(["heave", "roll", "pitch"]):
            series = QLineSeries()
            series.setName(name.capitalize())
            series.setColor(colors[i])
            self.dynamics_series[name] = series
            chart.addSeries(series)

        # Create axes
        self.dynamics_x_axis = QValueAxis()
        self.dynamics_x_axis.setTitleText("Time (s)")
        self.dynamics_x_axis.setRange(0, 10)

        self.dynamics_y_axis = QValueAxis()
        self.dynamics_y_axis.setTitleText("Position/Angle")
        self.dynamics_y_axis.setRange(-0.1, 0.1)

        chart.addAxis(self.dynamics_x_axis, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(self.dynamics_y_axis, Qt.AlignmentFlag.AlignLeft)

        # Attach series to axes
        for series in self.dynamics_series.values():
            series.attachAxis(self.dynamics_x_axis)
            series.attachAxis(self.dynamics_y_axis)

        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Add to tab widget
        self.tab_widget.addTab(chart_view, "Dynamics")

    def _create_flow_chart(self):
        """Create mass flow chart"""
        # Create chart
        chart = QChart()
        chart.setTitle("Mass Flows")
        chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)

        # Set background colors for better visibility
        chart.setBackgroundBrush(QColor(30, 30, 40))  # Dark gray background
        chart.setTitleBrush(QColor(255, 255, 255))  # White title

        # Create series
        self.flow_series = {}
        colors = [
            QColor(100, 255, 100),  # Green for inflow
            QColor(255, 100, 100),  # Red for outflow
            QColor(255, 255, 100),  # Yellow for relief
        ]

        for i, name in enumerate(["inflow", "outflow", "tank_relief"]):
            series = QLineSeries()
            series.setName(name.replace("_", " ").title())
            series.setColor(colors[i])
            self.flow_series[name] = series
            chart.addSeries(series)

        # Create axes
        self.flow_x_axis = QValueAxis()
        self.flow_x_axis.setTitleText("Time (s)")
        self.flow_x_axis.setRange(0, 10)

        self.flow_y_axis = QValueAxis()
        self.flow_y_axis.setTitleText("Mass Flow (kg/s)")
        self.flow_y_axis.setRange(-0.001, 0.001)

        chart.addAxis(self.flow_x_axis, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(self.flow_y_axis, Qt.AlignmentFlag.AlignLeft)

        # Attach series to axes
        for series in self.flow_series.values():
            series.attachAxis(self.flow_x_axis)
            series.attachAxis(self.flow_y_axis)

        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Add to tab widget
        self.tab_widget.addTab(chart_view, "Flows")

    def update_from_snapshot(self, snapshot: StateSnapshot):
        """Update charts from state snapshot

        Args:
            snapshot: Current system state
        """
        # Throttle updates for performance
        self.update_counter += 1
        if self.update_counter % self.update_interval != 0:
            return

        # Add time point
        sim_time = snapshot.simulation_time
        self.time_buffer.append(sim_time)

        # Update pressure data
        self._update_pressure_data(snapshot)

        # Update dynamics data
        self._update_dynamics_data(snapshot)

        # Update flow data
        self._update_flow_data(snapshot)

        # Update chart ranges
        self._update_chart_ranges(sim_time)

    def _update_pressure_data(self, snapshot: StateSnapshot):
        """Update pressure chart data"""
        # Line pressures
        for line_name, line_state in snapshot.lines.items():
            buffer_key = line_name.value  # A1, B1, A2, B2
            if buffer_key in self.pressure_buffers:
                self.pressure_buffers[buffer_key].append(line_state.pressure)

        # Tank pressure
        self.pressure_buffers["Tank"].append(snapshot.tank.pressure)

        # Update series
        for name, series in self.pressure_series.items():
            if name in self.pressure_buffers:
                buffer = self.pressure_buffers[name]
                time_buffer = self.time_buffer

                if len(buffer) == len(time_buffer):
                    # Convert to QPointF objects
                    points = [
                        QPointF(float(t), float(p)) for t, p in zip(time_buffer, buffer)
                    ]
                    series.replace(points)

    def _update_dynamics_data(self, snapshot: StateSnapshot):
        """Update dynamics chart data"""
        frame = snapshot.frame

        # Add new data points
        self.frame_buffers["heave"].append(frame.heave)
        self.frame_buffers["roll"].append(frame.roll)
        self.frame_buffers["pitch"].append(frame.pitch)

        # Update series
        for name, series in self.dynamics_series.items():
            buffer = self.frame_buffers[name]
            time_buffer = self.time_buffer

            if len(buffer) == len(time_buffer):
                # Convert to QPointF objects
                points = [
                    QPointF(float(t), float(v)) for t, v in zip(time_buffer, buffer)
                ]
                series.replace(points)

    def _update_flow_data(self, snapshot: StateSnapshot):
        """Update flow chart data"""
        # Calculate total flows
        total_inflow = sum(line.flow_atmo for line in snapshot.lines.values())
        total_outflow = sum(line.flow_tank for line in snapshot.lines.values())
        tank_relief = (
            snapshot.tank.flow_min
            + snapshot.tank.flow_stiff
            + snapshot.tank.flow_safety
        )

        # Add to buffers
        self.flow_buffers["inflow"].append(total_inflow)
        self.flow_buffers["outflow"].append(total_outflow)
        self.flow_buffers["tank_relief"].append(tank_relief)

        # Update series
        for name, series in self.flow_series.items():
            buffer = self.flow_buffers[name]
            time_buffer = self.time_buffer

            if len(buffer) == len(time_buffer):
                # Convert to QPointF objects
                points = [
                    QPointF(float(t), float(f)) for t, f in zip(time_buffer, buffer)
                ]
                series.replace(points)

    def _update_chart_ranges(self, current_time: float):
        """Update chart X-axis ranges to follow current time"""
        # Update time window (show last 10 seconds)
        time_window = 10.0

        if current_time > time_window:
            min_time = current_time - time_window
            max_time = current_time
        else:
            min_time = 0.0
            max_time = time_window

        # Update all X axes
        self.pressure_x_axis.setRange(min_time, max_time)
        self.dynamics_x_axis.setRange(min_time, max_time)
        self.flow_x_axis.setRange(min_time, max_time)

        # Auto-scale Y axes occasionally
        if self.update_counter % 100 == 0:  # Every 100 updates
            self._auto_scale_y_axes()

    def _auto_scale_y_axes(self):
        """Auto-scale Y axes based on current data"""
        # Auto-scale pressure axis
        if self.pressure_buffers["A1"] and len(self.pressure_buffers["A1"]) > 10:
            all_pressures = []
            for buffer in self.pressure_buffers.values():
                if buffer:
                    all_pressures.extend(list(buffer)[-100:])  # Last 100 points

            if all_pressures:
                min_p = min(all_pressures)
                max_p = max(all_pressures)
                margin = (max_p - min_p) * 0.1
                self.pressure_y_axis.setRange(min_p - margin, max_p + margin)

        # Auto-scale dynamics axis
        if self.frame_buffers["heave"] and len(self.frame_buffers["heave"]) > 10:
            all_dynamics = []
            for buffer in self.frame_buffers.values():
                if buffer:
                    all_dynamics.extend(list(buffer)[-100:])  # Last 100 points

            if all_dynamics:
                min_d = min(all_dynamics)
                max_d = max(all_dynamics)
                margin = max(abs(min_d), abs(max_d)) * 0.1
                self.dynamics_y_axis.setRange(min_d - margin, max_d + margin)

    def clear_data(self):
        """Clear all chart data"""
        # Clear buffers
        self.time_buffer.clear()

        for buffer in self.pressure_buffers.values():
            buffer.clear()

        for buffer in self.frame_buffers.values():
            buffer.clear()

        for buffer in self.flow_buffers.values():
            buffer.clear()

        # Clear series
        for series in self.pressure_series.values():
            series.clear()

        for series in self.dynamics_series.values():
            series.clear()

        for series in self.flow_series.values():
            series.clear()

        # Reset counter
        self.update_counter = 0
