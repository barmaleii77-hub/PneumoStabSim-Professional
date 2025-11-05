# `make check` Results – 2025-11-05

Command: `make check`

## Summary
- Ruff formatting/linting: ✅ (`244` files already formatted; no lint violations).
- Mypy type-check: ✅ (3 targets).
- `qmllint`: ✅ (Qt plugin duplication warnings observed, no blocking errors).
- Pytest suite (quality + physics + pneumo): ✅ (`28 passed`).
- Shader validation (`tools/validate_shaders.py`): ✅.
- HDR orientation validation: ✅ (`3 skybox entries`).
- Translation audit: ✅ (no missing strings; unfinished items remain expected backlog).
- Qt environment probe: ✅ after exporting `QT_PLUGIN_PATH` and `QML2_IMPORT_PATH` to the generated `.venv` paths.

## Notes
- Installed missing runtime dependencies (`pydantic`, `libxkbcommon0`, `libgl1`, `libegl1`) to satisfy CI tooling and shader validators.
- Generated Qt environment reports at `reports/environment/qt_environment_20251105T074538Z.log` and `reports/environment/qt_environment_20251105T074711Z.log` during iterative runs.
- `qmllint` emitted duplicate plugin warnings for `QtDesignStudio`/`Quick`; no action required per Phase 3 guidance (tracked in existing backlog).
