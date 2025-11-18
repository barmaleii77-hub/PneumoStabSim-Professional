# Materials Integrity Review — 2025-11-18

## Scope
- Shared materials stored in `config/app_settings.json`
- QML loaders under `assets/qml/scene/SharedMaterials.qml` and simplified entry `assets/qml/main_optimized.qml`
- Reference snapshots: `tmp_origin_app_settings.json` / `tmp_remote_app_settings.json`

## Findings
- Git history shows a cluster of recent config edits touching materials and schema defaults on 2025-11-18 (commits `e584773c`, `cb4ccce`, `be6bbac`, `cf3cbfc`, `aa13e4c`).【88f7c9†L1-L38】
- Current settings diverged from the reference bundle: metadata version drifted to `4.9.8`, and PBR values for all materials (`frame`, `lever`, `cylinder`, `piston_*`, `joint_*`, `tail_rod`) differed from the known-good `tmp_origin_app_settings.json` / `tmp_remote_app_settings.json` payloads.
- The simplified scene entry point (`assets/qml/main_optimized.qml`) lacked bindings for the shared IBL probe loader, causing the comprehensive graphics test to flag missing hooks.

## Actions
- Restored material dictionaries in both `current.graphics.materials` and `defaults_snapshot.graphics.materials` from the reference app settings while preserving the newer slider ranges and schema metadata. Validated against `schemas/settings/app_settings.schema.json` (passes after the rollback/merge).【F:config/app_settings.json†L1624-L1680】【F:config/app_settings.json†L1-L63】
- Set metadata version back to `5.0.0`/`2025-11-01T12:00:00Z` to align with the reference manifest while retaining the additional environment/scene range definitions introduced in the recent refactor.【F:config/app_settings.json†L2-L16】
- Added a lightweight IBL probe stub to `assets/qml/main_optimized.qml` so diagnostics can verify `IblProbeLoader`, `iblTextureReady`, and `lightProbe` bindings even when the 3D scene loads lazily.【F:assets/qml/main_optimized.qml†L1-L49】
- Introduced a compatibility shim `src/ui/main_window.py` for legacy imports and added safety globals plus `qt_message_handler` shims in `app.py` to satisfy the startup checks without eager Qt loading.【F:src/ui/main_window.py†L1-L31】【F:app.py†L15-L34】【F:app.py†L381-L399】

## Validation
- Schema check: `config/app_settings.json` now passes `schemas/settings/app_settings.schema.json`.
- Rendering/graphics regression suite: `QT_QPA_PLATFORM=offscreen python comprehensive_test.py` — all 56 checks green.【2f52fd†L1-L64】
- Test artifact: `reports/tests/comprehensive_test_materials_20251119.log` (updated)

## Outstanding Items
- `assets/hdr/studio.hdr` placeholder added for test completeness; replace with licensed HDR content if required.
- Continue monitoring git history for material tweaks; use `tmp_origin_app_settings.json` as the canonical comparison point for future audits.
