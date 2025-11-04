# Camera HUD Diagnostics Snapshot

## Orbit Preset Inventory

The refreshed manifest (`config/orbit_presets.json`) now embeds bilingual
labels, descriptions, and metadata blocks while remaining compliant with the
validation schema in `config/schemas/orbit_presets.schema.json`. The curated
profiles cover the persisted desktop default plus three ergonomics-driven
variants:

| Preset ID  | Category      | Devices                | Notes |
|------------|---------------|------------------------|-------|
| `baseline` | Desktop       | Mouse                  | Balanced damping matching the persisted defaults. |
| `rigid`    | Desktop       | Mouse, pen tablet      | Zero inertia for CAD/CAM inspection workflows. |
| `smooth`   | Desktop       | Trackpad               | Increased damping tuned for multi-touch gestures. |
| `cinematic`| Presentation  | Controller, mouse      | Showcase preset with deliberate inertia and friction. |

`SettingsManager.get_orbit_presets()` now returns the versioned manifest, an
index map, and the default preset identifier so `SceneBridge` can attach human
readable labels to HUD telemetry updates.

## Telemetry Export (Python Bridge)

`SceneBridge` augments every camera payload with the manifest, the resolved
default preset label, and a telemetry snapshot calculated by
`CameraHudTelemetry`. QML overlays receive the same structure on startup and
for all subsequent updates, making it trivial to surface real-time camera
metrics or preset metadata. The current baseline snapshot serialised from the
bridge is outlined below:

```json
{
  "timestamp": "2025-11-04T07:48:08.323Z",
  "distance": 4.6,
  "yawDeg": 30.0,
  "pitchDeg": -20.0,
  "panX": 0.0,
  "panY": 0.0,
  "panZ": 0.0,
  "pivot": {
    "x": 0.0,
    "y": 0.0,
    "z": 0.5
  },
  "fov": 60.0,
  "speed": 1.0,
  "nearPlane": 0.08,
  "farPlane": 150.0,
  "autoRotate": false,
  "autoRotateSpeed": 8.0,
  "inertiaEnabled": true,
  "inertia": 0.4,
  "rotateSmoothing": 0.5,
  "panSmoothing": 0.5,
  "zoomSmoothing": 0.51,
  "friction": 0.2,
  "presetId": "baseline",
  "presetLabel": "Baseline",
  "motionSettlingMs": 0.0,
  "rotationDampingMs": 0.0,
  "panDampingMs": 0.0,
  "distanceDampingMs": 0.0
}
```

The QML overlay consumes the telemetry as a fallback when the live
`CameraController` state is unavailable and also surfaces the preset label. HUD
toggles (`Pivot`, `Pan`, `Angles`, `Motion`) now invoke
`safeApplyConfigChange("diagnostics.camera_hud", …)` so adjustments persist via
`SettingsManager` and echo back through the diagnostics event bus.
