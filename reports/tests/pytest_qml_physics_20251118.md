# Pytest report: QML bridge and physics suites

- **Command**: `uv run pytest tests/unit/test_qml_bridge_metadata.py tests/ui/test_qml_signal_contract.py tests/physics/`
- **Date**: 2025-11-18
- **Environment**: Linux container, Python 3.13.8, PySide6 6.10.0 (headless)
- **Result**: ✅ All tests passed (15 tests in ~2s)
- **Notes**: Initial missing system libraries (`libGL.so.1`, `libEGL.so.1`, `libxkbcommon.so.0`) were resolved via package installation. Added shared fixture for physics regression cases and tightened force stubbing to prefer real module imports.

See console chunk `a568cb` for detailed pytest output.
