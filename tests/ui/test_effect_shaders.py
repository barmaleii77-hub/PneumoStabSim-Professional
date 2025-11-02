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


REPO_ROOT = Path(__file__).resolve().parents[2]

EFFECT_FILES = [
    REPO_ROOT / "assets/qml/effects/FogEffect.qml",
    REPO_ROOT / "assets/qml/effects/PostEffects.qml",
]


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
