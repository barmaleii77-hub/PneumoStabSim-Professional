# Qt Quick 3D Shader & Batched Update Failures — Research Notes

## Community & Documentation References

- **Qt Forum – QDiffuseSpecularMaterial shader compilation failure**  
  <https://forum.qt.io/topic/140840/qdiffusespecularmaterial-bug-opengl-fragment-shader-not-supported>  
  Highlights how missing or unsupported GLSL semantics (e.g., `attribute` usage in fragment shaders) cause the runtime message `"ERROR: 0:7: '' : compilation terminated"` followed by `"2 compilation errors. No code generated."`. Mirrors the error signature seen in our `run.log` when environment/threeD batches apply.
- **Qt Quick 3D Effect type documentation**  
  <https://doc.qt.io/qt-6/qml-qtquick3d-effect.html>  
  Stresses that every shader uniform or sampler referenced inside an `Effect` must have a corresponding QML property; otherwise, Qt aborts compilation at runtime. This directly explains why recent edits to `FogEffect.qml` / `PostEffects.qml` could be failing during batched updates.
- **Felgo summary of QtQuick3D.Effects deprecation (Qt 6.5+)**  
  <https://felgo.com/doc/qt/qtquick3d-effects-qmlmodule-obsolete/>  
  Recommends migrating to `ExtendedSceneEnvironment` for fog/bloom/color grading to avoid legacy shader paths. Useful if custom effects remain unstable under heavy batched parameter churn.
- **Stack Overflow – Qt Quick Effect Maker resources**  
  <https://stackoverflow.com/questions/78370079/innershadow-effect-not-being-applied-in-qml-application>  
  Notes that missing `.qsb` shader binaries or incorrect resource paths lead to effects silently failing. Worth verifying when batched updates reload environment/threeD assets on the fly.

## Observed Log Correlations (Project Context)

- Bursts of `"ERROR: :47: '' : compilation terminated"` and `"2 compilation errors. No code generated."` in `logs/run.log` coincide with `environment_batch` and `threeD_batch` telemetry marked as `failed` inside `logs/graphics/session_*.jsonl`.
- Payload mismatches (mixing `ibl_source` and legacy `iblSource`) and rapid duplicate batches aggravate shader recompilation pressure, increasing the number of failed events per run.

## GitHub Copilot Prompt

```text
Project context: Qt Quick 3D app (Qt 6.x) using batched QML updates for lighting, environment, quality, camera, materials, and effects. Recent edits touched FogEffect.qml and PostEffects.qml.

Problem: Runtime logs show repeated shader compilation failures exactly when environment_batch or threeD_batch payloads apply. Errors read “ERROR: :47: '' : compilation terminated” and “ERROR: 2 compilation errors. No code generated.” Graphics telemetry records ~8–12 failed batched events per session. Payloads currently include both ibl_source and legacy iblSource keys, and some batches are dispatched twice within one second.

Goals:
1. Fix shader compilation errors in FogEffect.qml/PostEffects.qml so all uniforms and samplers have matching QML properties and GLSL syntax aligns with Qt 6 expectations.
2. Ensure environment/threeD batches succeed (no failed events) after shader fixes.
3. Standardise the payload schema to one IBL key (prefer iblSource to match existing QML) and guard against sending duplicate batches.
4. Optionally migrate to ExtendedSceneEnvironment APIs if custom effects remain unstable.

Task for Copilot: Provide concrete QML and, if needed, Python examples that:
- audit FogEffect/PostEffects uniform/property bindings,
- adjust shader snippets or regenerate .qsb assets to compile cleanly,
- show how to debounce or coalesce batched updates before dispatch,
- and update the payload handling so only the supported IBL key is emitted.
```
