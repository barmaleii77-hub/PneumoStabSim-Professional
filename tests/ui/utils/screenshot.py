"""Utilities for capturing deterministic Qt Quick frames in tests."""

from __future__ import annotations

import argparse
import base64
import io
import json
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from PIL import Image, ImageChops, ImageStat

from PySide6.QtCore import QObject, Qt, QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlContext, QQmlFileSelector
from PySide6.QtQuick import QQuickView, QQuickWindow

from src.ui.qml_bridge import QMLBridge
from src.ui.scene_bridge import SceneBridge

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

_ASSETS_IMPORT = Path("assets/qml").resolve()
_BASELINE_VERSION = 1


def _process_events(qapp, iterations: int = 10) -> None:
    """Process Qt events to ensure asynchronous loaders finish."""

    for _ in range(max(1, iterations)):
        qapp.processEvents()
        qapp.sendPostedEvents()


def _wait_until(
    condition, qapp, timeout_ms: int = 4000, *, sleep_step: float = 0.01
) -> bool:
    """Spin the Qt event loop until ``condition`` returns ``True`` or timeout."""

    deadline = time.monotonic() + timeout_ms / 1000.0
    while time.monotonic() < deadline:
        if condition():
            return True
        _process_events(qapp, iterations=1)
        if sleep_step:
            time.sleep(sleep_step)
    return condition()


@dataclass
class QMLScene:
    """Container describing the loaded QML view."""

    view: QQuickView
    root: QObject
    scene_bridge: SceneBridge

    def close(self) -> None:
        """Release Qt resources associated with the scene."""

        if self.view.isVisible():
            self.view.hide()
        self.view.deleteLater()
        engine = self.view.engine()
        if engine is not None:
            engine.clearComponentCache()

    def __enter__(self) -> "QMLScene":
        return self

    def __exit__(self, exc_type, exc, tb) -> Optional[bool]:
        self.close()
        return None


def _initialise_view(
    qapp,
    *,
    qml_path: Path,
    width: int = 800,
    height: int = 450,
    scene_bridge: Optional[SceneBridge] = None,
) -> QMLScene:
    view = QQuickView()
    view.setColor(QColor(Qt.black))
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    engine = view.engine()
    engine.addImportPath(str(_ASSETS_IMPORT))
    selector = QQmlFileSelector(engine)
    selector.setExtraSelectors(["screenshots"])

    bridge = scene_bridge or SceneBridge()

    context: QQmlContext = view.rootContext()
    context.setContextProperty("pythonSceneBridge", bridge)

    view.setSource(QUrl.fromLocalFile(str(qml_path)))
    view.setWidth(width)
    view.setHeight(height)
    view.show()

    def _view_ready() -> bool:
        return view.status() == QQuickView.Ready and view.rootObject() is not None

    if not _wait_until(_view_ready, qapp, timeout_ms=6000):
        raise TimeoutError(f"Failed to load QML scene from {qml_path}")

    root = view.rootObject()
    if root is None:
        raise RuntimeError("QQuickView root object is unavailable after loading")

    _process_events(qapp, iterations=5)

    return QMLScene(view=view, root=root, scene_bridge=bridge)


def load_main_scene(
    qapp,
    *,
    width: int = 800,
    height: int = 450,
    qml_file: Path | str = Path("assets/qml/main.qml"),
) -> QMLScene:
    """Load the main QML entry point into an offscreen ``QQuickView``."""

    qml_path = Path(qml_file).resolve()
    if not qml_path.exists():
        raise FileNotFoundError(qml_path)

    return _initialise_view(qapp, qml_path=qml_path, width=width, height=height)


def ensure_simulation_panel_ready(
    scene: QMLScene, qapp, timeout_ms: int = 4000
) -> QObject:
    """Wait for the simulation panel to report ``isReady``."""

    def _panel_ready() -> bool:
        panel = scene.root.findChild(QObject, "simulationPanel")
        return bool(panel and panel.property("isReady"))

    success = _wait_until(_panel_ready, qapp, timeout_ms=timeout_ms)
    if not success:
        raise TimeoutError("Simulation panel did not become ready in time")
    panel = scene.root.findChild(QObject, "simulationPanel")
    assert panel is not None
    return panel


def _qimage_to_pillow(image: QImage) -> Image.Image:
    converted = image.convertToFormat(QImage.Format_RGBA8888)
    ptr = converted.bits()
    if hasattr(ptr, "tobytes"):
        buffer = ptr.tobytes()
    else:
        buffer = bytes(ptr)
    if len(buffer) != converted.sizeInBytes():
        buffer = buffer[: converted.sizeInBytes()]
    pil_image = Image.frombuffer(
        "RGBA",
        (converted.width(), converted.height()),
        buffer,
        "raw",
        "RGBA",
        0,
        1,
    )
    return pil_image.copy()


