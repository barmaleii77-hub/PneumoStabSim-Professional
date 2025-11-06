# RHI Backend Validation (Qt 6.10)

This report captures the smoke test results requested for Qt 6.10 helpers. Each
run was executed after clearing shader caches and forcing the Qt Quick
application into `--test-mode` so it closes automatically.

## Run 1 — OpenGL backend (`QSG_RHI_BACKEND=opengl`)
- Command: `QT_QPA_PLATFORM=offscreen QSG_RHI_BACKEND=opengl QT_RHI_SHADER_CACHE_DIR=.qtshadercache-opengl python app.py --test-mode --verbose`
- Outcome: application created the main window, loaded all graphics batches, and
  exited with status code `0`.
- Key log excerpt:

```
INFO     | PneumoStabSim | Backend: opengl
INFO     | PneumoStabSim | MainWindow created and shown
✅ Application closed (code: 0)
```

## Run 2 — Default backend (no override)
- Command: `QT_QPA_PLATFORM=offscreen QT_RHI_SHADER_CACHE_DIR=.qtshadercache-default python app.py --test-mode --verbose`
- Outcome: backend resolved to OpenGL on this platform, the UI initialised, and
  exit status remained `0` with no critical shader warnings from `FogEffect.qml`
  or `PostEffects.qml`.
- Key log excerpt:

```
INFO     | PneumoStabSim | Backend: opengl
INFO     | PneumoStabSim | MainWindow created and shown
✅ Application closed (code: 0)
```

No `ERROR` level records or `qml:` diagnostics were produced by
`FogEffect.qml` or `PostEffects.qml` in either run, confirming that GLSL profile
selection succeeded without triggering fallback errors.

## 2025-11-06 — Effect toggle sweep (OpenGL / ANGLE / Vulkan)

- Command template: `QT_QPA_PLATFORM=offscreen QSG_INFO=1 QSG_RHI_DEBUG_LAYER=1
  QSG_RHI_BACKEND=<backend> python app.py --test-mode --verbose`
- Settings: temporary copies of `config/app_settings.json` were patched per run
  to flip Bloom, Depth of Field, Motion Blur, and SSAO (`ao_enabled`).
- Automation: `tools/settings_cycle_runner.py` inspired runner captured stdout
  into dedicated artefacts under `reports/graphics/` and JSON summaries in
  `logs/graphics/session_*.jsonl`.

| Backend | Mode | Run log |
| --- | --- | --- |
| OpenGL | Effects on | `reports/graphics/rhi_effects_opengl_effects_on_20251106_032913.md` |
| OpenGL | Effects off | `reports/graphics/rhi_effects_opengl_effects_off_20251106_032913.md` |
| ANGLE (`QT_OPENGL=angle`) | Effects on | `reports/graphics/rhi_effects_angle_effects_on_20251106_032913.md` |
| ANGLE (`QT_OPENGL=angle`) | Effects off | `reports/graphics/rhi_effects_angle_effects_off_20251106_032913.md` |
| Vulkan (Lavapipe) | Effects on | `reports/graphics/rhi_effects_vulkan_effects_on_20251106_032913.md` |
| Vulkan (Lavapipe) | Effects off | `reports/graphics/rhi_effects_vulkan_effects_off_20251106_032913.md` |

Highlights:

- All six runs exited with return code `0`; the summary JSON captures the raw
  metadata (`reports/graphics/rhi_effects_summary_20251106_032913.json`).
- Telemetry confirmed that the `effects_batch` payload applied the requested
  toggles (e.g. `motion_blur` and `depth_of_field` enabled in the OpenGL "on"
  sweep, then disabled in the "off" sweep).
- Qt still reports `Property value set multiple times` for
  `SuspensionAssembly.qml` even on an unmodified baseline run; this pre-existing
  warning does not impact the effect toggles and will be tracked separately.

## 2025-11-06 — RHI debug-layer sweep (`QSG_INFO=1`, `QSG_RHI_DEBUG_LAYER=1`)

- Command template: `QT_QPA_PLATFORM=offscreen QSG_INFO=1 QSG_RHI_DEBUG_LAYER=1`
  `QSG_RHI_BACKEND=<backend> python app.py --test-mode --verbose`
- Automation: `tools/run_rhi_effects_sweep.py` now patches a temporary copy of
  `config/app_settings.json` and records each run as Markdown plus a JSON
  summary (`reports/graphics/rhi_effects_summary_20251106_034349.json`).
- Verification: Bloom, Depth of Field, Motion Blur, and SSAO were toggled on
  and off for every backend while the Qt Quick debug layer remained active.

| Backend | Mode | Run log |
| --- | --- | --- |
| OpenGL | Effects on | `reports/graphics/rhi_effects_opengl_effects_on_20251106_034349.md` |
| OpenGL | Effects off | `reports/graphics/rhi_effects_opengl_effects_off_20251106_034349.md` |
| ANGLE (`QT_OPENGL=angle`) | Effects on | `reports/graphics/rhi_effects_angle_effects_on_20251106_034349.md` |
| ANGLE (`QT_OPENGL=angle`) | Effects off | `reports/graphics/rhi_effects_angle_effects_off_20251106_034349.md` |
| Vulkan (Lavapipe) | Effects on | `reports/graphics/rhi_effects_vulkan_effects_on_20251106_034349.md` |
| Vulkan (Lavapipe) | Effects off | `reports/graphics/rhi_effects_vulkan_effects_off_20251106_034349.md` |

Observations:

- The QSG debug layer did not emit additional validation errors for any RHI
  backend; only the long-standing `_qquick_widget` status warning and
  `SuspensionAssembly.qml` duplication message remain.
- Renderer API selection stayed consistent (`opengl-rhi`, `angle-rhi`, and
  `vulkan-rhi` respectively) and each run exited cleanly (`returncode == 0`).
