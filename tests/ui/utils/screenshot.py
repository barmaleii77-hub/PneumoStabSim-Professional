"""Utilities for capturing deterministic Qt Quick frames in tests."""

from __future__ import annotations

import argparse
import base64
import io
import json
import json
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable

from PIL import Image, ImageChops, ImageStat

from PySide6.QtCore import QObject, Qt, QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlContext, QQmlFileSelector
from PySide6.QtQuick import QQuickView, QQuickWindow

from src.ui.qml_bridge import QMLBridge
from src.ui.scene_bridge import SceneBridge
from src.ui.startup import enforce_fixed_window_metrics
from tests._qt_headless import apply_headless_defaults
from tests._qt_headless import headless_requested

_ASSETS_IMPORT = Path("assets/qml").resolve()
_BASELINE_VERSION = 1


def _read_baseline_size(path: Path) -> tuple[int, int] | None:
    try:
        payload = json.loads(path.read_text())
    except Exception:
        return None

    size = payload.get("size") if isinstance(payload, dict) else None
    if (
        isinstance(size, (list, tuple))
        and len(size) == 2
        and all(isinstance(v, (int, float)) for v in size)
    ):
        return int(size[0]), int(size[1])

    return None


def _ensure_qt_environment() -> None:
    if headless_requested():
        apply_headless_defaults()

    # Ensure stable HiDPI scaling so captured screenshots match recorded baselines
    os.environ.setdefault("QT_SCALE_FACTOR", "1.5")
    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")


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

    def __enter__(self) -> QMLScene:
        return self

    def __exit__(self, exc_type, exc, tb) -> bool | None:
        self.close()
        return None


def _initialise_view(
    qapp,
    *,
    qml_path: Path,
    width: int = 800,
    height: int = 450,
    scene_bridge: SceneBridge | None = None,
) -> QMLScene:
    _ensure_qt_environment()
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
    enforce_fixed_window_metrics(view, width=width, height=height)
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
    baseline_path: Path | None = None,
) -> QMLScene:
    """Load the main QML entry point into an offscreen ``QQuickView``."""

    qml_path = Path(qml_file).resolve()
    if not qml_path.exists():
        raise FileNotFoundError(qml_path)

    baseline_size = _read_baseline_size(baseline_path) if baseline_path else None
    target_width, target_height = baseline_size if baseline_size else (width, height)

    return _initialise_view(
        qapp, qml_path=qml_path, width=target_width, height=target_height
    )


def load_qml_scene(
    qapp,
    *,
    qml_file: Path | str,
    width: int = 800,
    height: int = 450,
) -> QMLScene:
    """Load an arbitrary QML scene into a visible ``QQuickView``.

    This helper mirrors :func:`load_main_scene` but accepts an explicit QML file
    path so Windows desktop runs can preview bespoke scenes (e.g. animated
    Canvas schematics) without modifying the main entry point. The window is
    shown immediately to make the rendered content visible for manual
    inspection while still working in headless CI environments.
    """

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


def _grab_by_item(window: QQuickWindow, qapp, timeout_ms: int = 1500) -> QImage | None:
    item = None
    try:
        item = window.contentItem()
    except Exception:
        pass
    if item is None:
        try:
            item = window.property("contentItem")
        except Exception:
            item = None
    if item is None:
        try:
            item = window.property("rootObject")
        except Exception:
            item = None
    if item is None or not hasattr(item, "grabToImage"):
        return None

    try:
        result = item.grabToImage()
    except Exception:
        return None

    ready = [False]

    def _on_ready():
        ready[0] = True

    try:
        result.ready.connect(_on_ready)  # type: ignore[attr-defined]
    except Exception:
        # If signal not available, fall back to polling below
        pass

    deadline = time.monotonic() + max(0, timeout_ms) / 1000.0
    while time.monotonic() < deadline and not ready[0]:
        _process_events(qapp, iterations=1)
        time.sleep(0.01)
        # some bindings don't emit ready() reliably; check image size
        try:
            img = result.image()
            if isinstance(img, QImage) and not img.isNull():
                ready[0] = True
                break
        except Exception:
            pass

    try:
        image = result.image()
        if isinstance(image, QImage) and not image.isNull():
            return image
    except Exception:
        return None
    return None


