# Path and Environment Issues Overview

This document captures known problems related to Python path configuration, Qt/QML environment variables, resource locations, and configuration consistency. Items marked as resolved highlight completed remediation, while the remaining sections enumerate outstanding gaps.

## Critical: Project Path Imports
- ✅ **Resolved** — `app.py` now injects the project root and `src/` directory into `sys.path` before any local imports execute, ensuring the mixed absolute/relative imports remain available from source checkouts.

## Qt/QML Environment Variables
- ✅ **Resolved** — `setup_qtquick3d_environment` always appends the Qt installation paths (including `QT_PLUGIN_PATH`) and the project's `assets/qml` plus `assets/qml/components` directories to `QML2_IMPORT_PATH`, `QML_IMPORT_PATH`, and `QT_QML_IMPORT_PATH`, even when custom values are present in `.env`.
- ✅ **Resolved** — A default `QT_QUICK_CONTROLS_STYLE=Fusion` is now provided during bootstrap, matching the recommended consistent styling.
- ✅ **Resolved** — Linux headless safeguards (`QT_QPA_PLATFORM=offscreen`, `QT_QUICK_BACKEND=software`) remain enforced when `DISPLAY` is unset.

## Encoding and Locale Fragility
- ✅ **Resolved** — Windows code-page switching now checks the `chcp 65001` result and reports failures, reducing silent UTF-8 breakages, while the locale bootstrap records issues via `log_warning`.
- ✅ **Resolved** — POSIX locale configuration attempts `en_US.UTF-8` before `C.UTF-8`, exporting the successful locale through `LC_ALL`/`LANG` when available.

## Configuration Schema Path Inconsistencies
- ✅ **Resolved** — `tools/audit_config.py` now defaults to the canonical schema path `schemas/settings/app_settings.schema.json`, matching runtime usage.
- `config/app_settings.json` and the associated schema files are present; ensure future changes keep both locations synchronized if multiple copies remain necessary.

## QML Resource Paths and Compatibility
- Runtime logs reference `assets/qml/main.qml`, but the repository only includes `assets/qml/quality/Check.qml`; attempting to load the missing file results in a failure.
- The QML error `Cannot assign to non-existent property "fogDensity"` indicates an incompatibility with the installed QtQuick3D version or incorrect imports for effects such as fog; Qt 6.10+ with the relevant modules is required.

## Dependency and Version Mismatches
- PySide6 version 6.10.x is required (see `.github/copilot-instructions.md`), yet `requirements.txt` lists placeholder entries ("… (multiple hashes)") that break installation.
- Documentation and code disagree on the expected Python and Qt versions, leading to features like `ExtendedSceneEnvironment` or Fog properties failing under mismatched runtimes.

## Additional Path Handling Concerns
- ✅ **Resolved for entrypoints** — The main launcher now prepares `sys.path`, mitigating mixed import failures when running from a checkout. Review auxiliary scripts to ensure they import `app.bootstrap` helpers or perform equivalent setup.
- Reliance on `os.getcwd()` to resolve resource paths is brittle—running the application from a different working directory breaks QML resource discovery.

## Recommended Next Steps
- Verify Qt 6.10+ availability to unlock fog and extended scene environment properties.
- Consolidate JSON schema authoring so duplicate copies remain synchronized or are deduplicated entirely.
- Audit scripts that derive resource paths from `os.getcwd()` and refactor them to rely on project-root resolution utilities.
