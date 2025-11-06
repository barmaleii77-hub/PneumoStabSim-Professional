# QML Screenshot Baselines

This directory contains deterministic reference frames used by
`tests/ui/test_main_qml_screenshots.py`. Each baseline is stored as a JSON
document containing the encoded PNG payload (`encoding: "png"`,
`data: <base64>`). The frames are captured from the Qt Quick scene running in
offscreen mode (`QT_QPA_PLATFORM=offscreen`) with the `screenshots` file
selector enabled. The selector routes `main.qml` and the simulation panel
through lightweight screenshot-specific variants located in
`assets/qml/+screenshots/`.

## Update procedure

1. Ensure the PySide6 dependencies are installed with `make uv-sync`.
2. Remove outdated baselines if necessary: `rm tests/ui/baselines/*.json`.
3. Re-generate the frames by executing:

   ```bash
   make uv-run CMD="pytest tests/ui/test_main_qml_screenshots.py --capture=tee-sys"
   ```

   After a successful run, PNG artifacts are written to
   `reports/tests/integration/ui_screenshots/`.
4. Convert each PNG artifact into the JSON baseline format using the helper
   command:

   ```bash
   python -m tests.ui.utils.screenshot encode-baseline \
       reports/tests/integration/ui_screenshots/main_default.png \
       tests/ui/baselines/main_default.json
   ```

   Repeat for every updated frame (e.g., `main_animation_running`).
5. Review the textual diff and commit the refreshed baselines.

Always verify the rendered scene looks correct by inspecting the generated
artifacts.  Minor numerical differences are tolerated in the tests via the RMS
threshold configured in `compare_with_baseline`.
