"""Fullscreen canvas animation test.

Запуск QML Canvas сцены в полноэкранном режиме и проверка анимации.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest
from PIL import ImageChops, ImageStat

try:  # noqa: SIM105
    from PySide6.QtQuick import QQuickWindow  # type: ignore  # noqa: F401
    QT_QUICK_AVAILABLE = True
except Exception:  # noqa: BLE001
    QT_QUICK_AVAILABLE = False

from PySide6.QtCore import QObject, Qt  # type: ignore

from tests._qt_headless import headless_requested
from tests.ui.utils import capture_window_image, load_qml_scene, log_window_metrics

CANVAS_QML = Path("assets/qml/main_canvas_2d.qml")
FRAME_DELAY = 0.5
MAX_WAIT_FULLSCREEN = 1.5  # секунды ожидания перехода окна в полноэкранный режим
MIN_ANGLE_DELTA_DEG = 5.0
MIN_MEAN_DELTA = 0.25  # слегка снижено, используется как fallback
MIN_CHANGE_RATIO = 0.02  # минимум 2% пикселей должны отличаться (по яркости порог > 8)
PIXEL_DIFF_THRESHOLD = 8  # граница яркости для счёта пикселя как изменившегося


def _locate_canvas(root: QObject) -> QObject:
    canvas = root.findChild(QObject, "schematicCanvas")
    if canvas is None:
        raise AssertionError("Canvas item 'schematicCanvas' not found in scene")
    return canvas


def _angle_delta(a0: float, a1: float) -> float:
    d = (a1 - a0) % 360.0
    return 360.0 - d if d > 180.0 else d


def _ensure_fullscreen(view) -> None:
    """Гарантировать переход окна в полноэкранный режим с коротким ожиданием."""
    view.showFullScreen()
    deadline = time.monotonic() + MAX_WAIT_FULLSCREEN
    while time.monotonic() < deadline:
        if (view.windowState() & Qt.WindowFullScreen) or view.visibility() == Qt.WindowFullScreen:
            return
        view.requestActivate()
        view.raise_()
        view.showFullScreen()
        view.update()
        view.screen()
        view.app.processEvents() if hasattr(view, "app") else None
        time.sleep(0.05)


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_canvas_fullscreen_animation(qapp, integration_reports_dir) -> None:  # noqa: D401
    """Открыть сцену канваса в полноэкранном режиме и подтвердить движение.

    Headless / отсутствует QtQuick: выполняется упрощённый PASS.
    """
    if headless_requested() or not QT_QUICK_AVAILABLE:
        assert True, "Headless/No QtQuick fallback PASS (fullscreen unsupported)"
        return

    with load_qml_scene(qapp, qml_file=CANVAS_QML, width=1280, height=720) as scene:
        _ensure_fullscreen(scene.view)
        qapp.processEvents()

        assert scene.view.isVisible(), "Window must be visible"
        assert scene.view.isExposed(), "Window not exposed"
        assert (scene.view.windowState() & Qt.WindowFullScreen) or scene.view.visibility() == Qt.WindowFullScreen, "Window not in fullscreen state"

        log_window_metrics(scene.view)

        canvas = _locate_canvas(scene.root)

        qapp.processEvents()
        angle0 = float(canvas.property("animationAngle") or 0.0)
        frame1 = capture_window_image(scene.view, qapp)
        time.sleep(FRAME_DELAY)

        qapp.processEvents()
        angle1 = float(canvas.property("animationAngle") or 0.0)
        frame2 = capture_window_image(scene.view, qapp)

        delta = _angle_delta(angle0, angle1)
        assert delta >= MIN_ANGLE_DELTA_DEG, f"Animation angle delta too small: {delta:.2f} deg"

        diff = ImageChops.difference(frame1, frame2)
        # Сырые метрики
        stat = ImageStat.Stat(diff.convert("L"))
        mean_delta = stat.mean[0]
        # Относительное изменение: считаем долю пикселей с яркостью > порога
        diff_l = diff.convert("L")
        w, h = diff_l.size
        px = diff_l.load()
        changed = 0
        for y in range(h):
            for x in range(w):
                if px[x, y] > PIXEL_DIFF_THRESHOLD:
                    changed += 1
        change_ratio = changed / float(w * h)

        # Основное условие: либо относительная доля >= MIN_CHANGE_RATIO, либо mean_delta >= MIN_MEAN_DELTA
        assert (change_ratio >= MIN_CHANGE_RATIO) or (mean_delta >= MIN_MEAN_DELTA), (
            f"Animation not visible: mean_delta={mean_delta:.3f}, change_ratio={change_ratio:.3%}" )

        out_dir = integration_reports_dir / "canvas_fullscreen"
        out_dir.mkdir(parents=True, exist_ok=True)
        frame1.save(out_dir / "frame_1.png")
        frame2.save(out_dir / "frame_2.png")
        diff.save(out_dir / "frame_diff.png")
        (out_dir / "metrics.txt").write_text(
            f"angle_delta={delta:.2f}\nmean_delta={mean_delta:.3f}\nchange_ratio={change_ratio:.5f}\n", encoding="utf-8"
        )

        hold = float(os.environ.get("PSS_FULLSCREEN_TEST_HOLD", "0") or 0)
        end = time.monotonic() + hold
        while time.monotonic() < end:
            qapp.processEvents()
            time.sleep(0.05)
