from __future__ import annotations

from pathlib import Path

import pytest

from tools import validate_shaders


def _write_shader(base: Path, relative: str, content: str) -> None:
    target = base / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def test_validate_shaders_success(tmp_path: Path) -> None:
    shader_root = tmp_path / "shaders"

    _write_shader(shader_root, "effects/bloom.frag", "#version 450 core\nvoid main() {}\n")
    _write_shader(shader_root, "effects/bloom_fallback.frag", "#version 330 core\nvoid main() {}\n")
    _write_shader(shader_root, "post_effects/bloom_es.frag", "#version 300 es\nvoid main() {}\n")

    _write_shader(shader_root, "effects/fog.vert", "#version 450 core\nvoid main() {}\n")
    _write_shader(shader_root, "effects/fog_es.vert", "#version 300 es\nvoid main() {}\n")
    _write_shader(shader_root, "effects/fog.frag", "#version 450 core\nvoid main() {}\n")
    _write_shader(shader_root, "effects/fog_fallback.frag", "#version 330 core\nvoid main() {}\n")
    _write_shader(shader_root, "effects/fog_es.frag", "#version 300 es\nvoid main() {}\n")

    errors = validate_shaders.validate_shaders(shader_root)

    assert errors == []


def test_validate_shaders_reports_missing_gles_variant(tmp_path: Path) -> None:
    shader_root = tmp_path / "shaders"

    _write_shader(shader_root, "effects/ssao.frag", "#version 450 core\nvoid main() {}\n")
    _write_shader(shader_root, "effects/ssao_fallback.frag", "#version 330 core\nvoid main() {}\n")

    errors = validate_shaders.validate_shaders(shader_root)

    assert any("missing GLES variant" in message for message in errors)


def test_validate_shaders_reports_version_mismatch(tmp_path: Path) -> None:
    shader_root = tmp_path / "shaders"

    _write_shader(shader_root, "effects/dof.frag", "#version 450 core\nvoid main() {}\n")
    _write_shader(shader_root, "effects/dof_fallback.frag", "#version 330 core\nvoid main() {}\n")
    _write_shader(shader_root, "post_effects/dof_es.frag", "#version 100 es\nvoid main() {}\n")

    errors = validate_shaders.validate_shaders(shader_root)

    assert any("expected '#version 300 es'" in message for message in errors)