def capture_window_image(
    window: QQuickWindow, qapp, *, settle_iterations: int = 4
) -> Image.Image:
    """Grab the current framebuffer of ``window`` as a Pillow image.

    В headless/offscreen режимах QSG может отложить первый кадр. Функция
    активно запрашивает обновление и выполняет несколько попыток захвата. Если
    кадр отсутствует, применяется резервный путь через QQuickItem.grabToImage().
    """

    # Первичная обработка очереди событий
    _process_events(qapp, iterations=max(1, settle_iterations))

    # До 60 попыток (~1 сек) с активным обновлением окна
    attempts = 60
    for _ in range(attempts):
        image = window.grabWindow()
        if not image.isNull():
            return _qimage_to_pillow(image)
        try:
            window.requestUpdate()
        except Exception:
            pass
        _process_events(qapp, iterations=1)
        time.sleep(0.01)

    # Резервный способ: захват через root/content item
    fallback = _grab_by_item(window, qapp, timeout_ms=2000)
    if isinstance(fallback, QImage) and not fallback.isNull():
        return _qimage_to_pillow(fallback)

    # Последняя попытка прямого grabWindow
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


def _prepare_images_for_diff(
    captured: Image.Image, baseline_path: Path | str
) -> tuple[Image.Image, Image.Image]:
    target = Path(baseline_path)
    if not target.exists():
        raise FileNotFoundError(
            f"Baseline image '{target}' is missing. Run the update procedure to regenerate baselines."
        )

    baseline = _load_baseline_image(target)
    captured_rgba = captured.convert("RGBA")

    if baseline.size != captured_rgba.size:
        bw, bh = baseline.size
        cw, ch = captured_rgba.size
        # Плавающий коэффициент масштабирования
        ratio_w = cw / bw
        ratio_h = ch / bh
        if abs(ratio_w - ratio_h) < 1e-6:
            ratio = ratio_w
            if ratio in {1.25, 1.5, 1.75, 2.0, 3.0}:
                # Масштабируем до baseline для визуального сравнения
                captured_rgba = captured_rgba.resize(baseline.size, Image.BICUBIC)
            else:
                raise AssertionError(
                    f"Unsupported scaling ratio {ratio:.4f}; baseline {baseline.size} vs captured {captured_rgba.size}"
                )
        else:
            raise AssertionError(
                f"Baseline size {baseline.size} does not match captured image size {captured_rgba.size}"
            )

    return baseline, captured_rgba


def compare_with_baseline(
    captured: Image.Image,
    baseline_path: Path | str,
    *,
    tolerance: float = 3.5,
    diff_output: Path | None = None,
) -> float:
    """Compare ``captured`` image against the stored baseline.

    HiDPI нормализация: если framebuffer масштабирован (например 960x540 при baseline 640x360),
    то вычисляется ratio = captured.width / baseline.width (должен совпадать с captured.height / baseline.height).
    Допустимые коэффициенты: 1.25, 1.5, 1.75, 2.0, 3.0.
    При совпадении выполняем ресайз вниз и сравниваем содержимое.
    """

    baseline, captured_rgba = _prepare_images_for_diff(captured, baseline_path)
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


def measure_rms_difference(captured: Image.Image, baseline_path: Path | str) -> float:
    """Return RMS deviation between ``captured`` and the encoded baseline."""

    baseline, captured_rgba = _prepare_images_for_diff(captured, baseline_path)
    diff = ImageChops.difference(baseline, captured_rgba)
    stats = ImageStat.Stat(diff)
    return math.sqrt(sum(value * value for value in stats.rms) / len(stats.rms))


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
    "measure_rms_difference",
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


def log_window_metrics(window: QQuickWindow) -> dict[str, int]:
    """Записать метрики окна (width/height/contentSize) и вернуть их.

    Используется тестами для диагностики расхождений baseline размеров.
    """
    metrics = {
        "width": int(getattr(window, "width", lambda: 0)()),
        "height": int(getattr(window, "height", lambda: 0)()),
    }
    try:
        item = window.contentItem()
        if item is not None:
            metrics["contentWidth"] = int(getattr(item, "width", 0))
            metrics["contentHeight"] = int(getattr(item, "height", 0))
    except Exception:
        pass
    print("[screenshot] window metrics:", metrics)
    return metrics


__all__.append("log_window_metrics")
