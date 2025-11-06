# PneumoStabSim RHI sweep

* **Backend:** `opengl`
* **Mode:** `effects_on`
* **Command:** `QSG_INFO=1 QSG_RHI_BACKEND=opengl QSG_RHI_DEBUG_LAYER=1 QT_QPA_PLATFORM=offscreen /workspace/PneumoStabSim-Professional/.venv/bin/python3 app.py --test-mode --verbose`
* **Timestamp:** 2025-11-06 03:43:57 UTC

## Console output
```
============================================================
🚀 PNEUMOSTABSIM v4.9.5
============================================================
📊 Python 3.13 | Qt 6.10.0
🎨 Graphics: Qt Quick 3D | Backend: opengl
⏳ Initializing...
🗑️  Удален лог: PneumoStabSim_20251106_034255.log
🗑️  Удален старый run.log
INFO     | PneumoStabSim | ======================================================================
INFO     | PneumoStabSim | === START RUN: PneumoStabSim ===
INFO     | PneumoStabSim | ======================================================================
INFO     | PneumoStabSim | Python version: 3.13.3 (main, Aug 28 2025, 21:56:01) [GCC 13.3.0]
INFO     | PneumoStabSim | Platform: Linux-6.12.13-x86_64-with-glibc2.39
INFO     | PneumoStabSim | Process ID: 12299
INFO     | PneumoStabSim | Log file: /workspace/PneumoStabSim-Professional/logs/PneumoStabSim_20251106_034351.log
INFO     | PneumoStabSim | Run log: /workspace/PneumoStabSim-Professional/logs/run.log
INFO     | PneumoStabSim | Max log size: 10.0 MB
INFO     | PneumoStabSim | Backup count: 5
INFO     | PneumoStabSim | Timestamp: 2025-11-06T03:43:51.366101Z
INFO     | PneumoStabSim | PySide6 version: 6.10.0
INFO     | PneumoStabSim | NumPy version: 2.3.4
INFO     | PneumoStabSim | SciPy version: 1.16.2
Settings file: /tmp/tmpxwvb_s4m/app_settings.json [source=ENV]
INFO     | PneumoStabSim | ======================================================================
INFO     | PneumoStabSim | ============================================================
INFO     | PneumoStabSim | PneumoStabSim v4.9.5 - Application Started
INFO     | PneumoStabSim | ============================================================
INFO     | PneumoStabSim | Python: 3.13
INFO     | PneumoStabSim | Global error hooks enabled (JSON log: logs/errors/errors_20251106_034351.jsonl)
INFO     | PneumoStabSim | Qt: 6.10.0
INFO     | PneumoStabSim | Platform: linux
INFO     | PneumoStabSim | Backend: opengl
INFO     | PneumoStabSim | Console verbose mode is ENABLED
INFO     | PneumoStabSim | Logging initialized successfully
INFO     | PneumoStabSim | Verbose mode enabled
INFO     | PneumoStabSim | Configured default OpenGL surface format -> OpenGL 4.5 Core Profile
INFO     | PneumoStabSim | QApplication created and configured
INFO     | PneumoStabSim | Settings file: /tmp/tmpxwvb_s4m/app_settings.json [source=ENV]
INFO     | PneumoStabSim.GeometryPanel | ✅ Geometry loaded from app_settings.json (no code defaults)
✅ Ready!
============================================================

🧪 Test mode: auto-closing in 5 seconds...
ERROR    | PneumoStabSim | QML initialisation issue (status-missing): _qquick_widget of type QLabel does not expose status(); a fallback widget is active.
INFO     | PneumoStabSim | MainWindow created and shown
INFO     | PneumoStabSim | Test mode: auto-closing in 5 seconds

✅ Application closed (code: 0)

INFO     | PneumoStabSim | SettingsService payload persisted on exit
INFO     | PneumoStabSim | Application closed with code: 0
INFO     | PneumoStabSim | ============================================================
INFO     | PneumoStabSim | ======================================================================
INFO     | PneumoStabSim | === END RUN ===
INFO     | PneumoStabSim | Shutdown at: 2025-11-06T03:43:57.389407Z
INFO     | PneumoStabSim | ======================================================================

2025-11-06 03:43:51,885 MainWindow [INFO] MainWindow init: Qt Quick 3D (main.qml v4.3)
2025-11-06 03:43:51,885 MainWindow [INFO] SettingsManager initialized
2025-11-06 03:43:51,885 MainWindow [INFO] ProfileSettingsManager initialized
2025-11-06 03:43:51,887 IblSignalLogger [INFO] IBL Logger: Writing to logs/ibl/ibl_signals_20251106_034351.log
2025-11-06 03:43:51,888 MainWindow [INFO] EventLogger initialized
2025-11-06 03:43:51,889 MainWindow [INFO] FeedbackService initialized
2025-11-06 03:43:51,891 src.runtime.sim_loop [INFO] PhysicsWorker settings: dt=0.001000s, vsync=60.0Hz, max_steps=10, max_frame_time=0.050s, receiver=0.020m³ (MANUAL mode)
2025-11-06 03:43:51,891 MainWindow [INFO] ✅ SimulationManager created
2025-11-06 03:43:51,904 MainWindow [INFO] ✅ GeometryBridge created
2025-11-06 03:43:51,904 MainWindow [INFO] Building UI...
2025-11-06 03:43:51,905 src.ui.main_window_pkg.ui_setup [INFO]     [QML] Загрузка main.qml...
2025-11-06 03:43:51,920 src.ui.main_window_pkg.ui_setup [INFO]     [QML] Renderer API: opengl-rhi
2025-11-06 03:43:51,920 src.ui.main_window_pkg.ui_setup [INFO]     ✅ Feedback controller exposed to QML context
2025-11-06 03:43:51,930 src.ui.main_window_pkg.ui_setup [INFO]     ✅ SceneBridge exposed to QML context
2025-11-06 03:43:51,931 src.ui.main_window_pkg.ui_setup [INFO]     ✅ Lighting settings facade exposed to QML context
2025-11-06 03:43:51,932 src.ui.main_window_pkg.ui_setup [INFO]     ✅ Training presets bridge exposed to QML context
2025-11-06 03:43:51,932 src.ui.main_window_pkg.ui_setup [INFO]     ✅ Window context registered
2025-11-06 03:43:51,934 src.ui.main_window_pkg.ui_setup [INFO]     ✅ Initial graphics settings exposed to QML
2025-11-06 03:43:51,935 src.ui.main_window_pkg.ui_setup [INFO]     [QML] Загрузка сцены: main.qml
2025-11-06 03:43:52,078 src.ui.main_window_pkg.ui_setup [ERROR]     ❌ QML load failed: QML load errors:
file:///workspace/PneumoStabSim-Professional/assets/qml/main.qml:340:26: Type SimulationRoot unavailable
file:///workspace/PneumoStabSim-Professional/assets/qml/PneumoStabSim/SimulationRoot.qml:1163:2: Type Scene.SuspensionAssembly unavailable
file:///workspace/PneumoStabSim-Professional/assets/qml/scene/SuspensionAssembly.qml:379:5: Property value set multiple times
Traceback (most recent call last):
  File "/workspace/PneumoStabSim-Professional/src/ui/main_window_pkg/ui_setup.py", line 567, in _setup_qml_3d_view
    raise RuntimeError(f"QML load errors:\n{error_msg}")
RuntimeError: QML load errors:
file:///workspace/PneumoStabSim-Professional/assets/qml/main.qml:340:26: Type SimulationRoot unavailable
file:///workspace/PneumoStabSim-Professional/assets/qml/PneumoStabSim/SimulationRoot.qml:1163:2: Type Scene.SuspensionAssembly unavailable
file:///workspace/PneumoStabSim-Professional/assets/qml/scene/SuspensionAssembly.qml:379:5: Property value set multiple times
2025-11-06 03:43:52,121 MainWindow [INFO]   ✅ Central view setup
2025-11-06 03:43:52,141 src.ui.panels.pneumo [INFO] ✅ PneumoPanel: using refactored modular implementation
2025-11-06 03:43:52,219 src.ui.panels.pneumo.panel_pneumo_refactored [INFO] PneumoPanel (refactored) initializing...
2025-11-06 03:43:52,249 src.ui.panels.pneumo.panel_pneumo_refactored [INFO] PneumoPanel initialized
2025-11-06 03:43:52,420 src.ui.panels.graphics.panel_graphics_refactored [INFO] Settings file path: /tmp/tmpxwvb_s4m/app_settings.json
2025-11-06 03:43:52,428 EventLogger [INFO] [USER_CLICK] panel_graphics.click_lighting.key.cast_shadow: None → False
2025-11-06 03:43:52,430 EventLogger [INFO] [USER_CLICK] panel_graphics.click_lighting.spot.cast_shadow: None → False
2025-11-06 03:43:52,433 EventLogger [INFO] [SIGNAL_EMIT] panel_graphics.emit_scene_changed: None → {'default_clear_color': '#1b1f27', 'exposure': 1.0, 'model_base_color': '#9da3aa', 'model_metalness': 0.82, 'model_roughness': 0.42, 'scale_factor': 1.0}
2025-11-06 03:43:52,434 EventLogger [INFO] [USER_CLICK] panel_graphics.click_camera.auto_fit: None → False
2025-11-06 03:43:52,435 EventLogger [INFO] [USER_CLICK] panel_graphics.click_camera.orbit_inertia_enabled: None → False
2025-11-06 03:43:52,439 src.ui.panels.graphics.panel_graphics_refactored [INFO] ✅ Graphics settings loaded from app_settings.json
2025-11-06 03:43:52,439 src.ui.panels.graphics.panel_graphics_refactored [INFO] ✅ GraphicsPanel coordinator initialized (v3.1, centralized save-on-exit)
2025-11-06 03:43:52,502 MainWindow [INFO]   ✅ Tabs setup
2025-11-06 03:43:52,504 MainWindow [INFO]   ✅ Menus setup
2025-11-06 03:43:52,506 MainWindow [INFO]   ✅ Toolbar setup
2025-11-06 03:43:52,507 MainWindow [INFO]   ✅ Status bar setup
2025-11-06 03:43:52,508 src.ui.main_window_pkg.signals_router [INFO] ✅ GeometryPanel signals connected
2025-11-06 03:43:52,508 src.ui.main_window_pkg.signals_router [INFO] ✅ PneumoPanel signals connected
2025-11-06 03:43:52,508 src.ui.main_window_pkg.signals_router [INFO] ✅ ModesPanel signals connected
2025-11-06 03:43:52,508 src.ui.main_window_pkg.signals_router [INFO] ✅ GraphicsPanel signals connected
2025-11-06 03:43:52,509 src.ui.main_window_pkg.signals_router [INFO] ✅ Simulation signals connected
2025-11-06 03:43:52,509 src.ui.main_window_pkg.signals_router [INFO] ✅ Все сигналы подключены
2025-11-06 03:43:52,509 MainWindow [INFO]   ✅ Signals connected
2025-11-06 03:43:52,509 MainWindow [INFO]   ✅ Render timer started
2025-11-06 03:43:52,510 MainWindow [INFO]   ✅ Settings restored
2025-11-06 03:43:52,526 src.ui.main_window_pkg.state_sync [INFO] Initial full sync pushed as batch
2025-11-06 03:43:52,527 MainWindow [INFO]   ✅ Initial sync completed
2025-11-06 03:43:52,527 MainWindow [INFO] ✅ MainWindow initialization complete
2025-11-06 03:43:52,576 MainWindow [INFO] Geometry update: 20 keys
2025-11-06 03:43:57,311 src.ui.main_window_pkg.state_sync [INFO] ℹ️ No settings changes detected; skipping save
2025-11-06 03:43:57,582 src.runtime.sim_loop [INFO] Принудительная очистка PhysicsWorker завершена

```
