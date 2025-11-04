# Panel Modernization Report

## 1. Audit of Existing Preset Logic

- **Geometry defaults (`src/ui/panels/panel_geometry.py` & `config/constants.py`)** still define preset payloads (`standard_truck`, `light_commercial`, `heavy_truck`) that are hydrated from `app_settings.json`.  The new accordion implementation now consumes those same payloads directly from `get_geometry_presets()` instead of duplicating the data.
- **Graphics quality tab (`src/ui/panels/graphics/quality_tab.py`)** keeps an in-memory `_quality_presets` dictionary and a `_suspend_preset_sync` guard to prevent feedback loops while presets are replayed.
- **Lighting facade (`src/ui/panels/lighting/settings.py`)** exposes `LightingSettingsBridge` which already surfaces tonemap presets to QML via `list_tonemap_presets()` and `applyTonemapPreset()`.
- **Legacy QML (`assets/qml/panels/lighting/LightingTonemapPanel.qml`)** previously re-implemented the preset button layout, duplicating tooltip and selection handling.

Common threads across these modules:

1. Preset definitions originate from the JSON settings payload and must stay in sync with persisted values.
2. UI layers publish explicit "preset activated" signals alongside telemetry hooks so diagnostics can trace changes.
3. Each panel implemented bespoke guard flags to avoid recursive updates during undo/redo or preset application.

## 2. Reusable Accordion Primitives

- `SliderFieldSpec` gained a `resets_preset` flag so individual sliders can opt out of preset resets, and `_UndoCommand` now records arbitrary payloads (value + preset id) so undo/redo restores both numeric state and active preset.
- The new `PanelPreset` dataclass plus `SettingsBackedAccordionPanel.register_presets()` and `.apply_preset()` encapsulate preset orchestration, including snapshot diffing, telemetry emission, and persistence of the active preset via `SettingsManager`.
- `SettingsBackedAccordionPanel` publishes QML-facing bindings: `undoController` (constant), `presetModel` (`QVariantList`), `activePresetId` (`str`), and an `applyPreset()` slot, letting QML reuse the Python undo stack and preset store without custom glue.
- `GeometryPanelAccordion` now instantiates with `preset_settings_key="active_preset"`, loads preset definitions from `config/app_settings.json`, and updates the active preset automatically when users tweak sliders or replay undo steps.

## 3. Undo/Redo Surface

- `PanelUndoController` continues to expose Qt properties for availability state, and replay paths now drive both slider values and preset identifiers through a single command pipeline.
- `Panels.Common/PresetButtons.qml` wraps the preset list UI, optionally wiring an injected `PanelUndoController` into the shared `UndoRedoControls` header so QML surfaces get consistent undo affordances alongside preset buttons. When paired with the new `presetModel`/`activePresetId` properties, the QML delegate stays in sync with Python-driven preset changes and undo replays.
- `LightingTonemapPanel.qml` now delegates its UI to `PresetButtons`, reducing duplication and giving the QML layer immediate access to the shared undo/redo affordance.

## 4. Settings & Telemetry Integration

- Slider changes and preset activations emit `diagnostics.ui.panels.*` events, ensuring structlog-aware and standard logging environments share the same diagnostics channel.
- Active preset identifiers persist through `SettingsManager` (`current.geometry.active_preset`) so both Python and QML can recover the last selection without bespoke glue code.
- Preset application reuses `set_parameters()` under the hood, guaranteeing that any slider participating in a preset benefits from the same undo, validation, and telemetry hooks as ad-hoc edits.

## 5. Follow-up Items

- Adopt `SettingsBackedAccordionPanel` + `PanelPreset` within pneumatic, simulation, and graphics accordion panels to retire bespoke preset guards.
- Surface the shared `PresetButtons` component inside the graphics and modes QML panels once their controllers expose a `PanelUndoController` to QML.

## 6. Verification

- `pytest tests/ui/test_signals_router_connections.py`
- `pytest tests/settings/test_persistence.py`
