# UI Environment Tab IBL Dependencies Test (2025-02-14)

## System preparation
- Installed Qt runtime libraries via APT to satisfy PySide6 offscreen requirements:
  - `libgl1`
  - `libegl1`
  - `libegl-mesa0`
  - `libxkbcommon0`
  - transitively pulled Mesa/XCB dependencies (`mesa-vulkan-drivers`, `libdrm2`, etc.).
- Bootstrapped the Python toolchain with `make uv-sync` to materialise PySide6 6.10 and GUI dependencies inside the project virtual environment.

## Test execution
```bash
uv run pytest tests/ui/test_environment_tab_ibl_dependencies.py
```

## Result
- ✅ Test passed (1 test).
- Confirms that the Environment tab disables dependent controls when the IBL and skybox toggles change states once the Qt runtime libraries are present.
