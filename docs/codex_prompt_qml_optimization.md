# Prompt: QML Rendering Overhaul for PneumoStabSim-Professional

You are Codex (gpt-5-codex), assisting on PneumoStabSim-Professional. Optimise the QML rendering stack, upgrade visual fidelity (PBR/HDR/DOF), and modernise animation components while preserving the existing Python↔QML bridge.

## Project context
- Entry point: `assets/qml/main.qml` loads `PneumoStabSim/SimulationRoot.qml` when the `pythonSceneBridge` context property is available, otherwise falls back to `SimulationFallbackRoot.qml`.
- `SimulationRoot` orchestrates the full hydraulic rig scene. It exposes batched update slots for geometry, lighting, animation, diagnostics, and keeps Python-driven state in properties like `pythonAnimationActive`, `lightingState`, and `geometryState`.【F:assets/qml/PneumoStabSim/SimulationRoot.qml†L1-L120】【F:assets/qml/PneumoStabSim/SimulationRoot.qml†L680-L832】
- Shared PBR materials are declared in `assets/qml/scene/SharedMaterials.qml` and referenced by rig components. Parameters default from `initialSharedMaterials` provided via SceneBridge.【F:assets/qml/scene/SharedMaterials.qml†L1-L120】
- Post effects live in `assets/qml/effects/PostEffects.qml` (Bloom, SSAO, Depth of Field, Motion Blur) and feed `View3D.effects`. Scene-wide HDR, IBL, AA, and dithering settings are managed by `assets/qml/effects/SceneEnvironmentController.qml`.【F:assets/qml/effects/PostEffects.qml†L1-L80】【F:assets/qml/effects/SceneEnvironmentController.qml†L1-L140】
- The Python side exposes `pythonSceneBridge` through `src/ui/qml_host.py` and `src/ui/main_window_pkg/ui_setup.py`. Updates are dispatched by `src/ui/scene_bridge.py`, which aggregates categories (geometry, lighting, animation, diagnostics) and emits Qt signals consumed by QML helpers like `applySceneBridgeState()`.【F:src/ui/qml_host.py†L30-L80】【F:src/ui/main_window_pkg/ui_setup.py†L220-L350】【F:src/ui/scene_bridge.py†L1-L200】

## Goals
1. **Restructure QML modules**
   - Extract reusable rig subcomponents (frame, pistons, levers, diagnostics overlays) into focused QML files under `assets/qml/PneumoStabSim/` or `assets/qml/components/`.
   - Replace ad-hoc property bags with typed helper objects or single-responsibility components. Keep batched update entry points (`applyBatchedUpdates`, `applySceneBridgeState`) stable for Python callers.
   - Introduce consistent naming (`FrameAssembly`, `CylinderRig`, `RigAnimationController`) and register them in `qmldir` files for discoverability.

2. **Enhance PBR materials & HDR pipeline**
   - Expand `SharedMaterials` to cover clearcoat, anisotropy, transmission, and emissive parameters per QtQuick 3D best practices. Support texture slots (normal, roughness, metalness) loaded via `Texture` or `TextureData` elements.
   - Implement HDR-friendly tone mapping and exposure controls via `SceneEnvironmentController` (set `exposure`, `probeExposure`, `tonemapMode`, `whitePoint`). Add UI bindings/hooks for Python settings if missing.
   - Improve IBL/HDR asset loading (use `IblProbeLoader.qml` in `assets/qml/components`) and ensure fallback to neutral lighting when HDR files unavailable.

3. **Depth of Field & advanced post-processing**
   - Refine DOF shader parameters: auto-focus based on target node distance, configurable bokeh shape, multi-pass blur to avoid banding. Optimise SSAO kernel and TAA interplay to reduce shimmer.
   - Add toggleable filmic effects (chromatic aberration, vignette, grain) with sane defaults, exposed through SceneBridge `effects` payloads.

4. **Animation architecture modernisation**
   - Replace imperative angle calculations with a `Timeline`/`AnimationController` component that blends Python-driven keyframes with fallback procedural motion.
   - Ensure lever/cylinder transforms derive from a central kinematics solver module (could live in `assets/qml/PneumoStabSim/rig/`). Keep properties `userFrequency`, `userAmplitude`, phase offsets, etc., but encapsulate transform computation.
   - Provide diagnostic overlays for animation states (current phase, mismatches) integrated with existing `SignalTracePanel.qml`.

## Constraints & requirements
- Maintain compatibility with the existing SceneBridge signal contract. Do not rename context properties or remove batch update handlers without updating Python emitters.
- All tunable parameters must originate from `config/app_settings.json`; introduce new keys with schema updates if you add settings.
- Internationalisation: any new user-facing text must have en/ru translations under `assets/i18n/`.
- Follow QML style: 4-space indentation, properties grouped by category, `id` first. Keep console logging behind feature flags or diagnostics checks.
- Update documentation describing new structure: `docs/QML_INTEGRATION.md` and relevant phase plans under `docs/`.

### QML Lint policy (обязательно для новых изменений)
- Добавляйте `pragma ComponentBehavior: Bound` в корневых компонентах для избежания предупреждений `unqualified access`.
- Объявляйте `required property` для всех зависимостей, используемых через `property alias` или внешние биндинги.
- Используйте `readonly property` вместо `property` там, где данные не изменяются.
- Запускайте `qmllint` (`make qml-lint` или часть `make check`) перед генерацией кода.

## Deliverables
- Refactored QML components with clear separation of responsibilities and updated `qmldir` files.
- Enhanced PBR material definitions and HDR configuration; new textures or LUTs placed under `assets/hdr/` or `assets/qml/assets/`.
- Improved post-processing pipeline with configurable DOF, SSAO, and optional cinematic effects.
- Modernised animation controller with explicit blending between Python data and fallback simulation.
- Updated documentation and schemas reflecting new parameters.
- Comprehensive tests: extend `tests/ui/test_main_qml_structure.py` and add new coverage for SceneBridge payload handling if necessary.

## Testing & validation
- Run `make check` (aggregates `ruff`, `mypy`, `pytest`, `qmllint`) before submitting.
- Launch the QtQuick scene via `python -m src.app` or `make run-ui` to visually validate HDR/DOF changes. Capture screenshots for regression docs.
- Record any performance baselines with `tools/performance_monitor.py` when adjusting animation timing or enabling new effects.

Provide the final answer as a Git diff across all touched files, ensuring the project remains buildable and documented.
