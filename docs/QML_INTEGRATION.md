# QML ↔ Python Integration

This document describes how the Qt Quick3D scene communicates with the
Python backend in PneumoStabSim after the unified plugin refactor.

## Module layout

* **QML plugin** – the `assets/qml/PneumoStabSim` directory exposes a
  self-contained module with a `qmldir`. `SimulationRoot.qml` is the
  entry point and now wires up both the reusable controllers hosted in
  the same module (`CameraController.qml`,
  `SceneEnvironmentController.qml`) and the scene graph assembly from
  `scene/SuspensionAssembly.qml`. The assembly encapsulates the frame,
  four suspension corners and the reflection probe so that all
  kinematics math lives in a single helper object. Both controllers and
  the assembly accept the `sceneBridge` payload, so every
  camera/environment/geometry change flows through Qt properties instead
  of imperative lookups. The top level `assets/qml/main.qml` simply
  instantiates `SimulationRoot` and passes the Python bridge object.
  The animation directory adds `RigAnimationController.qml`, providing
  declarative smoothing and snap thresholds for lever angles, pistons
  and frame motion so that SimulationRoot stays lean while exposing the
  new animation tuning surface to Python.
* **Python bridge** – `src/ui/scene_bridge.py` defines `SceneBridge`, a
 `QObject` with a `QVariantMap` property for every update category and a
 matching Qt signal. The bridge is injected into the QML context as the
 `pythonSceneBridge` property by both main-window implementations.

## Signal/Property routing

1. Python code pushes category dictionaries into
 `SceneBridge.dispatch_updates`.
2. The bridge updates its cached state, emits a `*Changed` signal for
 each category and finally emits `updatesDispatched` with the full
 payload.
3. `SimulationRoot.qml` listens to those signals and invokes the
 existing `apply*Updates` functions. In parallel the camera and
 environment controllers subscribe to the bridge and update their Qt
 properties, keeping aliases such as `cameraController.fov` in sync
 for any other QML consumer.
4. When the scene starts or when QML reconnects (for example after the
 widget is recreated) the helper `applySceneBridgeState()` pulls the
 cached state from the bridge and reapplies it. The controllers run
 the same helper to restore their internal values.

The old `pendingPythonUpdates` property remains as a compatibility
fallback, but the primary path is the signal/property wiring described
above.

## Type registration

`src/ui/qml_registration.py` registers the `PneumoStabSim` module name
and calls `qmlRegisterType(SceneBridge, ...)` so the Qt meta-object
information for every bridge property/signal is available even when the
bridge is instantiated from QML. The `ApplicationRunner` calls
`register_qml_types()` before a main window is instantiated, ensuring
the module metadata and bridge type are ready for Qt6.10 during scene
creation.

## Testing strategy

Integration tests create a `SceneBridge`, feed synthetic payloads and
validate the emitted Qt signals. Dedicated GUI tests instantiate the QML
scene with the offscreen platform, attach the bridge and check that both
`SimulationRoot` and the embedded controllers react to category updates.
This ensures the full Python→SceneBridge→QML route behaves as expected.
