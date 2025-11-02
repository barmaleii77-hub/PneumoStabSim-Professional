# HDR Environment Inventory

This directory stores the canonical high dynamic range (HDR) environment maps that feed
image-based lighting for PneumoStabSim Professional. Keeping the authoritative copies
here ensures that lighting presets stay consistent between the editor, automated tests
and packaged builds.

## Required production HDRIs

| File name | Resolution | Source | License | Purpose |
| --- | --- | --- | --- | --- |
| `studio_small_09_2k.hdr` | 2048×1024 | https://polyhaven.com/a/studio_small_09 | CC0 1.0 | Default fallback for the workshop lighting preset. |

_Store additional HDRIs in this directory using the same table format so that the
renovation plan can track coverage at a glance._

## Installation workflow

1. Download the required HDR files from the sources listed above.
2. Place the originals in `assets/hdr/` and keep the filenames unchanged.
3. Copy (or symlink) the fallback HDR used by QML views to
   `assets/qml/assets/studio_small_09_2k.hdr`.
4. Commit the updated inventory table whenever new lighting profiles are added.

## Curation policy

- Do not commit temporary placeholder files. Missing HDRIs should surface as
  configuration warnings during testing so we notice broken lighting pipelines
  early.
- Large raw captures (for example, `DSC_9975.NEF`) must stay in the external
  art source archive. Reference them in documentation or manifests, but do not
  add them to this repository.
- When introducing a new HDRI, update the table above and attach licensing
  details so downstream teams can validate redistribution rights.
