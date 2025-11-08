# QML HDR Assets

The modern rendering pipeline no longer ships with a hard-coded HDR fallback.
Qt Quick 3D scenes load image-based lighting (IBL) assets through
`components/IblProbeLoader.qml`, which reads the active file from the
application settings or the graphics UI. If no EXR/HDR file is configured,
the loader leaves the probe empty and the UI displays `—` to reflect the
absence of lighting data.

## Asset handling checklist

- Place candidate HDR/EXR files under `assets/hdr/` or another configured
  search path.
- Use the graphics settings panel to cycle through the available HDR files and
  persist the chosen path back to `config/app_settings.json`. The same
  `FileCyclerWidget` powers the materials tab: drop custom textures (for
  example, `frame_albedo.png`) here or next to the project so that
  `SharedMaterials` picks them up automatically.
- Do **not** copy placeholder files into this directory. Missing files should
  surface as warnings so users can address the configuration explicitly.
- Re-run the rendering smoke tests after updating HDR assets to confirm the
  lighting profile loads correctly.
