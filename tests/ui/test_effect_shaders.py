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
    """Each shader must start with a #version directive without BOM/whitespace."""

    data = shader_file.read_bytes()
    assert not data.startswith(
        b"\xef\xbb\xbf"
    ), f"{shader_file} should not contain a UTF-8 BOM"

    text = data.decode("utf-8")
    assert text.startswith("#version"), (
        f"{shader_file} must start with #version on the very first line"
    )

    first_line = text.splitlines()[0]
    assert first_line.startswith("#version"), (
        f"{shader_file} first line must contain #version"
    )


@pytest.mark.gui
@pytest.mark.parametrize("qml_file", EFFECT_FILES)
def test_effect_shaders_load_without_version_warning(qapp, qml_file: Path) -> None:
    """Ensure loading the effect components emits no #version warnings."""

    pytest.importorskip(
        "PySide6.QtCore",
        reason="PySide6 QtCore module is required to verify shader warnings",
        exc_type=ImportError,
    )
    pytest.importorskip(
        "PySide6.QtQml",
        reason="PySide6 QtQml module is required to verify shader warnings",
        exc_type=ImportError,
    )
    pytest.importorskip(
        "PySide6.QtQuick3D",
        reason="PySide6 QtQuick3D module is required to instantiate effects",
        exc_type=ImportError,
    )

    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlApplicationEngine

    engine = QQmlApplicationEngine()
    engine.addImportPath(str((REPO_ROOT / "assets" / "qml").resolve()))

    qml_url = QUrl.fromLocalFile(str(qml_file.resolve()))
    engine.load(qml_url)

    try:
        qapp.processEvents()
        assert engine.rootObjects(), f"{qml_file} should instantiate a root object"

        version_warnings = [
            warning
            for warning in engine.warnings()
            if "#version must appear first" in warning.description()
        ]
        assert not version_warnings, (
            "Qt reported '#version must appear first' while loading "
            f"{qml_file}: "
            + "; ".join(warning.description() for warning in version_warnings)
        )
    finally:
        engine.deleteLater()


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


def test_profiler_toggle_available(monkeypatch) -> None:
    """Diagnostics profiler module should expose the overlay toggle state."""

    from src.diagnostics import profiler as profiler_module

    class _DummySettingsManager:
        def get(self, path, default=None):
            if path == "diagnostics":
                return {"signal_trace": {"overlay_enabled": True, "history_limit": 64}}
            return default

    profiler_module._reset_profiler_state_for_tests()
    monkeypatch.setattr(profiler_module, "get_settings_manager", lambda: _DummySettingsManager())

    defaults = profiler_module.get_profiler_overlay_defaults()
    payload = defaults["signal_trace"]
    assert payload["overlay_enabled"] is True
    assert payload["overlayEnabled"] is True
    assert payload["history_limit"] == 64
    assert "recordedAt" in payload

    state = profiler_module.load_profiler_overlay_state()
    assert state.overlay_enabled is True
    assert state.to_payload()["overlayEnabled"] is True

    updated = profiler_module.record_profiler_overlay(False, source="pytest")
    assert updated.overlay_enabled is False
    assert updated.to_payload()["overlayEnabled"] is False

    profiler_module._reset_profiler_state_for_tests()
