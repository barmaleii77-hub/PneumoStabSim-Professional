# QML HDR Fallback

QML scenes reference `assets/studio_small_09_2k.hdr` as the default fallback
image-based lighting probe. The canonical copy of this HDRI lives in
`assets/hdr/`; replicate it here (or create a symlink) so that relative
imports from QML continue to resolve during development builds.

## Refresh checklist

- Pull the latest lighting assets into `assets/hdr/`.
- Copy `assets/hdr/studio_small_09_2k.hdr` to this directory.
- Confirm that the file size matches the source download (≈4 MiB).
- Re-run the rendering smoke tests to validate lighting presets.
If the HDRI is not yet available, leave a tiny placeholder file with the same
name so that module imports do not fail. Replace the placeholder as soon as
the real asset ships.
