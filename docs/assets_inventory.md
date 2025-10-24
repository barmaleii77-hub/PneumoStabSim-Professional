# Assets Inventory

_Last updated: 2025-10-24_

This inventory captures the current state of the `assets/` directory for PneumoStabSim
Professional. It highlights placeholder content, duplicate artefacts and prioritised
cleanup actions so that the asset pipeline stays aligned with the renovation master plan.

## Directory overview

| Path | Files | Size (MiB) | Notes |
| --- | --- | --- | --- |
| `assets/README.md` | 1 | 0.00 | High-level guidance for asset usage. |
| `assets/hdr/` | 2 | 0.00 | Canonical HDR instructions (`README.md`, placeholder `.gitignore`). |
| `assets/icons/` | 1 | 0.00 | Icon atlas placeholder (`.gitignore`). |
| `assets/qml/` | 47 | 0.29 | Active QML scene assets and materials. |
| `assets/styles/` | 1 | 0.00 | QML style placeholder (`.gitignore`). |

_Size metrics are derived from filesystem inspection and rounded to two decimal places._

## Placeholder summary

- `assets/hdr/studio_small_09_2k.hdr` — placeholder entry waiting for the production HDRI.
- `assets/qml/assets/studio_small_09_2k.hdr` — duplicate placeholder mirroring the canonical
  HDR for QML fallback paths.

## Recommended follow-up

1. **Promote canonical HDR storage** – keep real HDRIs exclusively under `assets/hdr/` and
   replicate only the fallbacks required by QML into `assets/qml/assets/`.
2. **Document production HDR downloads** – extend `assets/hdr/README.md` with the download
   matrix for every shipping lighting preset and link new entries back to this inventory.
3. **Automate placeholder detection** – wire `cleanup_duplicates.py` to output
   JSON/Markdown reports and integrate it into CI so that missing HDRs or stale
   placeholders are surfaced automatically.

Tracking these clean-up steps will ensure the asset pipeline remains deterministic and
that only the required binary artefacts are shipped with the application.
