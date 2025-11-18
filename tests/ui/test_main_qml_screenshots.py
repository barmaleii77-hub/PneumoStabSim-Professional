"""Regression tests validating rendered frames for ``assets/qml/main.qml``."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtQuick", reason="PySide6 is required to capture QtQuick screenshots"
)

from tests.ui.utils import (
    capture_window_image,
    compare_with_baseline,
    ensure_simulation_panel_ready,
    load_main_scene,
    measure_rms_difference,
    push_updates,
    wait_for_property,
    log_window_metrics,
)

BASELINE_DIR = Path("tests/ui/baselines")
DEFAULT_BASELINE = BASELINE_DIR / "main_default.json"
ANIMATION_RUNNING_BASELINE = BASELINE_DIR / "main_animation_running.json"


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_main_scene_matches_default_baseline(qapp, integration_reports_dir) -> None:
    """The default scene should match the recorded baseline frame."""

    with load_main_scene(
        qapp, width=640, height=360, baseline_path=DEFAULT_BASELINE
    ) as scene:
        ensure_simulation_panel_ready(scene, qapp)
        log_window_metrics(scene.view)
        image = capture_window_image(scene.view, qapp)
        output_dir = integration_reports_dir / "ui_screenshots"
        output_dir.mkdir(parents=True, exist_ok=True)
        png_artifact = output_dir / DEFAULT_BASELINE.with_suffix(".png").name
        image.save(png_artifact)
        compare_with_baseline(
            image,
            DEFAULT_BASELINE,
            tolerance=4.0,
            diff_output=png_artifact.with_suffix(".diff.png"),
        )


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_main_scene_animation_running_baseline(qapp, integration_reports_dir) -> None:
    """Activating the animation flag must update the simulation panel status."""

    with load_main_scene(
        qapp, width=640, height=360, baseline_path=DEFAULT_BASELINE
    ) as scene:
        panel = ensure_simulation_panel_ready(scene, qapp)
        log_window_metrics(scene.view)
        push_updates(
            scene.root,
            {
                "simulation": {
                    "animation": {"is_running": True},
                    "status": "running",
                }
            },
        )
        push_updates(scene.root, {"animation": {"is_running": True}})

        wait_for_property(panel, "simulationRunning", bool, qapp, timeout_ms=3000)

        image = capture_window_image(scene.view, qapp)
        output_dir = integration_reports_dir / "ui_screenshots"
        output_dir.mkdir(parents=True, exist_ok=True)
        png_artifact = output_dir / ANIMATION_RUNNING_BASELINE.with_suffix(".png").name
        image.save(png_artifact)
        compare_with_baseline(
            image,
            ANIMATION_RUNNING_BASELINE,
            tolerance=4.5,
            diff_output=png_artifact.with_suffix(".diff.png"),
        )


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_post_effects_bypass_toggle_restores_baseline(qapp, integration_reports_dir) -> None:
    """Bypassing post-effects should change the frame and return to baseline after recovery."""

    with load_main_scene(
        qapp, width=640, height=360, baseline_path=DEFAULT_BASELINE
    ) as scene:
        ensure_simulation_panel_ready(scene, qapp)

        image = capture_window_image(scene.view, qapp)
        output_dir = integration_reports_dir / "ui_screenshots"
        output_dir.mkdir(parents=True, exist_ok=True)
        baseline_png = output_dir / DEFAULT_BASELINE.with_suffix(".png").name
        image.save(baseline_png)
        compare_with_baseline(
            image,
            DEFAULT_BASELINE,
            tolerance=4.0,
            diff_output=baseline_png.with_suffix(".diff.png"),
        )

        push_updates(
            scene.root,
            {"effects": {"effects_bypass": True, "effects_bypass_reason": "test toggle"}},
        )
        wait_for_property(scene.root, "postProcessingBypassed", bool, qapp)

        bypassed = capture_window_image(scene.view, qapp)
        bypass_png = output_dir / "main_bypass.png"
        bypassed.save(bypass_png)
        rms_delta = measure_rms_difference(bypassed, DEFAULT_BASELINE)
        assert rms_delta > 1.5, "Bypassing post-effects should materially alter the frame"

        push_updates(
            scene.root,
            {"effects": {"effects_bypass": False, "effects_bypass_reason": ""}},
        )
        wait_for_property(scene.root, "postProcessingBypassed", lambda v: v is False, qapp)

        recovered = capture_window_image(scene.view, qapp)
        recovered_png = output_dir / "main_bypass_recovered.png"
        recovered.save(recovered_png)
        compare_with_baseline(
            recovered,
            DEFAULT_BASELINE,
            tolerance=4.2,
            diff_output=recovered_png.with_suffix(".diff.png"),
        )
