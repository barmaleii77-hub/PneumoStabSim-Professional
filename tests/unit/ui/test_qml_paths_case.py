"""Validate that QML resources use correct casing and resolved URLs."""

from __future__ import annotations

from pathlib import Path

from src.ui.main_window_pkg.ui_setup import (
    QML_ABSOLUTE_ROOT,
    QML_RELATIVE_ROOT,
    UISetup,
)

PROJECT_ROOT = QML_ABSOLUTE_ROOT.parent.parent


def _assert_case_sensitive(path: Path) -> None:
    """Ensure each segment of ``path`` matches the filesystem casing."""

    relative = path.relative_to(PROJECT_ROOT)
    current = PROJECT_ROOT
    for part in relative.parts:
        entries = {entry.name for entry in current.iterdir()}
        assert part in entries, f"Path segment '{part}' not found under '{current}'"
        current = current / part


def test_supported_scene_paths_use_correct_case() -> None:
    """All supported scenes must exist and match filesystem casing exactly."""

    for scene_path in UISetup._SUPPORTED_SCENES.values():
        assert scene_path.is_absolute(), "Scene paths must be absolute"
        assert scene_path.exists(), f"Scene file is missing: {scene_path}"
        _assert_case_sensitive(scene_path)


def test_qml_root_constants_point_to_existing_directory() -> None:
    """The QML root constants should be aligned with the repository layout."""

    assert QML_ABSOLUTE_ROOT.is_absolute()
    assert QML_ABSOLUTE_ROOT.exists()
    assert QML_RELATIVE_ROOT.as_posix() == "assets/qml"
    _assert_case_sensitive(QML_ABSOLUTE_ROOT)


def test_effects_resolve_shader_directories() -> None:
    """Fog and post-processing effects must rely on Qt.resolvedUrl bindings."""

    effects_dir = QML_ABSOLUTE_ROOT / "effects"
    for qml_file in ("FogEffect.qml", "PostEffects.qml"):
        contents = (effects_dir / qml_file).read_text(encoding="utf-8")
        assert 'Qt.resolvedUrl("../../shaders/effects/")' in contents
        assert 'Qt.resolvedUrl("../../shaders/")' in contents