def capture_window_image(
    window: QQuickWindow, qapp, *, settle_iterations: int = 4
) -> Image.Image:
    """Grab the current framebuffer of ``window`` as a Pillow image."""

    _process_events(qapp, iterations=max(1, settle_iterations))
    image = window.grabWindow()
    if image.isNull():
        raise RuntimeError("grabWindow() returned an empty image")
    return _qimage_to_pillow(image)


def _normalise_payload(updates: dict[str, object]) -> dict[str, object]:
    prepared = QMLBridge._prepare_for_qml(dict(updates))
    return prepared


def push_updates(root: QObject, updates: dict[str, object]) -> None:
    """Apply a batch of updates to ``pendingPythonUpdates`` using :class:`QMLBridge`."""

    if not updates:
        return

    payload = _normalise_payload(updates)
    root.setProperty("pendingPythonUpdates", payload)


def _baseline_from_payload(payload: dict[str, object], *, source: Path) -> Image.Image:
    encoding = payload.get("encoding", "png")
    if encoding != "png":
        raise ValueError(f"Unsupported baseline encoding '{encoding}' in {source}")

    raw_data = base64.b64decode(str(payload["data"]))
    image = Image.open(io.BytesIO(raw_data)).convert("RGBA")
    expected_size = tuple(payload.get("size", []))
    if expected_size and image.size != tuple(expected_size):
        raise AssertionError(
            f"Baseline size metadata {expected_size} does not match decoded image size {image.size}"
        )
    return image


def _load_baseline_image(target: Path) -> Image.Image:
    """Load a baseline encoded as JSON with base64 image payload."""

    payload = json.loads(target.read_text(encoding="utf-8"))
    version = payload.get("version", 1)
    if version != _BASELINE_VERSION:
        raise ValueError(
            f"Baseline '{target}' has unsupported version {version}; expected {_BASELINE_VERSION}"
        )
    return _baseline_from_payload(payload, source=target)


def _serialise_baseline(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    payload = {
        "version": _BASELINE_VERSION,
        "encoding": "png",
        "mode": image.mode,
        "size": [image.width, image.height],
        "data": encoded,
    }
    return json.dumps(payload, indent=2) + "\n"


def encode_baseline_from_png(png_path: Path | str, baseline_path: Path | str) -> Path:
    """Convert ``png_path`` into the textual baseline format at ``baseline_path``."""

    source = Path(png_path)
    if not source.exists():
        raise FileNotFoundError(source)

    image = Image.open(source).convert("RGBA")
    baseline = Path(baseline_path)
    baseline.write_text(_serialise_baseline(image), encoding="utf-8")
    return baseline


def compare_with_baseline(
    captured: Image.Image,
    baseline_path: Path | str,
    *,
    tolerance: float = 3.5,
    diff_output: Path | None = None,
) -> float:
    """Compare ``captured`` image against the stored baseline."""

    target = Path(baseline_path)
    if not target.exists():
        raise FileNotFoundError(
            f"Baseline image '{target}' is missing. Run the update procedure to regenerate baselines."
        )

    baseline = _load_baseline_image(target)
    captured_rgba = captured.convert("RGBA")
    if baseline.size != captured_rgba.size:
        raise AssertionError(
            f"Baseline size {baseline.size} does not match captured image size {captured_rgba.size}"
        )

    diff = ImageChops.difference(baseline, captured_rgba)
    if diff_output is not None:
        diff_output.parent.mkdir(parents=True, exist_ok=True)
        diff.save(diff_output)

    stats = ImageStat.Stat(diff)
    rms_values = stats.rms
    overall = math.sqrt(sum(value * value for value in rms_values) / len(rms_values))

    if overall > tolerance:
        raise AssertionError(
            f"Captured frame deviates from baseline by RMS={overall:.2f}, tolerance={tolerance:.2f}"
        )
    return overall


def wait_for_property(
    obj: QObject,
    name: str,
    predicate: Callable[[object], bool],
    qapp,
    *,
    timeout_ms: int = 2000,
) -> object:
    """Wait until ``predicate`` returns ``True`` for ``obj.property(name)``."""

    def _property_ready() -> bool:
        return predicate(obj.property(name))

    if not _wait_until(_property_ready, qapp, timeout_ms=timeout_ms):
        raise TimeoutError(
            f"Property '{name}' did not satisfy predicate within timeout"
        )
    return obj.property(name)


__all__ = [
    "QMLScene",
    "capture_window_image",
    "compare_with_baseline",
    "encode_baseline_from_png",
    "_load_baseline_image",
    "ensure_simulation_panel_ready",
    "load_main_scene",
    "push_updates",
    "wait_for_property",
]


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Utilities for screenshot baselines")
    sub = parser.add_subparsers(dest="command")
    encode = sub.add_parser(
        "encode-baseline",
        help="Convert a PNG file into the textual baseline representation.",
    )
    encode.add_argument("png_path", type=Path)
    encode.add_argument("baseline_path", type=Path)
    return parser


def _main(argv: list[str] | None = None) -> int:
    parser = _build_cli()
    args = parser.parse_args(argv)
    if args.command == "encode-baseline":
        encode_baseline_from_png(args.png_path, args.baseline_path)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(_main())
