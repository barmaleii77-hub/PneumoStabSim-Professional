"""
Main window for PneumoStabSim application
"""
from PySide6.QtWidgets import (QMainWindow, QStatusBar, QDockWidget, QWidget, 
                              QMenuBar, QToolBar, QPushButton, QLabel, QVBoxLayout)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QAction, QKeySequence
import logging

from .gl_view import GLView
from .charts import ChartWidget
from ..runtime import SimulationManager, StateSnapshot


class MainWindow(QMainWindow):
    """Main application window with integrated simulation"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PneumoStabSim - Pneumatic Stabilizer Simulator")
        self.setGeometry(100, 100, 1400, 900)
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # Current state
        self.current_snapshot: Optional[StateSnapshot] = None
        self.is_simulation_running = False
        
        # Setup simulation manager
        self.simulation_manager = SimulationManager(self)
        
        # Setup UI components
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        
        # Setup render timer (60 FPS for UI)
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self._update_render)
        self.render_timer.start(16)  # ~60 FPS
        
        # Connect simulation signals
        self._connect_simulation_signals()
        
        # Start simulation manager
        self.simulation_manager.start()
        
        self.logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Setup main UI components"""
        # Setup central OpenGL widget
        self.gl_view = GLView()
        self.setCentralWidget(self.gl_view)
        
        # Setup dock widget with charts
        self.chart_dock = QDockWidget("Charts", self)
        self.chart_widget = ChartWidget()
        self.chart_dock.setWidget(self.chart_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.chart_dock)
        
        # Set dock widget properties
        self.chart_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable | 
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        
        # Setup control dock
        self.control_dock = QDockWidget("Controls", self)
        self.control_widget = self._create_control_widget()
        self.control_dock.setWidget(self.control_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.control_dock)
    
    def _create_control_widget(self) -> QWidget:
        """Create control panel widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Simulation control buttons
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.reset_button = QPushButton("Reset")
        self.pause_button = QPushButton("Pause")
        
        # Connect button signals
        self.start_button.clicked.connect(self._start_simulation)
        self.stop_button.clicked.connect(self._stop_simulation)
        self.reset_button.clicked.connect(self._reset_simulation)
        self.pause_button.clicked.connect(self._pause_simulation)
        
        # Add buttons to layout
        layout.addWidget(QLabel("Simulation Control:"))
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.reset_button)
        
        # Status labels
        self.sim_time_label = QLabel("Sim Time: 0.000s")
        self.step_count_label = QLabel("Steps: 0")
        self.fps_label = QLabel("Physics FPS: 0")
        
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.sim_time_label)
        layout.addWidget(self.step_count_label)
        layout.addWidget(self.fps_label)
        
        layout.addStretch()  # Push content to top
        
        return widget
    
    def _setup_menus(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Simulation menu
        sim_menu = menubar.addMenu("Simulation")
        
        start_action = QAction("Start", self)
        start_action.setShortcut(QKeySequence("Ctrl+R"))
        start_action.triggered.connect(self._start_simulation)
        sim_menu.addAction(start_action)
        
        stop_action = QAction("Stop", self)
        stop_action.setShortcut(QKeySequence("Ctrl+T"))
        stop_action.triggered.connect(self._stop_simulation)
        sim_menu.addAction(stop_action)
        
        reset_action = QAction("Reset", self)
        reset_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        reset_action.triggered.connect(self._reset_simulation)
        sim_menu.addAction(reset_action)
    
    def _setup_toolbar(self):
        """Setup toolbar"""
        toolbar = self.addToolBar("Main")
        
        # Add simulation control actions
        toolbar.addAction("Start", self._start_simulation)
        toolbar.addAction("Stop", self._stop_simulation)
        toolbar.addAction("Pause", self._pause_simulation)
        toolbar.addAction("Reset", self._reset_simulation)
    
    def _setup_status_bar(self):
        """Setup status bar with simulation info"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status labels
        self.status_label = QLabel("Ready")
        self.realtime_label = QLabel("RT: 1.00x")
        self.queue_label = QLabel("Queue: 0/0")
        
        self.status_bar.addWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.queue_label)
        self.status_bar.addPermanentWidget(self.realtime_label)
        
        self.status_bar.showMessage("Application started")
    
    def _connect_simulation_signals(self):
        """Connect simulation manager signals"""
        # State updates
        self.simulation_manager.state_bus.state_ready.connect(
            self._on_state_update, Qt.QueuedConnection)
        
        # Error handling
        self.simulation_manager.state_bus.physics_error.connect(
            self._on_physics_error, Qt.QueuedConnection)
    
    @Slot()
    def _start_simulation(self):
        """Start simulation"""
        if not self.is_simulation_running:
            self.simulation_manager.state_bus.start_simulation.emit()
            self.is_simulation_running = True
            self.status_bar.showMessage("Simulation started")
            self.logger.info("Simulation started by user")
            
            # Update button states
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.pause_button.setEnabled(True)
    
    @Slot()
    def _stop_simulation(self):
        """Stop simulation"""
        if self.is_simulation_running:
            self.simulation_manager.state_bus.stop_simulation.emit()
            self.is_simulation_running = False
            self.status_bar.showMessage("Simulation stopped")
            self.logger.info("Simulation stopped by user")
            
            # Update button states
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.pause_button.setEnabled(False)
    
    @Slot()
    def _pause_simulation(self):
        """Pause/unpause simulation"""
        self.simulation_manager.state_bus.pause_simulation.emit()
        self.logger.info("Simulation pause toggled")
    
    @Slot()
    def _reset_simulation(self):
        """Reset simulation"""
        self.simulation_manager.state_bus.reset_simulation.emit()
        self.status_bar.showMessage("Simulation reset")
        self.logger.info("Simulation reset by user")
    
    @Slot(object)
    def _on_state_update(self, snapshot: StateSnapshot):
        """Handle state update from physics"""
        self.current_snapshot = snapshot
        
        # Update control panel labels
        if snapshot:
            self.sim_time_label.setText(f"Sim Time: {snapshot.simulation_time:.3f}s")
            self.step_count_label.setText(f"Steps: {snapshot.step_number}")
            
            # Calculate effective physics FPS
            if snapshot.aggregates.physics_step_time > 0:
                fps = 1.0 / snapshot.aggregates.physics_step_time
                self.fps_label.setText(f"Physics FPS: {fps:.1f}")
        
        # Update charts
        if hasattr(self.chart_widget, 'update_from_snapshot'):
            self.chart_widget.update_from_snapshot(snapshot)
    
    @Slot(str)
    def _on_physics_error(self, error_msg: str):
        """Handle physics error"""
        self.status_bar.showMessage(f"Physics Error: {error_msg}")
        self.logger.error(f"Physics error: {error_msg}")
        
        # Stop simulation on error
        self._stop_simulation()
    
    @Slot()
    def _update_render(self):
        """Update render (called by render timer)"""
        # Update GL view with current state
        if self.current_snapshot and hasattr(self.gl_view, 'set_current_state'):
            self.gl_view.set_current_state(self.current_snapshot)
        
        # Update queue statistics
        stats = self.simulation_manager.get_queue_stats()
        self.queue_label.setText(f"Queue: {stats['get_count']}/{stats['put_count']}")
        
        # Update realtime factor if available
        if self.current_snapshot and self.current_snapshot.aggregates:
            # Calculate realtime factor from physics timing
            rt_factor = 1.0  # Placeholder
            self.realtime_label.setText(f"RT: {rt_factor:.2f}x")
        
        # Trigger GL view update
        self.gl_view.update()
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.logger.info("Main window closing")
        
        # Stop render timer
        self.render_timer.stop()
        
        # Stop simulation manager
        self.simulation_manager.stop()
        
        # Accept close event
        event.accept()
        
        self.logger.info("Main window closed")


# Import Optional type
from typing import Optional