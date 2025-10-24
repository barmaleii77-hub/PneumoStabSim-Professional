"""
Simple demo application for runtime system
Shows Qt integration without physics dependencies
"""

import sys
import time
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import QTimer, QThread, QObject, Signal, Slot, Qt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from runtime.sync import LatestOnlyQueue, PerformanceMetrics, TimingAccumulator
from runtime.state import StateSnapshot, StateBus, FrameState


class SimplePhysicsWorker(QObject):
    """Simplified physics worker for demonstration"""

    state_ready = Signal(object)

    def __init__(self):
        super().__init__()
        self.running = False
        self.timer = None
        self.step_count = 0
        self.start_time = time.perf_counter()

        # Performance tracking
        self.performance = PerformanceMetrics()
        self.timing_accumulator = TimingAccumulator(0.01)  # 10ms timestep

    @Slot()
    def start_simulation(self):
        """Start simulation"""
        if not self.running:
            self.running = True

            # Create timer in this thread
            self.timer = QTimer()
            self.timer.timeout.connect(self._physics_step)
            self.timer.start(10)  # 10ms = 100 Hz
            print("? Physics worker started")

    @Slot()
    def stop_simulation(self):
        """Stop simulation"""
        if self.timer:
            self.timer.stop()
        self.running = False
        print("? Physics worker stopped")

    @Slot()
    def _physics_step(self):
        """Physics step - creates dummy state"""
        current_time = time.perf_counter()
        sim_time = current_time - self.start_time

        # Create dummy state snapshot
        snapshot = StateSnapshot()
        snapshot.simulation_time = sim_time
        snapshot.step_number = self.step_count

        # Add some dummy dynamics
        snapshot.frame = FrameState()
        snapshot.frame.heave = 0.01 * np.sin(sim_time * 2)  # 2 Hz oscillation
        snapshot.frame.roll = 0.005 * np.sin(sim_time * 1.5)
        snapshot.frame.pitch = 0.003 * np.sin(sim_time * 0.8)

        # Emit state
        self.state_ready.emit(snapshot)

        self.step_count += 1


class DemoMainWindow(QMainWindow):
    """Demo main window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Runtime System Demo (P7)")
        self.setGeometry(100, 100, 800, 600)

        # Current state
        self.current_snapshot = None

        # Setup UI
        self._setup_ui()

        # Setup simulation
        self._setup_simulation()

        # Setup render timer
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self._update_display)
        self.render_timer.start(16)  # ~60 FPS

    def _setup_ui(self):
        """Setup UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Status display
        self.status_label = QLabel("Status: Ready")
        self.time_label = QLabel("Sim Time: 0.000s")
        self.step_label = QLabel("Steps: 0")
        self.frame_label = QLabel("Frame: heave=0.000m, roll=0.000rad")

        layout.addWidget(self.status_label)
        layout.addWidget(self.time_label)
        layout.addWidget(self.step_label)
        layout.addWidget(self.frame_label)

        # Control buttons
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")

        self.start_button.clicked.connect(self._start_simulation)
        self.stop_button.clicked.connect(self._stop_simulation)

        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

    def _setup_simulation(self):
        """Setup simulation components"""
        # Create physics thread
        self.physics_thread = QThread()
        self.physics_worker = SimplePhysicsWorker()

        # Move to thread
        self.physics_worker.moveToThread(self.physics_thread)

        # Create state bus and queue
        self.state_bus = StateBus()
        self.state_queue = LatestOnlyQueue()

        # Connect signals
        self.physics_worker.state_ready.connect(
            self._on_state_ready, Qt.QueuedConnection
        )

        # Start thread
        self.physics_thread.start()

    @Slot(object)
    def _on_state_ready(self, snapshot):
        """Handle state from physics"""
        # Put in queue (latest only)
        self.state_queue.put_nowait(snapshot)

    @Slot()
    def _update_display(self):
        """Update display from latest state"""
        # Get latest state
        snapshot = self.state_queue.get_nowait()

        if snapshot:
            self.current_snapshot = snapshot

            # Update labels
            self.time_label.setText(f"Sim Time: {snapshot.simulation_time:.3f}s")
            self.step_label.setText(f"Steps: {snapshot.step_number}")

            if snapshot.frame:
                self.frame_label.setText(
                    f"Frame: heave={snapshot.frame.heave * 1000:.1f}mm, "
                    f"roll={snapshot.frame.roll * 1000:.2f}mrad"
                )

            # Show queue stats
            stats = self.state_queue.get_stats()
            self.status_label.setText(
                f"Status: Running - Queue: {stats['get_count']}/{stats['put_count']} "
                f"(dropped: {stats['dropped_count']})"
            )

    @Slot()
    def _start_simulation(self):
        """Start simulation"""
        self.physics_worker.start_simulation()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    @Slot()
    def _stop_simulation(self):
        """Stop simulation"""
        self.physics_worker.stop_simulation()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        """Handle close"""
        self.render_timer.stop()
        if self.physics_thread.isRunning():
            self.physics_thread.quit()
            self.physics_thread.wait(3000)
        event.accept()


def main():
    """Run demo"""
    # Import numpy here to avoid issues
    global np
    import numpy as np

    app = QApplication(sys.argv)

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    window = DemoMainWindow()
    window.show()

    print("=" * 60)
    print("RUNTIME SYSTEM DEMO (P7)")
    print("=" * 60)
    print("? Qt application created")
    print("? Physics thread started")
    print("? State bus connected")
    print("? LatestOnlyQueue active")
    print("? Render loop at ~60 FPS")
    print("")
    print("Click 'Start' to begin simulation")
    print("Watch the oscillating values - this demonstrates:")
    print(" • Fixed-timestep physics in separate thread")
    print(" • Thread-safe state communication")
    print(" • Latest-only queue (no frame lag)")
    print(" • UI remains responsive")
    print("=" * 60)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
