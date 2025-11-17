"""Visual regression test for the animated Canvas schematic (Windows-ready)."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from PIL import ImageChops, ImageStat

pytest.importorskip(
    "PySide6.QtQuick",
    reason="PySide6/QtQuick is required to render the Canvas schematic",
)

from PySide6.QtCore import QObject

from tests.ui.utils import capture_window_image, load_qml_scene, log_window_metrics

CANVAS_QML = Path("assets/qml/main_canvas_2d.qml")
FRAME_CAPTURE_DELAY = 0.6  # seconds between grabs to observe the animation


def _locate_canvas(root) -> QObject:
    canvas = root.findChild(QObject, "schematicCanvas")
    if canvas is None:
        raise AssertionError("schematicCanvas Canvas item is missing from the scene")
    return canvas


def _normalise_angle_delta(start: float, end: float) -> float:
    delta = (end - start) % 360.0
    if delta > 180.0:
        delta = 360.0 - delta
    return delta


def _maybe_hold_window(scene, qapp) -> None:
    hold_seconds = float(os.environ.get("PSS_CANVAS_TEST_HOLD_SECONDS", "0") or 0)
    if hold_seconds <= 0:
        return
    try:
        scene.view.raise_()
        scene.view.requestActivate()
    except Exception:
        pass
    deadline = time.monotonic() + hold_seconds
    while time.monotonic() < deadline:
        qapp.processEvents()
        time.sleep(0.05)


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_canvas_animation_renders_and_updates(qapp, integration_reports_dir) -> None:
    """Ensure the Canvas schematic renders visibly and animates across frames."""

    with load_qml_scene(qapp, qml_file=CANVAS_QML, width=960, height=540) as scene:
        log_window_metrics(scene.view)
        canvas = _locate_canvas(scene.root)

        # Capture the first frame and current animation angle
        qapp.processEvents()
        initial_angle = float(canvas.property("animationAngle") or 0.0)
        first_frame = capture_window_image(scene.view, qapp)

        # Allow the NumberAnimation to progress before taking the second frame
        time.sleep(FRAME_CAPTURE_DELAY)
        qapp.processEvents()
        updated_angle = float(canvas.property("animationAngle") or 0.0)
        second_frame = capture_window_image(scene.view, qapp)

        # Validate that the animation advanced in QML and visually on screen
        angle_delta = _normalise_angle_delta(initial_angle, updated_angle)
        assert angle_delta >= 5.0, (
            f"Animation angle delta too small: {angle_delta:.2f} degrees"
        )

        diff_image = ImageChops.difference(first_frame, second_frame)
        diff_stat = ImageStat.Stat(diff_image.convert("L"))
        mean_delta = diff_stat.mean[0]
        # Headless Linux runs tend to produce lower deltas than Windows desktops,
        # so we keep the threshold loose enough while still confirming motion.
        assert mean_delta >= 0.3, (
            "Canvas frames look identical; animation is not visible"
        )

        # Persist the captured frames for manual inspection on Windows desktops
        output_dir = integration_reports_dir / "canvas_animation"
        output_dir.mkdir(parents=True, exist_ok=True)
        first_path = output_dir / "canvas_frame_1.png"
        second_path = output_dir / "canvas_frame_2.png"
        diff_path = output_dir / "canvas_frame_diff.png"
        first_frame.save(first_path)
        second_frame.save(second_path)
        diff_image.save(diff_path)

        _maybe_hold_window(scene, qapp)
