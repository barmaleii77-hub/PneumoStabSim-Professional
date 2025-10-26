# MainWindow Module

## Overview

- **Module path:** `src/ui/main_window/`
- **Public API:** re-exports from `src.ui.main_window_pkg`
- **Purpose:** Compatibility shim that exposes the refactored main window
  implementation while keeping the historical import path (`src.ui.main_window`)
  stable for tooling and legacy scripts.
- **Status:** ✅ Stable – the refactoring is complete and the compatibility layer
  is maintained alongside the new package.

The original project stored all logic in a single `src/ui/main_window.py` file.
During the renovation the codebase migrated to the package
`src.ui.main_window_pkg`, which splits the responsibilities into focussed
modules (`ui_setup`, `state_sync`, `signals_router`, etc.). Some integration
helpers, tests, and third-party extensions still import from
`src.ui.main_window`. The compatibility package ensures those imports continue
to resolve while delegating all behaviour to the new implementation.

---

## Responsibilities

1. **API Bridging**
   - Re-export the `MainWindow` class and helper modules from
     `src.ui.main_window_pkg`.
   - Keep legacy attribute names (`qml_bridge`, `signals_router`, `state_sync`,
     `ui_setup`, `menu_actions`) available so older scripts remain functional.

2. **QML Bridge Hosting**
   - Ship a thin `qml_bridge.py` module inside the compatibility package so
     tools that load files directly from the filesystem (rather than importing a
     module) continue to work.
   - Provide helpers to expose the Qt Quick 3D root object and allow
     bidirectional communication between Python and QML.

3. **Diagnostics**
   - Offer the `describe_modules()` utility that mirrors the shape of the old
     monolithic module. Renovation tooling calls this function to verify that
     all expected helpers are wired up.

---

## Public Surface

```python
from src.ui import main_window

window = main_window.MainWindow(use_qml_3d=True)
window.show()

info = main_window.describe_modules()
assert info["using_refactored"] is True
```

Additional helpers available through the package:

- `main_window.signals_router` – signal/slot wiring between Python panels and
  Qt Quick 3D scene objects.
- `main_window.state_sync` – routines that translate simulation state snapshots
  into UI updates.
- `main_window.ui_setup` – creation of panels, docks, and toolbar widgets.
- `main_window.menu_actions` – definitions for actions added to the menu bar and
  toolbar.
- `main_window.qml_bridge` – façade for interacting with the QML scene.

These helpers delegate to the implementations inside
`src.ui.main_window_pkg`. When updating behaviour, edit the modules in
`main_window_pkg` and the compatibility layer will automatically expose the new
logic.

---

## QML Integration Overview

The compatibility layer keeps the following workflow intact:

1. `MainWindow` instantiates the Qt Widgets shell and loads the Qt Quick 3D
   scene via `qml_bridge`.
2. The bridge exposes a `root_object` accessor that returns the QML root so
   other modules can mutate scene properties.
3. `signals_router` connects Qt signals from the panels to bridge slots, ensuring
   UI interactions propagate to the simulation backend.
4. `state_sync` receives simulation snapshots and calls into `qml_bridge`
   helpers to update 3D entities.

This structure matches the old monolithic file, preserving the public contract
while benefitting from the modularised internals.

---

## Migration Notes

- Remove any lingering imports of `src.ui.main_window.py`; always import the
  package (`from src.ui import main_window`).
- The compatibility layer is intentionally thin. New functionality should be
  added to modules under `src/ui/main_window_pkg/` so that both the modern and
  legacy import paths stay in sync.
- Legacy documentation referencing the standalone file should be updated to the
  package path to prevent confusion during onboarding.
