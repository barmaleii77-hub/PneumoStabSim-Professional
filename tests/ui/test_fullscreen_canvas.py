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

pytest.importorskip("PySide6.QtQuick", reason="PySide6 / QtQuick required")

from PySide6.QtCore import QObject, Qt  # <== добавлен Qt для корректной проверки состояния окна

from tests._qt_headless import headless_requested
from tests.ui.utils import capture_window_image, load_qml_scene, log_window_metrics

CANVAS_QML = Path("assets/qml/main_canvas_2d.qml")
FRAME_DELAY = 0.5
MAX_WAIT_FULLSCREEN = 1.5  # секунды ожидания перехода окна в полноэкранный режим


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
    # Ждём пока установится WindowFullScreen флаг или visibility
    while time.monotonic() < deadline:
        if (view.windowState() & Qt.WindowFullScreen) or view.visibility() == Qt.WindowFullScreen:
            return
        view.requestActivate()
        view.raise_()
        view.showFullScreen()  # повторно на случай платформенных задержек
        view.update()
        view.screen()  # доступ к экрану для прогонки цикла сообщений
        view.app.processEvents() if hasattr(view, "app") else None
        time.sleep(0.05)
    # Финальная проверка всё равно выполнится тестом


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
@pytest.mark.skipif(headless_requested(), reason="Fullscreen preview skipped on headless backends")
def test_canvas_fullscreen_animation(qapp, integration_reports_dir) -> None:
    """Открыть сцену канваса в полноэкранном режиме и подтвердить движение."""
    with load_qml_scene(qapp, qml_file=CANVAS_QML, width=1280, height=720) as scene:
        _ensure_fullscreen(scene.view)
        qapp.processEvents()

        assert scene.view.isVisible(), "Window must be visible"
        assert scene.view.isExposed(), "Window not exposed"
        # Корректная проверка полноэкранного режима через битовый флаг Qt.WindowFullScreen
        assert (scene.view.windowState() & Qt.WindowFullScreen) or scene.view.visibility() == Qt.WindowFullScreen, "Window not in fullscreen state"

        log_window_metrics(scene.view)

        canvas = _locate_canvas(scene.root)

        # First frame
        qapp.processEvents()
        angle0 = float(canvas.property("animationAngle") or 0.0)
        frame1 = capture_window_image(scene.view, qapp)
        time.sleep(FRAME_DELAY)

        # Second frame
        qapp.processEvents()
        angle1 = float(canvas.property("animationAngle") or 0.0)
        frame2 = capture_window_image(scene.view, qapp)

        delta = _angle_delta(angle0, angle1)
        assert delta >= 5.0, f"Animation angle delta too small: {delta:.2f} deg"

        diff = ImageChops.difference(frame1, frame2)
        stat = ImageStat.Stat(diff.convert("L"))
        mean_delta = stat.mean[0]
        assert mean_delta >= 0.3, "Frames difference too small; animation not visible"

        out_dir = integration_reports_dir / "canvas_fullscreen"
        out_dir.mkdir(parents=True, exist_ok=True)
        frame1.save(out_dir / "frame_1.png")
        frame2.save(out_dir / "frame_2.png")
        diff.save(out_dir / "frame_diff.png")

        hold = float(os.environ.get("PSS_FULLSCREEN_TEST_HOLD", "0") or 0)
        end = time.monotonic() + hold
        while time.monotonic() < end:
            qapp.processEvents()
            time.sleep(0.05)
