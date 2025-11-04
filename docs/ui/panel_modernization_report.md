# Panel Modernization Report

## 1. Audit of Existing Preset Logic

- **Geometry panel (`src/ui/panels/geometry/defaults.py`)** consolidates baseline geometry, slider ranges, and preset bundles such as `standard_truck`, `light_commercial`, and `heavy_truck`.  The presets derive from `config/app_settings.json` and expose a `PRESET_INDEX_MAP` used by options tabs.
- **Graphics quality tab (`src/ui/panels/graphics/quality_tab.py`)** builds a `_quality_presets` dictionary that mirrors the high/medium/low/ultra quality bundles.  The tab uses `_suspend_preset_sync` to guard against feedback loops when presets are applied programmatically.
- **Lighting baseline (`src/ui/panels/lighting/baseline.py`)** normalises tonemapping presets, validating payloads and emitting QML-friendly descriptors that surface inside `LightingTonemapPanel.qml`.
- **QML (`assets/qml/panels/lighting/LightingTonemapPanel.qml`)** binds to the lighting settings bridge and repeats preset buttons, mirroring the Python-side preset orchestration.

Shared themes:

1. Preset payloads always originate from the settings file to keep Python and QML in sync.
2. Both Python panels and QML wrappers use event hooks (`preset_applied`, `applyTonemapPreset`) to log telemetry and update state managers.
3. Manual guard flags (for example `_suspend_preset_sync`) are reimplemented across panels to stop recursive updates.

## 2. Reusable Accordion Primitives

- Introduced `SliderFieldSpec`, `_UndoCommand`, `PanelUndoController`, and `SettingsBackedAccordionPanel` inside `src/ui/panels_accordion.py`.  These abstractions build `ParameterSlider` widgets declaratively, hydrate values from `SettingsManager`, and automatically register undo/redo steps.
- Refactored `GeometryPanelAccordion` to inherit from the new base.  The panel now declares nine slider specs (wheelbase, track width, lever arm, etc.), emits the legacy `parameter_changed` signal, persists values to `current.geometry`, and keeps the read-only lever angle in sync via `set_read_only_value`.
- Telemetry is routed through a structlog-compatible shim so every change emits a `field.changed` event tagged with the originating panel and settings key.

## 3. Undo/Redo Surface

- `PanelUndoController` exposes Qt properties (`canUndo`, `canRedo`) and slots (`undo()`, `redo()`) that drive UI affordances and keep a replay-safe flag (`is_replaying`).
- Added `Panels.Common/UndoRedoControls.qml` to provide ready-to-use buttons plus keyboard shortcuts bound to any `PanelUndoController` instance.
- Sliders automatically push undo commands capturing old/new values; undo/redo updates both the slider widget and the persisted settings snapshot.

## 4. Settings & Telemetry Integration

- All geometry sliders now persist through `SettingsManager` using canonical keys (e.g. `current.geometry.wheelbase`).  Newly exposed `frame_mass` and `wheel_mass` fields are seeded in `config/app_settings.json` and covered by the JSON schema.
- Structured logs keep parity across structlog-enabled and standard-logging environments so diagnostics channels receive consistent payloads.

## 5. Follow-up Items

- Migrate `PneumoPanelAccordion` and other legacy accordion panels to `SettingsBackedAccordionPanel` for unified undo/redo behaviour.
- Wire `UndoRedoControls` into the QtQuick host once the panel controllers are registered with the QML engine.
