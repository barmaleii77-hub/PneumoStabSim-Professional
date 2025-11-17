# Cross-Platform RHI and HDR Test Status

## Request summary
- Windows: run with `QSG_RHI_BACKEND=d3d11`, validate `.hdr` loading and dithering.
- Linux: run with `QSG_RHI_BACKEND=opengl`, `QSG_OPENGL_VERSION=4.5`; verify HDR and fallback to GL 3.3.
- macOS: confirm Metal path, HDR, and dithering.

## Environment actions taken
- Synced Python environment with `make uv-sync` to ensure Qt and testing dependencies are available in the container.
- Attempted automated cross-platform prep and test execution via `python -m tools.cross_platform_test_prep --use-uv --run-tests`.

## Current Linux container outcome
- The prep step failed while installing Linux Qt runtime dependencies because `qt6-shader-tools` is not available in the Ubuntu repositories configured for the container. This halted the run before any OpenGL/HDR validation could execute.
- No HDR or dithering checks could be executed inside the container after this failure.

## Platform coverage gaps
- Windows and macOS validation could not run in this Linux-only environment.
- Hardware-accelerated rendering (OpenGL/Metal/D3D) and HDR output paths require a GUI stack that is not available in the headless container.

## Recommended manual verification
- **Windows**: launch the app with `QSG_RHI_BACKEND=d3d11` and load representative `.hdr` assets. Confirm dithering via screenshots or histogram inspection; monitor `logs/ibl/ibl_events.jsonl` for HDR path events.
- **Linux**: run with `QSG_RHI_BACKEND=opengl` and `QSG_OPENGL_VERSION=4.5` first; force fallback by setting `QSG_OPENGL_VERSION=3.3` and confirm graceful degradation. Capture output of `glxinfo | grep "OpenGL version"` for traceability.
- **macOS**: ensure the default Metal backend renders HDR scenes with dithering enabled; collect console logs and frame captures.

## Next steps
- Install or vend a compatible `qt6-shader-tools` package (or adjust the dependency list) so that `tools.cross_platform_test_prep` can complete in CI and local containers.
- After resolving the package issue, rerun the prep script and the standard `make check` workflow to produce verifiable HDR/dithering results for Linux.
- For Windows and macOS, execute equivalent runs on native hosts and archive screenshots plus rendering logs under `reports/tests/` for traceability.
