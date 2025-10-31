# CODEX Tasking — HDR asset migration & settings integrity

## Project context
The Qt Quick 3D scene is driven from Python via `SceneBridge` and the unified
`SimulationRoot.qml`. Graphics parameters, materials, environment toggles and
geometry defaults must come from `config/app_settings.json`; validation is
performed in Python (`EnvironmentTab`, `environment_schema.py`) before QML
controllers (`SceneEnvironmentController.qml`, `RealismEnvironment.qml`,
`PostEffects.qml`) are fed batched updates.

## Blocking issues discovered
1. **Hard-coded environment defaults bypass settings.**
   * `RealismEnvironment.qml` bakes in booleans, floats and colors for skybox,
     tonemapping, AO, bloom, fog, vignette, etc., instead of binding to the
     Python-provided settings object. No guard exists when values are missing or
     malformed. 【F:assets/qml/environment/RealismEnvironment.qml†L5-L143】
   * `SceneEnvironmentController.qml` mirrors the same defaults for
     antialiasing, IBL toggles, tonemapping, dithering, etc., exposing hard-coded
     strings/numbers that diverge from `config/app_settings.json`. 【F:assets/qml/effects/SceneEnvironmentController.qml†L41-L141】
   * `PostEffects.qml` sets bloom/SSAO/DOF strengths and shader toggles directly
     inside the component, again ignoring persisted values. 【F:assets/qml/effects/PostEffects.qml†L41-L162】
   * The suspension assembly creates a reflection probe with fixed padding,
     quality and refresh policy, rather than reading the saved reflection
     configuration and warning when the settings section is absent. 【F:assets/qml/scene/SuspensionAssembly.qml†L43-L199】
   * `SharedMaterials.qml` carries inline fallback colours and PBR parameters,
     contradicting the “no code defaults” rule and blocking texture-based
     authoring. 【F:assets/qml/scene/SharedMaterials.qml†L148-L239】

2. **UI controls ignore user-defined ranges and last-saved assets.**
   * `EnvironmentTab` instantiates every `LabeledSlider` with baked min/max/step
     tuples. The limits in `environment_schema.py` are also hard-coded, preventing
     users from adjusting ranges through settings metadata. 【F:src/ui/panels/graphics/environment_tab.py†L64-L220】【F:src/ui/environment_schema.py†L55-L141】
   * `LabeledSlider` itself has no pathway to load dynamic ranges from
     configuration, so any future additions will repeat the violation. 【F:src/ui/panels/graphics/widgets.py†L69-L114】
   * `materials_tab.py` preselects the first discovered texture, overriding the
     stored `texture_path` and forcing a “secret” default whenever new assets are
     added. 【F:src/ui/panels/graphics/materials_tab.py†L82-L95】

3. **Texture pipeline still assumes “no external textures”.**
   * The comment in `SharedMaterials.qml` explicitly states that only parameteric
     materials without textures are supported, conflicting with the new HDR/texture
     migration goal. 【F:assets/qml/scene/SharedMaterials.qml†L5-L24】
   * While `materials_tab.py` can browse textures, there is no validation or
     graceful degradation when the saved texture path disappears—UI silently
     resets to the first file. 【F:src/ui/panels/graphics/materials_tab.py†L240-L320】

## Required corrections for CODEX
1. **Settings-driven bindings.**
   * Replace hard-coded literals in the QML controllers with bindings that source
     values from the injected settings maps. When a key is missing or validation
     fails, emit a warning through the structured logger and present a UI alert
     instead of silently falling back.
   * Extend `SceneEnvironmentController` to push validated values into
     `RealismEnvironment`/`PostEffects` and propagate acknowledgements back via
     `SceneBridge.updatesDispatched`.
   * Promote reflection probe configuration, HDR exposure and AO sampling to the
     settings payload; ensure `SuspensionAssembly` reads SI units, converts to
     scene scale, and logs when defaults are substituted.

2. **Dynamic range metadata.**
   * Teach `environment_schema` and `EnvironmentTab` to query slider/spinbox
     definitions from settings metadata (`config/constants.py` or a new
     `graphics.ui_ranges` section). Allow the user to adjust min/max/step values
     at runtime, validate them, and persist the chosen ranges.
   * Generalise `LabeledSlider` so ranges and units come from a `QuantityDefinition`
     provided at construction, populated from settings instead of literals.

3. **Texture workflow resilience.**
   * Remove the “no external textures” assumption, load texture slots from
     settings, and surface missing-file errors in the UI (show dash, disable
     bindings, log warning).
   * Ensure the materials panel preserves the last-saved texture path and only
     auto-selects a discovered asset when the saved value is empty and the user
     explicitly requests a reset.

## Acceptance criteria
- All tunable values for environment, materials, reflection probe and post
  effects originate from validated settings; QML components emit explicit
  warnings whenever fallback values are used.
- UI sliders/spinboxes reflect user-configured ranges and update instantly when
  ranges change without requiring an application restart.
- Texture and HDR pickers respect persisted selections, degrade gracefully when
  files disappear, and never inject hidden defaults.
- Full regression suite passes (`make check`) and the Qt Quick 3D demo starts
  with the last-saved visual state.
