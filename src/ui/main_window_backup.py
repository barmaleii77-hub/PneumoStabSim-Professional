"""
Main window for PneumoStabSim application
Qt Quick 3D rendering with QQuickWidget (no createWindowContainer)
"""
from PySide6.QtWidgets import (
    QMainWindow, QStatusBar, QDockWidget, QWidget, QMenuBar, QToolBar, QLabel,
    QVBoxLayout, QFileDialog, QMessageBox, QApplication, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Slot, QSettings, QUrl, QFileInfo
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtQuickWidgets import QQuickWidget  # Используем QQuickWidget вместо QQuickView
import logging
import json
import numpy as np  # NEW: For calculations
from pathlib import Path
from typing import Optional, Dict

# NO OpenGL imports - using Qt Quick 3D instead
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

    def __init__(self, use_qml_3d: bool = True):
        super().__init__()
        
        # Store visualization backend choice
        self.use_qml_3d = use_qml_3d
        
        backend_name = "Qt Quick 3D (U-Frame PBR)" if use_qml_3d else "Legacy OpenGL"
        self.setWindowTitle(f"PneumoStabSim - {backend_name}")
        
        # Set reasonable initial size (not too large)
        self.resize(1200, 800)
        
        # Set minimum window size to prevent over-compression
        self.setMinimumSize(1000, 700)
        
        # Ensure window is in normal state
        self.setWindowState(Qt.WindowState.WindowNoState)

        # Logging
        self.logger = logging.getLogger(__name__)
        
        print("MainWindow: Creating SimulationManager...")
        
        # Simulation manager (will start AFTER window.show())
        try:
            self.simulation_manager = SimulationManager(self)
            self._sim_started = False  # Flag to ensure single start
            print("✅ SimulationManager created (not started yet)")
        except Exception as e:
            print(f"❌ SimulationManager creation failed: {e}")
            import traceback
            traceback.print_exc()
            raise

        # Current snapshot
        self.current_snapshot: Optional[StateSnapshot] = None
        self.is_simulation_running = False

        # NEW: Geometry converter for Python↔QML integration
        from .geometry_bridge import create_geometry_converter
        self.geometry_converter = create_geometry_converter()
        print("✅ GeometryBridge created for Python↔QML integration")

        # Panels references (temporarily disabled)
        self.geometry_panel: Optional[GeometryPanel] = None
        self.pneumo_panel: Optional[PneumoPanel] = None
        self.modes_panel: Optional[ModesPanel] = None
        self.road_panel: Optional[RoadPanel] = None
        self.chart_widget: Optional[ChartWidget] = None

        # Qt Quick 3D view reference
        self._qquick_widget: Optional[QQuickWidget] = None  # ? ��������
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
        """Create central visualization view (QML 3D or legacy OpenGL)"""
        print(f"    _setup_central: Creating visualization ({self.use_qml_3d and 'QML 3D' or 'legacy'})...")
        
        if self.use_qml_3d:
            self._setup_qml_3d_view()
        else:
            self._setup_legacy_opengl_view()

    def _setup_qml_3d_view(self):
        """Setup Qt Quick 3D full suspension scene"""
        print("    [QML] Loading main.qml directly for better UI integration...")
        
        try:
            # Create QQuickWidget for main.qml with UI integration
            self._qquick_widget = QQuickWidget(self)
            
            # CRITICAL: Set resize mode BEFORE loading source
            self._qquick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
            
            # Load main.qml directly (with UI integration)
            qml_path = Path("assets/qml/main.qml")
            if not qml_path.exists():
                raise FileNotFoundError(f"QML file not found: {qml_path.absolute()}")
            
            qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
            print(f"    Loading main.qml: {qml_url.toString()}")
            
            self._qquick_widget.setSource(qml_url)
            
            # Check for QML errors
            if self._qquick_widget.status() == QQuickWidget.Status.Error:
                errors = self._qquick_widget.errors()
                error_msg = "\n".join(str(e) for e in errors)
                raise RuntimeError(f"QML errors:\n{error_msg}")
            
            # Get root object for property access
            self._qml_root_object = self._qquick_widget.rootObject()
            if not self._qml_root_object:
                raise RuntimeError("Failed to get QML root object")
            
            print("    [OK] main.qml loaded successfully")
            
            # DEBUG: Check what object we got
            print(f"    [DEBUG] QML root object type: {type(self._qml_root_object)}")
            print(f"    [DEBUG] QML root object class: {self._qml_root_object.__class__.__name__ if self._qml_root_object else 'None'}")
            
            # DEBUG: Try to list all properties
            try:
                from PySide6.QtCore import QMetaObject
                meta = self._qml_root_object.metaObject()
                print(f"    [DEBUG] QML object has {meta.propertyCount()} properties:")
                for i in range(meta.propertyCount()):
                    prop = meta.property(i)
                    print(f"       - {prop.name()}")
                
                print(f"    [DEBUG] QML object has {meta.methodCount()} methods:")
                for i in range(meta.methodCount()):
                    method = meta.method(i)
                    print(f"       - {method.name().data().decode('utf-8')}")
            except Exception as e:
                print(f"    [WARNING] Could not introspect QML object: {e}")
            
            # Set as central widget
            self.setCentralWidget(self._qquick_widget)
            
            print("    [OK] main.qml set as central widget with UI integration")
            
        except Exception as e:
            print(f"    [ERROR] main.qml loading failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to SuspensionSceneHost
            print("    [FALLBACK] Falling back to SuspensionSceneHost...")
            try:
                from .qml_host import SuspensionSceneHost
                self._qquick_widget = SuspensionSceneHost(self)
                self.setCentralWidget(self._qquick_widget)
                self._qml_root_object = self._qquick_widget.rootObject()
                print("    [OK] Fallback to SuspensionSceneHost successful")
            except Exception as e2:
                print(f"    [ERROR] Fallback also failed: {e2}")
                # Final fallback to simple label
                fallback = QLabel(
                    "3D Scene Loading Failed\n\n"
                    "Both main.qml and SuspensionSceneHost failed to load.\n"
                    "Check console for detailed errors."
                )
                fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
                fallback.setStyleSheet("background: #1a1a2e; color: #ff6b6b; font-size: 14px; padding: 20px;")
                self.setCentralWidget(fallback)
                self._qquick_widget = None
                print("    [WARNING] Using fallback widget")


    def _setup_legacy_opengl_view(self):
        """Setup legacy OpenGL widget (existing main.qml scene)"""
        print("    _setup_legacy_opengl_view: Loading legacy QML...")
        
        try:
            # Create QQuickWidget for legacy Qt Quick 3D content
            self._qquick_widget = QQuickWidget(self)
            
            # CRITICAL: Set resize mode BEFORE loading source
            self._qquick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
            
            # Load legacy QML file
            qml_path = Path("assets/qml/main.qml")
            if not qml_path.exists():
                raise FileNotFoundError(f"QML file not found: {qml_path.absolute()}")
            
            qml_url = QUrl.fromLocalFile(str(qml_path.absolute()))
            print(f"    Loading legacy QML: {qml_url.toString()}")
            
            self._qquick_widget.setSource(qml_url)
            
            # Check for QML errors
            if self._qquick_widget.status() == QQuickWidget.Status.Error:
                errors = self._qquick_widget.errors()
                error_msg = "\n".join(str(e) for e in errors)
                raise RuntimeError(f"QML errors:\n{error_msg}")
            
            # Get root object for property access
            self._qml_root_object = self._qquick_widget.rootObject()
            if not self._qml_root_object:
                raise RuntimeError("Failed to get QML root object")
            
            print("    ✅ Legacy QML loaded successfully")
            
            # Set as central widget
            self.setCentralWidget(self._qquick_widget)
            
            print("    ✅ Legacy Qt Quick 3D view set as central widget")
            
        except Exception as e:
            print(f"    ❌ Legacy Qt Quick 3D view creation failed: {e}")
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
            self._qquick_widget = None
            print("    ⚠️  Using fallback widget")

    def _setup_docks(self):
        """Create and place dock panels with proper layout"""
        print("    _setup_docks: Creating panels...")
        
        # IMPORTANT: Do NOT use splitDockWidget - it causes overlaps
        # Instead, rely on Qt's automatic dock widget placement
        
        # Create geometry panel (left side)
        self.geometry_dock = QDockWidget("Geometry", self)
        self.geometry_dock.setObjectName("GeometryDock")
        self.geometry_panel = GeometryPanel(self)
        self.geometry_dock.setWidget(self.geometry_panel)
        
        # Set reasonable size constraints for left panels
        self.geometry_dock.setMinimumWidth(200)
        self.geometry_dock.setMaximumWidth(350)
        
        # Allow vertical resize but with limits
        self.geometry_panel.setMinimumHeight(200)
        
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.geometry_dock)
        print("      ? Geometry panel created")
        
        # Create pneumatics panel (left side, TABIFIED with geometry)
        self.pneumo_dock = QDockWidget("Pneumatics", self)
        self.pneumo_dock.setObjectName("PneumaticsDock")
        self.pneumo_panel = PneumoPanel(self)
        self.pneumo_dock.setWidget(self.pneumo_panel)
        
        self.pneumo_dock.setMinimumWidth(200)
        self.pneumo_dock.setMaximumWidth(350)
        self.pneumo_panel.setMinimumHeight(200)
        
        # TABIFY instead of stacking to save space
        self.tabifyDockWidget(self.geometry_dock, self.pneumo_dock)
        print("      ? Pneumatics panel created (tabified)")
        
        # Create charts panel (right side)
        self.charts_dock = QDockWidget("Charts", self)
        self.charts_dock.setObjectName("ChartsDocker")
        self.chart_widget = ChartWidget(self)
        self.charts_dock.setWidget(self.chart_widget)
        
        self.charts_dock.setMinimumWidth(300)
        self.charts_dock.setMaximumWidth(500)
        self.chart_widget.setMinimumHeight(250)
        
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.charts_dock)
        print("      ? Charts panel created")
        
        # Create modes panel (right side, TABIFIED with charts)
        self.modes_dock = QDockWidget("Simulation & Modes", self)
        self.modes_dock.setObjectName("ModesDock")
        self.modes_panel = ModesPanel(self)
        self.modes_dock.setWidget(self.modes_panel)
        
        self.modes_dock.setMinimumWidth(300)
        self.modes_dock.setMaximumWidth(500)
        self.modes_panel.setMinimumHeight(200)
        
        # TABIFY to save space
        self.tabifyDockWidget(self.charts_dock, self.modes_dock)
        print("      ? Modes panel created (tabified)")
        
        # Create road profiles panel (bottom, FLOATING or HIDDEN by default)
        self.road_dock = QDockWidget("Road Profiles", self)
        self.road_dock.setObjectName("RoadDock")
        self.road_panel = RoadPanel(self)
        self.road_dock.setWidget(self.road_panel)
        
        self.road_dock.setMinimumHeight(150)
        self.road_dock.setMaximumHeight(250)
        
        # Start as floating or hidden to avoid overlap
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.road_dock)
        self.road_dock.setFloating(False)
        self.road_dock.hide()  # Hidden by default - user can show via View menu
        print("      ? Road panel created (hidden by default)")
        
        # Raise first tab in each group to make them visible
        self.geometry_dock.raise_()
        self.charts_dock.raise_()
        
        # Set corner policies to give more space to central widget
        self.setCorner(Qt.Corner.TopLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.TopRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)
        self.setCorner(Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)
        
        # Connect panel signals
        self._wire_panel_signals()
        print("    ? Panels created and wired")

    def _wire_panel_signals(self):
        """Connect panel signals to simulation/state bus"""
        bus = self.simulation_manager.state_bus

        # Geometry updates -> 3D SCENE GEOMETRY CHANGES (MAIN!)
        if self.geometry_panel:
            self.geometry_panel.parameter_changed.connect(
                lambda name, val: [
                    self.logger.info(f"Geometry param {name}={val}"),
                    print(f"🔧 GeometryPanel signal: {name}={val}")
                ])
            # NEW: Connect geometry_changed signal for 3D scene updates
            self.geometry_panel.geometry_changed.connect(self._on_geometry_changed)
            print("✅ GeometryPanel geometry_changed signal connected")

        # Pneumatic panel -> send thermo mode and master isolation ONLY (NO GEOMETRY!)
        if self.pneumo_panel:
            self.pneumo_panel.mode_changed.connect(self._on_mode_changed)
            self.pneumo_panel.parameter_changed.connect(self._on_pneumo_param)
            # REMOVED: self.pneumo_panel.geometry_changed.connect(self._on_geometry_changed)
            print("✅ PneumoPanel signals connected (NO geometry)")

        # Modes panel -> simulation control + modes + ANIMATION
        if self.modes_panel:
            self.modes_panel.simulation_control.connect(self._on_sim_control)
            self.modes_panel.mode_changed.connect(self._on_mode_changed)
            self.modes_panel.parameter_changed.connect(
                lambda n, v: self.logger.debug(f"Road/global param {n}={v}"))
            # NEW: Connect animation_changed signal for animation parameters
            self.modes_panel.animation_changed.connect(self._on_animation_changed)
            print("✅ ModesPanel animation_changed signal connected")

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
        file_menu.addAction(load_preset_act)  # FIXED: was load_ppreset_act
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
        toolbar.setObjectName("MainToolbar")  # For saveState/restoreState
        toolbar.setMovable(True)
        
        start_act = QAction("Start", self)
        stop_act = QAction("Stop", self)
        pause_act = QAction("Pause", self)
        reset_act = QAction("Reset", self)
        
        # Add toggle panels action
        toggle_panels_act = QAction("Toggle Panels", self)
        toggle_panels_act.setCheckable(True)
        toggle_panels_act.setChecked(True)
        toggle_panels_act.toggled.connect(self._toggle_all_panels)
        
        start_act.triggered.connect(lambda: self._on_sim_control("start"))
        stop_act.triggered.connect(lambda: self._on_sim_control("stop"))
        pause_act.triggered.connect(lambda: self._on_sim_control("pause"))
        reset_act.triggered.connect(lambda: self._on_sim_control("reset"))
        
        toolbar.addActions([start_act, stop_act, pause_act, reset_act])
        toolbar.addSeparator()
        toolbar.addAction(toggle_panels_act)
        
        # Prevent toolbar from taking too much space
        toolbar.setMaximumHeight(50)

    def _toggle_all_panels(self, visible: bool):
        """Toggle visibility of all dock panels to show/hide 3D view"""
        for dock in [self.geometry_dock, self.pneumo_dock, self.charts_dock, 
                     self.modes_dock, self.road_dock]:
            if dock:
                dock.setVisible(visible)
        
        status_msg = "Panels shown" if visible else "Panels hidden (3D view visible)"
        self.status_bar.showMessage(status_msg)

    def _setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create status bar widgets with reasonable sizes
        self.sim_time_label = QLabel("Sim Time: 0.000s")
        self.sim_time_label.setMinimumWidth(120)
        
        self.step_count_label = QLabel("Steps: 0")
        self.step_count_label.setMinimumWidth(80)
        
        self.fps_label = QLabel("Physics FPS: 0")
        self.fps_label.setMinimumWidth(100)
        
        self.realtime_label = QLabel("RT: 1.00x")
        self.realtime_label.setMinimumWidth(80)
        
        self.queue_label = QLabel("Queue: 0/0")
        self.queue_label.setMinimumWidth(100)
        
        # P13 Kinematics display
        self.kinematics_label = QLabel("alpha: 0.0deg | s: 0.0mm | V_h: 0cm3 | V_r: 0cm3")
        self.kinematics_label.setToolTip("Lever angle (alpha), Cylinder stroke (s), Head/Rod volumes")
        self.kinematics_label.setMinimumWidth(300)
        
        for w in [self.sim_time_label, self.step_count_label, self.fps_label, 
                  self.queue_label, self.realtime_label, self.kinematics_label]:
            self.status_bar.addPermanentWidget(w)
        
        self.status_bar.showMessage("Ready")
        
        # Prevent status bar from being too tall
        self.status_bar.setMaximumHeight(30)

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
            
            # NEW: Update 3D scene with full simulation state (including piston positions!)
            self._update_3d_scene_from_snapshot(snapshot)
            
        if self.chart_widget:
            self.chart_widget.update_from_snapshot(snapshot)

    @Slot(str)
    def _on_physics_error(self, msg: str):
        """Handle physics error messages from simulation engine
        
        Args:
            msg: Error message from physics engine
        """
        self.status_bar.showMessage(f"Physics Error: {msg}")
        self.logger.error(f"Physics engine error: {msg}")
        
        # Optionally show error dialog for critical errors
        if "CRITICAL" in msg.upper() or "FATAL" in msg.upper():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Physics Engine Error",
                f"Critical error in physics simulation:\n\n{msg}\n\n"
                "Simulation may be unstable. Consider resetting."
            )

    def _update_3d_scene_from_snapshot(self, snapshot: StateSnapshot):
        """Update 3D scene with full simulation state including piston positions
        
        Args:
            snapshot: Current simulation state snapshot
        """
        if not self._qml_root_object:
            return  # QML not loaded yet
        
        try:
            # Get animation parameters from QML properties (set by ModesPanel)
            amplitude = self._qml_root_object.property("userAmplitude") or 8.0
            frequency = self._qml_root_object.property("userFrequency") or 1.0
            phase_global = self._qml_root_object.property("userPhaseGlobal") or 0.0
            phase_fl = self._qml_root_object.property("userPhaseFL") or 0.0
            phase_fr = self._qml_root_object.property("userPhaseFR") or 0.0
            phase_rl = self._qml_root_object.property("userPhaseRL") or 0.0
            phase_rr = self._qml_root_object.property("userPhaseRR") or 0.0
            
            # Cache last parameters to detect changes
            if not hasattr(self, '_last_animation_params'):
                self._last_animation_params = {}
            
            current_params = {
                'amplitude': amplitude,
                'frequency': frequency,
                'phase_global': phase_global
            }
            
            # Log only when parameters actually change
            if current_params != self._last_animation_params:
                print(f"📊 Animation params: Amp={amplitude:.1f}° Freq={frequency:.2f}Hz Phase={phase_global:.0f}°")
                self._last_animation_params = current_params
            
            # Use simulation time for smooth animation
            import time
            t = time.time()
            
            # Calculate angles with user-controlled parameters
            # Formula: amplitude * sin(2π * frequency * time + phase)
            omega = 2.0 * np.pi * frequency
            
            corners_data = {
                'fl': {
                    'leverAngle': amplitude * np.sin(omega * t + np.deg2rad(phase_global + phase_fl)),
                    'cylinderState': None
                },
                'fr': {
                    'leverAngle': amplitude * np.sin(omega * t + np.deg2rad(phase_global + phase_fr)),
                    'cylinderState': None
                },
                'rl': {
                    'leverAngle': amplitude * np.sin(omega * t + np.deg2rad(phase_global + phase_rl)),
                    'cylinderState': None
                },
                'rr': {
                    'leverAngle': amplitude * np.sin(omega * t + np.deg2rad(phase_global + phase_rr)),
                    'cylinderState': None
                }
            }
            
            # CRITICAL: Calculate piston positions using GeometryBridge!
            piston_positions = {}
            lever_angles = {}
            
            for corner, data in corners_data.items():
                angle = data['leverAngle']
                lever_angles[corner] = angle  # Store for QML update
                
                # Use GeometryBridge to calculate CORRECT piston position from angle
                if hasattr(self, 'geometry_converter'):
                    corner_3d = self.geometry_converter.get_corner_3d_coords(
                        corner, angle, None  # No physics state, pure geometry
                    )
                    piston_positions[corner] = corner_3d.get('pistonPositionMm', 125.0)
                else:
                    # Fallback without GeometryBridge
                    piston_ratio = 0.5 + angle / 20.0
                    piston_ratio = np.clip(piston_ratio, 0.1, 0.9)
                    piston_positions[corner] = piston_ratio * 250.0
            
            # Update animation time in QML (for smooth interpolation if needed)
            if hasattr(snapshot, 'simulation_time'):
                self._qml_root_object.setProperty("animationTime", snapshot.simulation_time)
            
            # CRITICAL: Update lever angles FIRST (so j_rod positions are correct)
            from PySide6.QtCore import QMetaObject, Q_ARG, Qt
            
            # WORKAROUND: Set angles directly via properties instead of method call
            # This is more reliable than invokeMethod for simple value updates
            for corner, angle in lever_angles.items():
                prop_name = f"{corner}_angle"
                self._qml_root_object.setProperty(prop_name, float(angle))
            
            # CRITICAL: Update piston positions SECOND (after angles are set)
            if piston_positions:
                success_pistons = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "updatePistonPositions",
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", piston_positions)
                )
                
                if not success_pistons:
                    self.logger.warning("Failed to invoke updatePistonPositions() in QML")
                
        except Exception as e:
            self.logger.error(f"Failed to update 3D scene from snapshot: {e}")
            import traceback
            traceback.print_exc()

    # Panel signal handlers
    def _on_sim_control(self, command: str):
        bus = self.simulation_manager.state_bus
        if command == "start":
            bus.start_simulation.emit()
            self.is_simulation_running = True
            # NEW: Start animation in QML
            if self._qml_root_object:
                self._qml_root_object.setProperty("isRunning", True)
                print("✅ QML animation STARTED")
        elif command == "stop":
            bus.stop_simulation.emit()
            self.is_simulation_running = False
            # NEW: Stop animation in QML
            if self._qml_root_object:
                self._qml_root_object.setProperty("isRunning", False)
                print("✅ QML animation STOPPED")
        elif command == "reset":
            bus.reset_simulation.emit()
            # NEW: Reset animation time
            if self._qml_root_object:
                self._qml_root_object.setProperty("animationTime", 0.0)
                print("✅ QML animation RESET")
        elif command == "pause":
            bus.pause_simulation.emit()
            # NEW: Pause animation
            if self._qml_root_object:
                self._qml_root_object.setProperty("isRunning", False)
                print("✅ QML animation PAUSED")
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
    
    def _on_geometry_changed(self, geometry_params: dict):
        """Handle geometry parameter changes from UI panels
        
        Args:
            geometry_params: Dictionary with geometry parameters from UI
        """
        print(f"═══════════════════════════════════════════════")
        print(f"📥 MainWindow: Received geometry_changed signal")
        print(f"   Parameters received:")
        for key, val in geometry_params.items():
            print(f"      {key}: {val}")
        print(f"═══════════════════════════════════════════════")
        
        self.logger.info(f"Geometry changed: {geometry_params}")
        
        # Update QML scene directly if available
        if self._qml_root_object:
            try:
                print(f"🔧 Attempting to update QML using QMetaObject.invokeMethod()...")
                
                # Use QMetaObject.invokeMethod() to call QML function
                from PySide6.QtCore import QMetaObject, Q_ARG, Qt
                
                # In PySide6, dict is automatically converted to JS object
                # No need for QVariant wrapper
                success = QMetaObject.invokeMethod(
                    self._qml_root_object,
                    "updateGeometry",
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", geometry_params)  # Pass dict directly
                )
                
                if success:
                    print(f"✅ QML updateGeometry() called successfully via invokeMethod")
                    self.status_bar.showMessage("Geometry updated in QML scene")
                else:
                    print(f"❌ QML updateGeometry() call failed")
                    # Fallback to individual properties
                    self._set_geometry_properties_fallback(geometry_params)
                    
            except Exception as e:
                print(f"═══════════════════════════════════════════════")
                print(f"❌ QML geometry update FAILED!")
                print(f"   Error: {e}")
                print(f"═══════════════════════════════════════════════")
                self.logger.error(f"QML geometry update failed: {e}")
                self.status_bar.showMessage(f"Geometry update failed: {e}")
                import traceback
                traceback.print_exc()
                
                # Fallback to individual properties
                self._set_geometry_properties_fallback(geometry_params)
        else:
            print(f"═══════════════════════════════════════════════")
            print(f"❌ MainWindow: QML root object is None!")
            print(f"   Cannot update geometry")
            print(f"═══════════════════════════════════════════════")
    
    def _set_geometry_properties_fallback(self, geometry_params: dict):
        """Fallback: Set individual QML properties directly
        
        Args:
            geometry_params: Dictionary with geometry parameters
        """
        print(f"🔧 Fallback: Setting individual QML properties...")
        
        prop_count = 0
        
        if 'frameLength' in geometry_params:
            self._qml_root_object.setProperty("userFrameLength", geometry_params['frameLength'])
            print(f"   ✅ Set userFrameLength = {geometry_params['frameLength']}")
            prop_count += 1
        
        if 'frameHeight' in geometry_params:
            self._qml_root_object.setProperty("userFrameHeight", geometry_params['frameHeight'])
            print(f"   ✅ Set userFrameHeight = {geometry_params['frameHeight']}")
            prop_count += 1
        
        if 'frameBeamSize' in geometry_params:
            self._qml_root_object.setProperty("userBeamSize", geometry_params['frameBeamSize'])
            print(f"   ✅ Set userBeamSize = {geometry_params['frameBeamSize']}")
            prop_count += 1
        
        if 'leverLength' in geometry_params:
            self._qml_root_object.setProperty("userLeverLength", geometry_params['leverLength'])
            print(f"   ✅ Set userLeverLength = {geometry_params['leverLength']}")
            prop_count += 1
        
        if 'cylinderBodyLength' in geometry_params:
            self._qml_root_object.setProperty("userCylinderLength", geometry_params['cylinderBodyLength'])
            print(f"   ✅ Set userCylinderLength = {geometry_params['cylinderBodyLength']}")
            prop_count += 1
        
        # NEW: Additional parameters
        if 'trackWidth' in geometry_params:
            self._qml_root_object.setProperty("userTrackWidth", geometry_params['trackWidth'])
            print(f"   ✅ Set userTrackWidth = {geometry_params['trackWidth']}")
            prop_count += 1
        
        if 'frameToPivot' in geometry_params:
            self._qml_root_object.setProperty("userFrameToPivot", geometry_params['frameToPivot'])
            print(f"   ✅ Set userFrameToPivot = {geometry_params['frameToPivot']}")
            prop_count += 1
        
        if 'rodPosition' in geometry_params:
            self._qml_root_object.setProperty("userRodPosition", geometry_params['rodPosition'])
            print(f"   ✅ Set userRodPosition = {geometry_params['rodPosition']}")
            prop_count += 1
        
        if 'boreHead' in geometry_params:
            self._qml_root_object.setProperty("userBoreHead", geometry_params['boreHead'])
            print(f"   ✅ Set userBoreHead = {geometry_params['boreHead']}")
            prop_count += 1
        
        if 'boreRod' in geometry_params:
            self._qml_root_object.setProperty("userBoreRod", geometry_params['boreRod'])
            print(f"   ✅ Set userBoreRod = {geometry_params['boreRod']}")
            prop_count += 1
        
        if 'rodDiameter' in geometry_params:
            self._qml_root_object.setProperty("userRodDiameter", geometry_params['rodDiameter'])
            print(f"   ✅ Set userRodDiameter = {geometry_params['rodDiameter']}")
            prop_count += 1
        
        if 'pistonThickness' in geometry_params:
            self._qml_root_object.setProperty("userPistonThickness", geometry_params['pistonThickness'])
            print(f"   ✅ Set userPistonThickness = {geometry_params['pistonThickness']}")
            prop_count += 1
        
        self.status_bar.showMessage(f"Geometry properties updated ({prop_count} properties)")
        print(f"✅ Set {prop_count} QML properties successfully")
        print(f"═══════════════════════════════════════════════")
    
    def _on_animation_changed(self, animation_params: dict):
        """Handle animation parameter changes from ModesPanel
        
        Args:
            animation_params: Dictionary with animation parameters (amplitude, frequency, phases)
        """
        self.logger.info(f"Animation changed: {animation_params}")
        
        # Update QML scene animation parameters if available
        if self._qml_root_object:
            try:
                print(f"🔧 Setting QML animation properties: {animation_params}")
                
                # Set animation properties directly (no function call needed - QML will react via property bindings)
                if 'amplitude' in animation_params:
                    # Convert amplitude from meters to degrees for lever rotation
                    amplitude_deg = animation_params['amplitude'] * 1000 / 10  # Scale factor for visual effect
                    self._qml_root_object.setProperty("userAmplitude", amplitude_deg)
                    print(f"   ✅ Set userAmplitude = {amplitude_deg} deg")
                
                if 'frequency' in animation_params:
                    self._qml_root_object.setProperty("userFrequency", animation_params['frequency'])
                    print(f"   ✅ Set userFrequency = {animation_params['frequency']} Hz")
                
                if 'phase' in animation_params:
                    self._qml_root_object.setProperty("userPhaseGlobal", animation_params['phase'])
                    print(f"   ✅ Set userPhaseGlobal = {animation_params['phase']} deg")
                
                if 'lf_phase' in animation_params:
                    self._qml_root_object.setProperty("userPhaseFL", animation_params['lf_phase'])
                    print(f"   ✅ Set userPhaseFL = {animation_params['lf_phase']} deg")
                
                if 'rf_phase' in animation_params:
                    self._qml_root_object.setProperty("userPhaseFR", animation_params['rf_phase'])
                    print(f"   ✅ Set userPhaseFR = {animation_params['rf_phase']} deg")
                
                if 'lr_phase' in animation_params:
                    self._qml_root_object.setProperty("userPhaseRL", animation_params['lr_phase'])
                    print(f"   ✅ Set userPhaseRL = {animation_params['lr_phase']} deg")
                
                if 'rr_phase' in animation_params:
                    self._qml_root_object.setProperty("userPhaseRR", animation_params['rr_phase'])
                    print(f"   ✅ Set userPhaseRR = {animation_params['rr_phase']} deg")
                
                self.status_bar.showMessage("Animation properties updated")
                print(f"✅ QML animation properties set successfully")
                    
            except Exception as e:
                self.logger.error(f"QML animation update failed: {e}")
                self.status_bar.showMessage(f"Animation update failed: {e}")
                import traceback
                traceback.print_exc()

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
            print("\n🚀 Window shown - starting SimulationManager...")
            try:
                self.simulation_manager.start()
                self._sim_started = True
                print("✅ SimulationManager started successfully\n")
            except Exception as e:
                print(f"❌ Failed to start SimulationManager: {e}")
                import traceback
                traceback.print_exc()
    
    def resizeEvent(self, event):
        """Override resizeEvent to handle window resizing gracefully"""
        super().resizeEvent(event)
        
        # Throttle resize updates to prevent performance issues
        if not hasattr(self, '_resize_timer'):
            self._resize_timer = QTimer(self)
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self._handle_resize_complete)
        
        # Restart timer on each resize event
        self._resize_timer.stop()
        self._resize_timer.start(100)  # Wait 100ms after last resize
    
    def _handle_resize_complete(self):
        """Called after resize operation completes"""
        # Force update of QML widget
        if self._qquick_widget:
            self._qquick_widget.update()
        
        # Log new size for debugging
        new_size = self.size()
        self.logger.debug(f"Window resized to: {new_size.width()}x{new_size.height()}")

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