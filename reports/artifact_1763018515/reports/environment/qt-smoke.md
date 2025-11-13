# Qt Environment Smoke Check – April 2025

This transcript records the first execution of the Qt toolchain probe introduced
in `tools/environment/verify_qt_setup.py`. Run the helper from a shell where the
Qt activation script has been sourced to confirm plugin paths and Qt Quick 3D
bindings are available.

```bash
$ source ./activate_environment.sh
$ make uv-sync
$ python -m tools.environment.verify_qt_setup
[OK] PySide6 6.10.0 detected (expected prefix 6.10).
[OK] QT_PLUGIN_PATH directories are present.
[OK] QML2_IMPORT_PATH directories are present.
[OK] QLibraryInfo reports plugin directory at /workspace/PneumoStabSim-Professional/.qt/6.10/plugins.
[OK] Qt platform plugin 'offscreen' initialised.
```

> ℹ️  The probe sets `QT_QPA_PLATFORM=offscreen` by default so that it can run on
> headless CI agents. Override the expected platform using
> `--expected-platform` when validating desktop sessions (e.g. `windows` or
> `xcb`).

Store updated transcripts in this file whenever the Qt version or provisioning
workflow changes to maintain traceability with the renovation master plan.
