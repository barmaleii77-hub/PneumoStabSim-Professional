"""Graphics tests for shader log parsing and baseline comparisons."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops

from tools import check_shader_logs


def _create_render(output_path: Path, color: tuple[int, int, int]) -> None:
    image = Image.new("RGB", (8, 8), color=color)
    image.save(output_path)


def test_shader_log_analysis(tmp_path):
    log = tmp_path / "shader.log"
    log.write_text(
        """
        qsb --glsl 450 --msl 12 shader.vert
        ERROR: failed to compile vertex shader
        WARNING: using fallback variant
        """,
        encoding="utf-8",
    )

    report = check_shader_logs.analyse_shader_log(log)
    assert report["error_count"] == 1
    assert report["warning_count"] == 1


def test_baseline_image_comparison(baseline_images_dir: Path, tmp_path):
    reference_path = baseline_images_dir / "qt_scene_reference.png"
    candidate_path = tmp_path / "render.png"
    _create_render(candidate_path, (120, 160, 200))

    reference = Image.open(reference_path)
    candidate = Image.open(candidate_path)

    difference = ImageChops.difference(reference, candidate)
    assert difference.getbbox() is None, (
        f"Изображения отличаются в области: {difference.getbbox()}"
    )

    altered_path = tmp_path / "render_changed.png"
    _create_render(altered_path, (110, 150, 190))
    altered = Image.open(altered_path)
    diff_altered = ImageChops.difference(reference, altered)
    assert diff_altered.getbbox() is not None
