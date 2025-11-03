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

- Bursts of `"ERROR: :47: '' : compilation terminated"` and `"2 compilation errors. No code generated."` in `logs/run.log` coincide with `environment_batch` and `threeD_batch` telemetry marked as `failed` inside `logs/graphics/session_*.jsonl`. The `:47` prefix maps to the generated GLSL rather than any QML line; rerun with `QT_DEBUG_SHADERS=1` to dump the expanded shader source and inspect the exact GLSL line numbers.
- Batched payloads include both `ibl_source` and the legacy `iblSource` to keep downstream QML bridges compatible. The dual keys are deliberate for backward compatibility and do **not** signal an unfinished migration; normalisation simply keeps the mirrored values in sync while we eliminate duplicate batch dispatches.

## GitHub Copilot Prompt

```text
Project context: Qt Quick 3D app (Qt 6.x) using batched QML updates for lighting, environment, quality, camera, materials, and effects. Recent edits touched FogEffect.qml and PostEffects.qml.

Problem: Runtime logs show repeated shader compilation failures exactly when environment_batch or threeD_batch payloads apply. Errors read “ERROR: :47: '' : compilation terminated” and “ERROR: 2 compilation errors. No code generated.” Graphics telemetry records ~8–12 failed batched events per session. Payloads intentionally include both `ibl_source` and legacy `iblSource` keys for compatibility, but they must remain normalised, and some batches are dispatched twice within one second.

Goals:
1. Fix shader compilation errors in FogEffect.qml/PostEffects.qml so all uniforms and samplers have matching QML properties and GLSL syntax aligns with Qt 6 expectations.
2. Ensure environment/threeD batches succeed (no failed events) after shader fixes.
3. Keep `ibl_source` as the canonical value, mirror it to the legacy `iblSource` key for compatibility, and guard against sending duplicate batches.
4. Optionally migrate to ExtendedSceneEnvironment APIs if custom effects remain unstable.

Task for Copilot: Provide concrete QML and, if needed, Python examples that:
- audit FogEffect/PostEffects uniform/property bindings,
- adjust shader snippets or regenerate .qsb assets to compile cleanly,
- show how to debounce or coalesce batched updates before dispatch,
- and keep payload handling normalised so `ibl_source` and `iblSource` always carry the same value.
```
## 2025-02-13 — GLSL 450 core adoption

- Основной fog-фрагмент переведён на `#version 450 core`, что соответствует требованию Qt Quick 3D использовать Vulkan-style GLSL и исключает непредсказуемые профили при компиляции SPIR-V. См. детализацию в [docs/graphics.md](../docs/graphics.md) и официальную справку Qt.[^qt-effect]
- Резервный `fog_fallback.frag` остаётся на `#version 330` и активируется, когда `FogEffect.qml` фиксирует `Shader.Error` или отсутствие depth-текстуры (`depthTextureAvailable=false`). Это гарантирует, что batched обновления не обрываются даже в GLES/ANGLE профилях.
- Результаты проверки зафиксированы в `reports/tests/make_check_20250213.md`: `make check` проходит `ruff`/`mypy`/`qmllint` без ошибок, подтверждая целостность пакета шейдеров и QML-мостов.
- basysKom подчёркивает, что для compute/эффектных шейдеров следует использовать как минимум GLSL 4.40, поскольку `qt_shader_tools` компилирует исходники в SPIR-V.[^basyskom]

[^qt-effect]: https://doc.qt.io/qt-6/qml-qtquick3d-effect.html#details
[^basyskom]: https://www.basyskom.de/use-compute-shader-in-qt-quick/
