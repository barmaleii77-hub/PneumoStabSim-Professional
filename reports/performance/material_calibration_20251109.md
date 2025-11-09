# Phase 3 Material Calibration Summary – 2025-11-09

## Overview
- Normalised all Phase 3 graphics materials to the calibrated IOR, transmission, and attenuation targets captured in the renovation plan.
- Synced `config/app_settings.json` and the baseline snapshot so runtime defaults match the new calibration data.
- Introduced a preset-aware tonemapping panel in the modular graphics UI to expose the HDR presets managed by `LightingSettingsFacade`.
- Relocated the HDR orientation validator to `tools/render_checks/` and regenerated the official report after applying the new material catalogue.

## Validation Artefacts
- ✅ `tools/render_checks/validate_hdr_orientation.py` &rarr; `reports/performance/hdr_orientation.md`
- ✅ `make check` (see CI logs) – ensures the validator runs on every pipeline execution.

## Follow-up
- Capture refreshed UI screenshots for the tonemapping presets during the next design review session.
- Monitor nightly profiles for drift now that metalness/roughness values reflect the calibration library.
