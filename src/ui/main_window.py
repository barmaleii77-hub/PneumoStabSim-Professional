"""
Main window for PneumoStabSim application
Qt Quick 3D rendering with RHI/Direct3D backend (no OpenGL)
"""
from PySide6.QtWidgets import (
    QMainWindow, QStatusBar, QDockWidget, QWidget, QMenuBar, QToolBar, QLabel,
    QVBoxLayout, QFileDialog, QMessageBox, QApplication, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Slot, QSettings, QUrl, QFileInfo
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtQuick import QQuickView
import logging
import json
from pathlib import Path
from typing import Optional

# NO OpenGL imports - using Qt Quick 3D instead
# from .gl_view import GLView  # REMOVED

from .charts import ChartWidget
from .panels import GeometryPanel, PneumoPanel, ModesPanel, RoadPanel
from ..runtime import SimulationManager, StateSnapshot


class MainWindow(QMainWindow):
    """Main application window with Qt Quick 3D rendering (RHI/Direct3D)"""
    SETTINGS_ORG = "PneumoStabSim"
    SETTINGS_APP = "PneumoStabSimApp"
    SETTINGS_GEOMETRY = "MainWindow/Geometry"
    SETTINGS_STATE = "MainWindow/State"
    SETTINGS_DOCK = "MainWindow/Docks"
    SETTINGS_LAST_PRESET = "Presets/LastPath"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PneumoStabSim - Qt Quick 3D (RHI/D3D)")
        self.resize(1500, 950)
        
        # Ensure window is in normal state
        self.setWindowState(Qt.WindowState.WindowNoState)

        # Logging
        self.logger = logging.getLogger(__name__)
        
        print("MainWindow: Creating SimulationManager...")
        
        # Simulation manager (will start AFTER window.show())
        try:
            self.simulation_manager = SimulationManager(self)
            self._sim_started = False  # Flag to ensure single start
            print("? SimulationManager created (not started yet)")
        except Exception as e:
            print(f"? SimulationManager creation failed: {e}")
            import traceback
            traceback.print_exc()
            raise

        # Current snapshot
        self.current_snapshot: Optional[StateSnapshot] = None
        self.is_simulation_running = False

        # Panels references (temporarily disabled)
        self.geometry_panel: Optional[GeometryPanel] = None
        self.pneumo_panel: Optional[PneumoPanel] = None
        self.modes_panel: Optional[ModesPanel] = None
        self.road_panel: Optional[RoadPanel] = None
        self.chart_widget: Optional[ChartWidget] = None

        # Qt Quick 3D view reference
        self._qquick_view: Optional[QQuickView] = None
        self._qml_root_object = None

        print("MainWindow: Building UI...")
        
        # Build UI
        self._setup_central()
        print("  ? Central Qt Quick 3D view setup")
        
        self._setup_docks()
        print("  ? Docks setup (panels disabled)")
        
        self._setup_menus()
        print("  ? Menus setup")
        
        self._setup_toolbar()
        print("  ? Toolbar setup")
        
        self._setup_status_bar()
        print("  ? Status bar setup")
        
        self._connect_simulation_signals()
        print("  ? Signals connected")

        # Render timer (UI thread ~60 FPS) - for QML property updates
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self._update_render)
        self.render_timer.start(16)
        print("  ? Render timer started")

        # DON'T start simulation manager here - will do in showEvent()
        print("  ? Simulation manager will start after window.show()")

        # Restore settings (SKIP restoreGeometry to avoid crashes)
        # self._restore_settings()
        print("  ??  Settings restore skipped (avoiding potential crashes)")

        self.logger.info("Main window (Qt Quick 3D) initialized")
        print("? MainWindow.__init__() complete")

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _setup_central(self):
        """Create central Qt Quick 3D view using QQuickView + createWindowContainer
        
        Preferred approach: QQuickView + createWindowContainer
        - Better performance than QQuickWidget
        - Proper integration with QMainWindow
        - Native window container for Qt Quick content
        """
        print("    _setup_central: Creating Qt Quick 3D view...")
        
        try:
            # Create QQuickView for Qt Quick 3D content
            self._qquick_view = QQuickView()
            
            # Set resize mode to synchronize QML root object size with view
            self._qquick_view.setResizeMode(QQuickView.SizeRootObjectToView)
            
            # Load QML file with Qt Quick 3D scene
            qml_path = Path("assets/qml/main.qml")
            if not qml_path.exists():
                raise FileNotFoundError(f"QML file not found: {qml_path.absolute()}")
            
            qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
            print(f"    Loading QML: {qml_url.toString()}")
            
            self._qquick_view.setSource(qml_url)
            
            # Check for QML errors
            if self._qquick_view.status() == QQuickView.Status.Error:
                errors = self._qquick_view.errors()
                error_msg = "\n".join(str(e) for e in errors)
                raise RuntimeError(f"QML errors:\n{error_msg}")
            
            # Get root object for property access
            self._qml_root_object = self._qquick_view.rootObject()
            if not self._qml_root_object:
                raise RuntimeError("Failed to get QML root object")
            
            print("    ? QML loaded successfully")
            
            # Wrap QQuickView in QWidget container
            # This is the recommended way to embed Qt Quick in QWidget-based UI
            container = QWidget.createWindowContainer(self._qquick_view, self)
            container.setMinimumSize(800, 600)
            container.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            
            # Set as central widget
            self.setCentralWidget(container)
            
            print("    ? Qt Quick 3D view embedded via createWindowContainer")
            
        except Exception as e:
            print(f"    ? Qt Quick 3D view creation failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to simple label
            fallback = QLabel(
                "Qt Quick 3D initialization failed\n\n"
                "Check:\n"
                "1. PySide6-Addons installed (pip install PySide6-Addons)\n"
                "2. QML file exists: assets/qml/main.qml\n"
                "3. Console for detailed errors"
            )
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setStyleSheet("background: #1a1a2e; color: #ff6b6b; font-size: 14px; padding: 20px;")
            self.setCentralWidget(fallback)
            self._qquick_view = None
            print("    ??  Using fallback widget")

    def _setup_docks(self):
        """Create and place dock panels"""
        print("    _setup_docks: Creating panels...")
        
        # Create geometry panel (left)
        self.geometry_dock = QDockWidget("Geometry", self)
        self.geometry_panel = GeometryPanel(self)
        self.geometry_dock.setWidget(self.geometry_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.geometry_dock)
        print("      ? Geometry panel created")
        
        # Create pneumatics panel (left, below geometry)
        self.pneumo_dock = QDockWidget("Pneumatics", self)
        self.pneumo_panel = PneumoPanel(self)
        self.pneumo_dock.setWidget(self.pneumo_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.pneumo_dock)
        print("      ? Pneumatics panel created")
        
        # Create charts panel (right)
        self.charts_dock = QDockWidget("Charts", self)
        self.chart_widget = ChartWidget(self)
        self.charts_dock.setWidget(self.chart_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.charts_dock)
        print("      ? Charts panel created")
        
        # Create modes/simulation control panel (right, below charts)
        self.modes_dock = QDockWidget("Simulation & Modes", self)
        self.modes_panel = ModesPanel(self)
        self.modes_dock.setWidget(self.modes_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.modes_dock)
        print("      ? Modes panel created")
        
        # Create road profiles panel (bottom)
        self.road_dock = QDockWidget("Road Profiles", self)
        self.road_panel = RoadPanel(self)
        self.road_dock.setWidget(self.road_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.road_dock)
        print("      ? Road panel created")
        
        # Connect panel signals
        self._wire_panel_signals()
        print("    ? Panels created and wired")

    def _wire_panel_signals(self):
        """Connect panel signals to simulation/state bus"""
        bus = self.simulation_manager.state_bus

        # Geometry updates -> (placeholder: just log / future: emit structured config)
        if self.geometry_panel:
            self.geometry_panel.parameter_changed.connect(
                lambda name, val: self.logger.info(f"Geometry param {name}={val}"))

        # Pneumatic panel -> send thermo mode and master isolation
        if self.pneumo_panel:
            self.pneumo_panel.mode_changed.connect(self._on_mode_changed)
            self.pneumo_panel.parameter_changed.connect(self._on_pneumo_param)

        # Modes panel -> simulation control + modes
        if self.modes_panel:
            self.modes_panel.simulation_control.connect(self._on_sim_control)
            self.modes_panel.mode_changed.connect(self._on_mode_changed)
            self.modes_panel.parameter_changed.connect(
                lambda n, v: self.logger.debug(f"Road/global param {n}={v}"))

        # Road panel -> load/apply road profiles (placeholder logging)
        if self.road_panel:
            self.road_panel.load_csv_profile.connect(
                lambda path: self.logger.info(f"Load CSV road profile: {path}"))
            self.road_panel.apply_preset.connect(
                lambda p: self.logger.info(f"Apply road preset: {p}"))
            self.road_panel.apply_to_wheels.connect(
                lambda pname, wheels: self.logger.info(f"Apply {pname} to wheels {wheels}"))
            self.road_panel.clear_profiles.connect(
                lambda: self.logger.info("Clear road profiles"))

    # ------------------------------------------------------------------
    # Menus & Toolbars
    # ------------------------------------------------------------------
    def _setup_menus(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        
        # Preset actions
        save_preset_act = QAction("Save Preset...", self)
        load_preset_act = QAction("Load Preset...", self)
        save_preset_act.triggered.connect(self._save_preset)
        load_preset_act.triggered.connect(self._load_preset)
        file_menu.addAction(save_preset_act)
        file_menu.addAction(load_preset_act)
        file_menu.addSeparator()
        
        # Export submenu (P11)
        export_menu = file_menu.addMenu("Export")
        export_timeseries_act = QAction("Export Timeseries...", self)
        export_snapshots_act = QAction("Export Snapshots...", self)
        export_timeseries_act.triggered.connect(self._export_timeseries)
        export_snapshots_act.triggered.connect(self._export_snapshots)
        export_menu.addAction(export_timeseries_act)
        export_menu.addAction(export_snapshots_act)
        file_menu.addSeparator()
        
        # Exit
        exit_act = QAction("Exit", self)
        exit_act.setShortcut(QKeySequence.StandardKey.Quit)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # Road menu
        road_menu = menubar.addMenu("Road")
        load_csv_act = QAction("Load CSV...", self)
        clear_profiles_act = QAction("Clear Profiles", self)
        load_csv_act.triggered.connect(lambda: self.road_panel and self.road_panel._browse_csv_file())
        clear_profiles_act.triggered.connect(lambda: self.road_panel and self.road_panel._clear_all_profiles())
        road_menu.addAction(load_csv_act)
        road_menu.addAction(clear_profiles_act)

        # Settings / Parameters menu
        params_menu = menubar.addMenu("Parameters")
        reset_ui_act = QAction("Reset UI Layout", self)
        reset_ui_act.triggered.connect(self._reset_ui_layout)
        params_menu.addAction(reset_ui_act)

        # View menu (show/hide docks) - only for non-None docks
        view_menu = menubar.addMenu("View")
        self._dock_actions = []
        
        # Only create menu items for docks that actually exist
        available_docks = [
            (self.geometry_dock, "Geometry"),
            (self.pneumo_dock, "Pneumatics"),
            (self.charts_dock, "Charts"),
            (self.modes_dock, "Modes"),
            (self.road_dock, "Road Profiles")
        ]
        
        for dock, title in available_docks:
            if dock:  # Only add if dock exists
                act = QAction(title, self, checkable=True, checked=True)
                act.toggled.connect(lambda checked, d=dock: d.setVisible(checked))
                view_menu.addAction(act)
                self._dock_actions.append(act)
        
        # If no docks available, add placeholder
        if not self._dock_actions:
            placeholder = QAction("(Panels disabled)", self)
            placeholder.setEnabled(False)
            view_menu.addAction(placeholder)

    def _setup_toolbar(self):
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(True)
        start_act = QAction("Start", self)
        stop_act = QAction("Stop", self)
        pause_act = QAction("Pause", self)
        reset_act = QAction("Reset", self)
        start_act.triggered.connect(lambda: self._on_sim_control("start"))
        stop_act.triggered.connect(lambda: self._on_sim_control("stop"))
        pause_act.triggered.connect(lambda: self._on_sim_control("pause"))
        reset_act.triggered.connect(lambda: self._on_sim_control("reset"))
        toolbar.addActions([start_act, stop_act, pause_act, reset_act])

    def _setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.sim_time_label = QLabel("Sim Time: 0.000s")
        self.step_count_label = QLabel("Steps: 0")
        self.fps_label = QLabel("Physics FPS: 0")
        self.realtime_label = QLabel("RT: 1.00x")
        self.queue_label = QLabel("Queue: 0/0")
        for w in [self.sim_time_label, self.step_count_label, self.fps_label, self.queue_label, self.realtime_label]:
            self.status_bar.addPermanentWidget(w)
        self.status_bar.showMessage("Ready")

    # ------------------------------------------------------------------
    # Simulation Control & Panels Interaction
    # ------------------------------------------------------------------
    def _connect_simulation_signals(self):
        bus = self.simulation_manager.state_bus
        bus.state_ready.connect(self._on_state_update, Qt.QueuedConnection)
        bus.physics_error.connect(self._on_physics_error, Qt.QueuedConnection)

    @Slot(object)
    def _on_state_update(self, snapshot: StateSnapshot):
        self.current_snapshot = snapshot
        if snapshot:
            self.sim_time_label.setText(f"Sim Time: {snapshot.simulation_time:.3f}s")
            self.step_count_label.setText(f"Steps: {snapshot.step_number}")
            if snapshot.aggregates.physics_step_time > 0:
                fps = 1.0 / snapshot.aggregates.physics_step_time
                self.fps_label.setText(f"Physics FPS: {fps:.1f}")
        if self.chart_widget:
            self.chart_widget.update_from_snapshot(snapshot)

    @Slot(str)
    def _on_physics_error(self, msg: str):
        self.status_bar.showMessage(f"Physics Error: {msg}")
        self.logger.error(msg)

    # Panel signal handlers
    def _on_sim_control(self, command: str):
        bus = self.simulation_manager.state_bus
        if command == "start":
            bus.start_simulation.emit()
            self.is_simulation_running = True
        elif command == "stop":
            bus.stop_simulation.emit()
            self.is_simulation_running = False
        elif command == "reset":
            bus.reset_simulation.emit()
        elif command == "pause":
            bus.pause_simulation.emit()
        self.status_bar.showMessage(f"Simulation: {command}")
        if self.modes_panel:
            self.modes_panel.set_simulation_running(self.is_simulation_running)

    def _on_mode_changed(self, mode_type: str, new_mode: str):
        bus = self.simulation_manager.state_bus
        if mode_type == 'thermo_mode':
            bus.set_thermo_mode.emit(new_mode)
        elif mode_type == 'sim_type':
            self.logger.info(f"Simulation type: {new_mode}")
        else:
            self.logger.info(f"Mode changed {mode_type} -> {new_mode}")

    def _on_pneumo_param(self, name: str, value: float):
        if name == 'master_isolation_open':
            self.simulation_manager.state_bus.set_master_isolation.emit(bool(value))
        elif name == 'cv_atmo_dp':
            pass  # TODO integrate into gas network
        # Additional pneumatic parameters could be forwarded here

    # ------------------------------------------------------------------
    # Rendering Update
    # ------------------------------------------------------------------
    @Slot()
    def _update_render(self):
        """Update QML scene properties from simulation state
        
        NO direct rendering calls - only update QML properties via Qt meta-object system
        """
        if not self._qml_root_object:
            return
        
        # Update simulation info in QML overlay
        if self.current_snapshot:
            sim_text = f"Sim: {self.current_snapshot.simulation_time:.2f}s | Step: {self.current_snapshot.step_number}"
            self._qml_root_object.setProperty("simulationText", sim_text)
            
            # Update FPS display
            if self.current_snapshot.aggregates.physics_step_time > 0:
                fps = 1.0 / self.current_snapshot.aggregates.physics_step_time
                fps_text = f"FPS: {fps:.0f}"
                self._qml_root_object.setProperty("fpsText", fps_text)
        
        # Update queue stats in status bar
        stats = self.simulation_manager.get_queue_stats()
        self.queue_label.setText(f"Queue: {stats['get_count']}/{stats['put_count']}")
    
    # ------------------------------------------------------------------
    # Window Events
    # ------------------------------------------------------------------
    def showEvent(self, event):
        """Override showEvent to start SimulationManager AFTER window is visible
        
        This prevents crashes from threading issues during window creation.
        """
        super().showEvent(event)
        
        # Start simulation manager only once, after window is shown
        if not self._sim_started:
            print("\n?? Window shown - starting SimulationManager...")
            try:
                self.simulation_manager.start()
                self._sim_started = True
                print("? SimulationManager started successfully\n")
            except Exception as e:
                print(f"? Failed to start SimulationManager: {e}")
                import traceback
                traceback.print_exc()
    # ------------------------------------------------------------------
    # Preset Save/Load & Settings
    # ------------------------------------------------------------------
    def _save_preset(self):
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        last_dir = settings.value(self.SETTINGS_LAST_PRESET, str(Path.cwd()))
        file_path, _ = QFileDialog.getSaveFileName(self, "Save UI Preset", last_dir, "JSON Files (*.json)")
        if not file_path:
            return
        settings.setValue(self.SETTINGS_LAST_PRESET, str(Path(file_path).parent))
        preset = {
            'geometry': self.geometry_panel.get_parameters() if self.geometry_panel else {},
            'pneumo': self.pneumo_panel.get_parameters() if self.pneumo_panel else {},
            'modes': self.modes_panel.get_parameters() if self.modes_panel else {},
            'physics': self.modes_panel.get_physics_options() if self.modes_panel else {}
        }
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(preset, f, indent=2)
            self.status_bar.showMessage(f"Preset saved: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Preset Failed", str(e))

    def _load_preset(self):
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        last_dir = settings.value(self.SETTINGS_LAST_PRESET, str(Path.cwd()))
        file_path, _ = QFileDialog.getOpenFileName(self, "Load UI Preset", last_dir, "JSON Files (*.json)")
        if not file_path:
            return
        settings.setValue(self.SETTINGS_LAST_PRESET, str(Path(file_path).parent))
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                preset = json.load(f)
            if self.geometry_panel and 'geometry' in preset:
                self.geometry_panel.set_parameters(preset['geometry'])
            if self.pneumo_panel and 'pneumo' in preset:
                self.pneumo_panel.set_parameters(preset['pneumo'])
            if self.modes_panel and 'modes' in preset:
                for k, v in preset['modes'].items():
                    # direct set not implemented for all; simplest: log
                    self.logger.info(f"Load mode param {k}={v}")
            self.status_bar.showMessage(f"Preset loaded: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Load Preset Failed", str(e))

    def _reset_ui_layout(self):
        """Reset UI layout (safe version - checks for None docks)"""
        for dock in [self.geometry_dock, self.pneumo_dock, self.charts_dock, self.modes_dock, self.road_dock]:
            if dock:  # Check for None before calling methods
                dock.show()
        self.status_bar.showMessage("UI layout reset")

    def _restore_settings(self):
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        if geo := settings.value(self.SETTINGS_GEOMETRY):
            self.restoreGeometry(geo)
        if state := settings.value(self.SETTINGS_STATE):
            self.restoreState(state)

    def _save_settings(self):
        settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)
        settings.setValue(self.SETTINGS_GEOMETRY, self.saveGeometry())
        settings.setValue(self.SETTINGS_STATE, self.saveState())

    # ------------------------------------------------------------------
    # CSV Export (P11)
    # ------------------------------------------------------------------
    def _export_timeseries(self):
        """Export chart timeseries data to CSV"""
        from PySide6.QtCore import QStandardPaths
        from ..common import export_timeseries_csv, get_default_export_dir, ensure_csv_extension, log_export
        
        if not self.chart_widget:
            QMessageBox.warning(self, "Export", "No chart data available")
            return
        
        # Get series data from chart widget
        try:
            time, series = self.chart_widget.get_series_buffers()
            if len(time) == 0:
                QMessageBox.warning(self, "Export", "No data to export")
                return
        except AttributeError:
            QMessageBox.warning(self, "Export", "Chart widget does not support export yet")
            return
        
        # Get default directory
        default_dir = str(get_default_export_dir())
        
        # File dialog
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Timeseries CSV",
            f"{default_dir}/PneumoStabSim_timeseries.csv",
            "CSV files (*.csv);;GZip CSV (*.csv.gz)"
        )
        
        if not file_path:
            return
        
        # Ensure proper extension
        file_path = ensure_csv_extension(Path(file_path), allow_gz=True)
        
        # Prepare header
        header = ['time'] + list(series.keys())
        
        try:
            # Export
            export_timeseries_csv(time, series, file_path, header)
            
            # Log and notify
            log_export("TIMESERIES", file_path, len(time))
            self.status_bar.showMessage(f"Exported {len(time)} points to {file_path.name}")
            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(time)} data points to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))
            self.logger.error(f"Timeseries export failed: {e}")
    
    def _export_snapshots(self):
        """Export state snapshots to CSV"""
        from PySide6.QtCore import QStandardPaths
        from ..common import export_state_snapshot_csv, get_default_export_dir, ensure_csv_extension, log_export
        
        # Get snapshot buffer from simulation manager
        try:
            snapshots = self.simulation_manager.get_snapshot_buffer()
            if not snapshots or len(snapshots) == 0:
                QMessageBox.warning(self, "Export", "No snapshots available")
                return
        except AttributeError:
            QMessageBox.warning(self, "Export", "Snapshot buffer not implemented yet")
            return
        
        # Get default directory
        default_dir = str(get_default_export_dir())
        
        # File dialog
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Snapshots CSV",
            f"{default_dir}/PneumoStabSim_snapshots.csv",
            "CSV files (*.csv);;GZip CSV (*.csv.gz)"
        )
        
        if not file_path:
            return
        
        # Ensure proper extension
        file_path = ensure_csv_extension(Path(file_path), allow_gz=True)
        
        try:
            # Export
            export_state_snapshot_csv(snapshots, file_path)
            
            # Log and notify
            log_export("SNAPSHOTS", file_path, len(snapshots))
            self.status_bar.showMessage(f"Exported {len(snapshots)} snapshots to {file_path.name}")
            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(snapshots)} snapshots to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))
            self.logger.error(f"Snapshot export failed: {e}")

    # ------------------------------------------------------------------
    # Close Event
    # ------------------------------------------------------------------
    def closeEvent(self, event):
        self.logger.info("Main window closing")
        self.render_timer.stop()
        self._save_settings()
        self.simulation_manager.stop()
        event.accept()
        self.logger.info("Main window closed")