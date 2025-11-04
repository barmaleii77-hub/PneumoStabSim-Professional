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
