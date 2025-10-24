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

## Placeholder policy

Until the production assets are available, create a tiny placeholder file named
`studio_small_09_2k.hdr` in both `assets/hdr/` and `assets/qml/assets/` so that QML
imports continue to resolve. Replace these placeholders with the genuine files before
shipping a release build.
