"""Regression checks for QML effect shader bindings.

These tests enforce that the custom post-processing and fog effects continue to
use URL-based shader bindings compatible with Qt 6.9+ instead of the deprecated
`ShaderData` helper that caused runtime compilation failures when Qt tightened
its shader loader.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.ui.main_window_pkg.ui_setup import EFFECT_SHADER_DIRS, UISetup


REPO_ROOT = Path(__file__).resolve().parents[2]

EFFECT_FILES = [
    REPO_ROOT / "assets/qml/effects/FogEffect.qml",
    REPO_ROOT / "assets/qml/effects/PostEffects.qml",
]

SHADER_DIRS = [Path(directory) for directory in EFFECT_SHADER_DIRS]
SHADER_FILES = sorted(
    [
        shader
        for directory in SHADER_DIRS
        for pattern in ("*.frag", "*.vert")
        for shader in directory.glob(pattern)
    ]
)


@pytest.mark.parametrize("qml_file", EFFECT_FILES)
def test_effect_shaders_use_url_bindings(qml_file: Path) -> None:
    """Ensure fog and post-processing effects rely on URL-based shader sources."""
    source = qml_file.read_text(encoding="utf-8")

    # Guard against regressions that reintroduce ShaderData wrappers which are
    # incompatible with Qt 6.9+'s shader compiler.
    assert "ShaderData" not in source
    assert "shaderDataUrl" not in source

    # Verify that each effect continues to bind shaders via the helper
    # `shaderPath(...)` function, which produces Qt-compatible URLs.
    assert re.search(r"shader\s*:\s*(?:fogEffect|root)\.shaderPath", source)


@pytest.mark.parametrize("shader_file", SHADER_FILES)
def test_effect_shaders_use_lf_line_endings(shader_file: Path) -> None:
    """Ensure GLSL shader files keep LF endings to avoid CR-induced compiler errors."""

    data = shader_file.read_bytes()
    assert b"\r" not in data, f"{shader_file} contains Windows CR characters"


@pytest.mark.parametrize("shader_file", SHADER_FILES)
def test_effect_shaders_start_with_version(shader_file: Path) -> None:
    """The first non-empty line in each shader must start with #version."""

    text = shader_file.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        assert stripped.startswith("#version"), (
            f"{shader_file} must begin with a #version directive"
        )
        break
    else:
        pytest.fail(f"{shader_file} is empty or lacks a #version directive")


def test_effect_shader_manifest_matches_filesystem() -> None:
    """UISetup manifest should mirror the actual shader files on disk."""

    manifest = UISetup._build_effect_shader_manifest()
    expected = {
        path.name
        for directory in SHADER_DIRS
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in {".frag", ".vert"}
    }

    assert set(manifest.keys()) == expected
    assert all(manifest[name] for name in expected)
