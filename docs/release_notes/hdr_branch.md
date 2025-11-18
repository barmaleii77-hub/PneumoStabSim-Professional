# HDR Branch Release Notes (v4.9.8)

## Overview
HDR improvements from `hdr/bloom-tonemap` are part of PneumoStabSim Professional v4.9.8. The release
consolidates tone mapping controls, normalizes HDR asset handling, and documents migration paths so
teams can adopt the updated pipeline without breaking existing presets. Version strings align with
`pyproject.toml` and the stabilization plan, removing earlier references to the 2.0.x line.

## Key Changes
- **Tone mapping controls**: `HDR Maximum` and `HDR Scale` sliders complement the existing threshold,
  enabling finer control over bloom/tonemap balance. Values persist through the settings service.
- **HDR asset browsing**: Environment panel now uses `FileCyclerWidget` for cycling HDR skybox files,
  clearing selections, and surfacing guidance when a manifest entry is missing or unreachable.
- **Path normalization & logging**: Main window normalizes HDR URLs across platforms and logs every
  resolution attempt, feeding structured telemetry for troubleshooting mismatched paths.
- **Documentation & guidance**: Updated HDR guides describe caching, manifest-driven lookups, and
  recovery rules for user textures; deprecated "not supported" notes were removed to match the
  current UX.

## Migration & Validation
- Run `make uv-sync && make uv-run CMD="python tools/setup_qt.py --check"` before validating builds
  to ensure Qt and Python dependencies align with the new HDR pipeline.
- Verify manifests with `make verify` (includes `hdr-verify`) and confirm `logs/ibl/ibl_events.jsonl`
  captures path resolution attempts for assets introduced in this release.
- For existing presets, re-save HDR selections through the environment panel so `FileCyclerWidget`
  can persist normalized paths in `config/app_settings.json`.

## Compatibility Notes
- Settings schema remains stable; no new keys are required beyond tone mapping adjustments.
- The release targets Qt/PySide 6.10 and Python 3.13; Windows and Linux builds share the same
  manifest expectations and logging format.
- Documentation, manifests, and release metadata uniformly reference v4.9.8 to avoid
  cross-branch confusion when validating HDR assets.
