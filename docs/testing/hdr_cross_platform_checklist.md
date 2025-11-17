# HDR Cross-Platform Validation Checklist

This guide documents the manual smoke procedures for validating HDR file
loading and dithering toggles across Windows, Linux, and macOS. The checklist
is backed by `tools/hdr_backend_matrix.py`, which verifies repository assets
and prints the environment configuration for the selected platform.

## 1. Prerequisites

1. Sync the Python toolchain:
   - Linux/macOS: `make uv-sync`
   - Windows: `python -m tools.task_runner uv-sync`
2. Verify dependencies, Qt version (≥ 6.10), and HDR assets:
   ```bash
   python -m tools.hdr_backend_matrix --check --require-qt 6.10
   ```
   The command fails if required assets or a compliant Qt runtime are missing.
3. Ensure Qt Quick Controls style is set to `Basic` or `Fusion` according to
   the platform launch script. Use the bundled launchers (`run_app.*` or
   `universal_f5.py`) instead of invoking `python app.py` directly.

## 2. Windows (Direct3D 11)

1. Launch an elevated PowerShell session and run:
   ```powershell
   scripts\setup_environment.ps1
   run_app.ps1
   ```
2. Confirm the application log prints `Qt RHI backend: d3d11` (Direct3D 11) and
   that `python -m tools.hdr_backend_matrix --platform windows` reports Qt ≥
   6.10.
3. Load any repository `.hdr` entry (for example the manifest-backed
   `../hdr/studio_small_09_2k.hdr`) via the Graphics → Environment panel.
4. Toggle **Graphics → Quality → Dithering (Qt 6.10+)** to verify the Direct3D
   path respects the flag and reduces banding on gradient-heavy meshes.
5. Capture a screenshot demonstrating dithering both on and off and attach it
   to the QA ticket.

## 3. Linux (OpenGL 4.5 Core)

1. Export the required environment variables:
   ```bash
   export QSG_RHI_BACKEND=opengl
   export QSG_OPENGL_VERSION=4.5
   export QT_OPENGL_PROFILE=core
   ```
   Optional fallback for legacy hardware (rerun the steps below after exporting):
   ```bash
   export QSG_OPENGL_VERSION=3.3
   ```
2. Run the automated suite: `make cross-platform-test`.
3. Launch `python -m tools.hdr_backend_matrix --platform linux --backend opengl`
   and confirm the rendered checklist lists OpenGL 4.5 as the primary backend
   (or 3.3 when testing the fallback path).
4. Start the application (`make run` or `python -m tools.task_runner uv-run -- python app.py`), load a manifest-listed `.hdr`
   file, and verify the environment label resolves to the `file://` URL.
5. Flip the dithering checkbox and confirm the JSON diagnostics
   (`reports/graphics/log_analysis_summary.txt`) capture the change for both the
   primary and fallback OpenGL versions.

## 4. macOS (Metal)

1. Execute the universal launcher so the Metal layer initialises correctly:
   ```bash
   python universal_f5.py --backend metal
   ```
2. Verify console output contains `Qt RHI backend: metal` and that shader
   compilation completes without warnings (Qt ≥ 6.10 must be reported by
   `python -m tools.hdr_backend_matrix --platform macos`).
3. Import a `.hdr` file from the manifest and inspect the tonemapping curve in
   the Graphics diagnostics overlay.
4. Toggle the dithering option to ensure the Metal pipeline respects the
   ExtendedSceneEnvironment flag and records the toggle in the graphics JSON
   diagnostics.

## 5. Troubleshooting

| Symptom | Resolution |
| --- | --- |
| `PySide6` import fails | Re-run `make uv-sync` (Linux/macOS) or
  `python -m tools.task_runner uv-sync` (Windows) to reinstall Qt 6.10. |
| HDR file missing | Restore the asset package from `assets/hdr/README.md`.
  The README includes download mirrors. |
| Dithering toggle disabled | Confirm Qt version ≥ 6.10 using
  `python -m tools.hdr_backend_matrix --check`. |
| OpenGL context defaults to compatibility profile | Explicitly export
  `QT_OPENGL_PROFILE=core` before launching and verify with `glxinfo`. |

## 6. Reporting

Attach the CLI output from `python -m tools.hdr_backend_matrix` and the UI
screenshot(s) to the QA ticket. Record pass/fail status for each platform in
`reports/tests/<date>_hdr_matrix.md` to preserve traceability.
