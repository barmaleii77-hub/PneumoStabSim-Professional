# Assets Inventory

_Last updated: 2025-10-24_

This inventory captures the current state of the `assets/` directory for PneumoStabSim Professional. It highlights placeholder content, duplicate artefacts and prioritised cleanup actions so that the asset pipeline stays aligned with the renovation master plan.

## Directory overview

| Path | Files | Size (MiB) | Notes |
| --- | --- | --- | --- |
| `assets/README.md` | 1 | 0.00 | High-level guidance for asset usage. |
| `assets/hdr/` | 2 | 0.00 | Placeholder HDR instructions (`README.md`, `.gitignore`). |
| `assets/hdr (2)/` | 2 | 0.00 | Duplicate of `assets/hdr/` placeholder content. |
| `assets/hdr (3)/` | 2 | 0.00 | Duplicate of `assets/hdr/` placeholder content. |
| `assets/icons/` | 1 | 0.00 | Icon atlas placeholder (`.gitignore`). |
| `assets/qml/` | 47 | 0.29 | Active QML scene assets and materials. |
| `assets/styles/` | 1 | 0.00 | QML style placeholder (`.gitignore`). |

_Size metrics are derived from filesystem inspection and rounded to two decimal places._

## Duplicate placeholder groups

The following files share identical checksums and indicate redundant placeholders:

- `.gitignore` files in `assets/hdr/`, `assets/hdr (2)/`, `assets/hdr (3)/` and `assets/qml/assets/` (176 bytes each, MD5 `7e42fbe55b7d5a9935bc7cb881027094`).
- `README.md` placeholder instructions in the same directories (297 bytes each, MD5 `45677ac6f2a1de9cbe8e1809019164e8`).

## Recommended follow-up

1. **Consolidate HDR placeholders** – keep a single canonical location (e.g. `assets/hdr/`) and remove extra copies once QML paths are confirmed.
2. **Document required production HDRIs** – update `assets/hdr/README.md` with an explicit download matrix (resolution, licensing, usage) and link from UI configuration docs.
3. **Prepare asset snapshot tooling** – wire `cleanup_duplicates.py` to output JSON/Markdown reports and integrate it into CI so that new duplicates are detected automatically.

Tracking these clean-up steps will ensure the asset pipeline remains deterministic and that only the required binary artefacts are shipped with the application.
