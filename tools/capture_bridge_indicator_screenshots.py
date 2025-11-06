#!/usr/bin/env python3
"""Capture before/after screenshots for the SceneBridge indicators overlay."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QEventLoop, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView


def _create_application() -> QGuiApplication:
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication(sys.argv)
    return app


def _apply_bridge_state(
    root: QObject,
    *,
    geometry_state: dict | None,
    simulation_state: dict | None,
    dispatch_count: int,
    bridge_connected: bool,
) -> None:
    root.setProperty("geometryState", geometry_state or {})
    root.setProperty("geometryStateReceived", bool(geometry_state))
    root.setProperty("simulationState", simulation_state or {})
    root.setProperty("simulationStateReceived", bool(simulation_state))
    root.setProperty("sceneBridgeDispatchCount", dispatch_count)

    if bridge_connected:
        root.setProperty("sceneBridge", QObject())
    else:
        root.setProperty("sceneBridge", None)


def _configure_panel(root: QObject, *, visible: bool) -> None:
    panel = root.findChild(QObject, "bridgeIndicators")
    if panel is not None:
        panel.setProperty("visible", visible)


def _capture_view(
    *,
    qml_path: Path,
    output_path: Path,
    geometry_state: dict | None,
    simulation_state: dict | None,
    dispatch_count: int,
    bridge_connected: bool,
    panel_visible: bool,
    size: tuple[int, int],
    delay_ms: int,
) -> None:
    view = QQuickView()
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.setSource(QUrl.fromLocalFile(str(qml_path)))
    view.setColor("black")
    width, height = size
    view.setWidth(width)
    view.setHeight(height)
    view.show()

    app = QGuiApplication.instance()
    if app is None:
        raise RuntimeError("QGuiApplication is not initialised")
    app.processEvents()

    root = view.rootObject()
    if root is None:
        raise RuntimeError("SimulationRoot.qml did not load")

    _apply_bridge_state(
        root,
        geometry_state=geometry_state,
        simulation_state=simulation_state,
        dispatch_count=dispatch_count,
        bridge_connected=bridge_connected,
    )
    _configure_panel(root, visible=panel_visible)

    loop = QEventLoop()
    QTimer.singleShot(delay_ms, loop.quit)
    loop.exec()

    image = view.grabWindow()
    if image.isNull() or not image.save(str(output_path)):
        raise RuntimeError(f"Failed to save screenshot to {output_path}")

    view.hide()
    view.deleteLater()
    app.processEvents()


def _default_geometry_state() -> dict:
    return {
        "frame": {"width": 1.8, "height": 0.65},
        "joints": {
            "fl": {"x": -0.45},
            "fr": {"x": 0.45},
            "rl": {"x": -0.45},
            "rr": {"x": 0.45},
        },
    }


def _default_simulation_state() -> dict:
    return {
        "levers": {
            "fl": {"angle": 12.5},
            "fr": {"angle": 13.0},
        },
        "pistons": {
            "fl": {"position": 0.22},
            "fr": {"position": 0.23},
        },
        "aggregates": {"stepNumber": 128, "simulationTime": 1.347},
    }


def capture_screenshots(
    output_dir: Path, *, size: tuple[int, int], delay_ms: int
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    qml_path = repo_root / "assets" / "qml" / "PneumoStabSim" / "SimulationRoot.qml"
    if not qml_path.is_file():
        raise FileNotFoundError(f"Cannot locate SimulationRoot.qml at {qml_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    geometry_state = _default_geometry_state()
    simulation_state = _default_simulation_state()

    _capture_view(
        qml_path=qml_path,
        output_path=output_dir / "bridge-indicators-before.png",
        geometry_state=geometry_state,
        simulation_state=simulation_state,
        dispatch_count=3,
        bridge_connected=True,
        panel_visible=False,
        size=size,
        delay_ms=delay_ms,
    )

    _capture_view(
        qml_path=qml_path,
        output_path=output_dir / "bridge-indicators-after.png",
        geometry_state=geometry_state,
        simulation_state=simulation_state,
        dispatch_count=6,
        bridge_connected=True,
        panel_visible=True,
        size=size,
        delay_ms=delay_ms,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/ui"))
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument(
        "--delay-ms",
        type=int,
        default=900,
        help="Delay before capturing each frame",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QSG_RHI_BACKEND", "opengl")
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    os.environ.setdefault("QML2_IMPORT_PATH", str(repo_root / "assets" / "qml"))

    app = _create_application()

    try:
        capture_screenshots(
            args.output_dir,
            size=(args.width, args.height),
            delay_ms=args.delay_ms,
        )
    finally:
        QTimer.singleShot(0, app.quit)
        app.exec()

    return 0


if __name__ == "__main__":
    sys.exit(main())
