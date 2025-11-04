"""Tests for GLES fallback shader selection in QML effects."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QJSValue

pytest.importorskip(
    "PySide6.QtWidgets",
    reason=(
        "PySide6.QtWidgets (libGL) is required for GLES fallback shader tests; install libgl1/libegl1"
    ),
    exc_type=ImportError,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SHADER_DIRS = (
    REPO_ROOT / "assets" / "shaders" / "effects",
    REPO_ROOT / "assets" / "shaders" / "post_effects",
)
SHADER_ROOT = REPO_ROOT / "assets" / "shaders"


os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")


def _build_manifest() -> dict[str, dict[str, object]]:
    manifest: dict[str, dict[str, object]] = {}
    for directory in SHADER_DIRS:
        for path in directory.iterdir():
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".frag", ".vert"}:
                continue
            relative_path = path.relative_to(SHADER_ROOT).as_posix()
            entry = manifest.get(path.name)
            if entry is None:
                manifest[path.name] = {
                    "enabled": True,
                    "path": relative_path,
                    "paths": [relative_path],
                }
                continue

            entry.setdefault("enabled", True)
            paths = entry.setdefault("paths", [])
            if relative_path not in paths:
                paths.append(relative_path)
            entry.setdefault("path", relative_path)
    return manifest


def _create_engine_with_manifest(
    manifest_overrides: dict[str, object] | None = None,
) -> QQmlEngine:
    engine = QQmlEngine()
    context = engine.rootContext()

    manifest = _build_manifest()
    if manifest_overrides:
        manifest.update(manifest_overrides)

    context.setContextProperty("qtGraphicsApiName", "opengl-es")
    context.setContextProperty("qtGraphicsApiRequiresDesktopShaders", False)
    context.setContextProperty("effectShaderManifest", manifest)
    return engine


def _create_component(engine: QQmlEngine, qml_path: Path) -> QQmlComponent:
    component = QQmlComponent(engine)
    component.loadUrl(QUrl.fromLocalFile(str(qml_path.resolve())))
    if component.status() != QQmlComponent.Ready:
        raise RuntimeError(f"Failed to load component {qml_path}: {component.errorString()}")
    return component


@pytest.mark.gui
def _normalize_url(value: object) -> str:
    if isinstance(value, QUrl):
        return value.toString()
    to_string = getattr(value, "toString", None)
    if callable(to_string):
        return str(to_string())
    return str(value)


def _to_variant_map(value: object) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, QJSValue):
        try:
            variant = value.toVariant()
        except AttributeError:  # pragma: no cover - defensive for PySide variations
            variant = None
        if isinstance(variant, dict):
            return variant
    if isinstance(value, dict):
        return value
    raise TypeError(f"Unsupported manifest container: {type(value)!r}")


def _to_sequence(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, QJSValue):
        try:
            variant = value.toVariant()
        except AttributeError:  # pragma: no cover - defensive for PySide variations
            variant = None
        if isinstance(variant, list):
            return variant
    if isinstance(value, (list, tuple)):
        return list(value)
    raise TypeError(f"Unsupported sequence container: {type(value)!r}")


def test_post_effects_prefers_fallback_when_gles_variant_missing(qapp) -> None:  # type: ignore[missing-type-doc]
    """If GLES variants are unavailable, PostEffects should switch to fallback shaders."""

    engine = _create_engine_with_manifest(
        {
            "bloom_es.frag": False,
            "bloom_gles.frag": False,
            "bloom_300es.frag": False,
        }
    )
    component = _create_component(engine, REPO_ROOT / "assets" / "qml" / "effects" / "PostEffects.qml")
    root = component.create()
    try:
        assert root.property("useGlesShaders") is True

        shader_url = _normalize_url(root.shaderPath("bloom.frag"))
        assert shader_url.endswith("bloom_fallback_es.frag")

        overrides = _to_variant_map(root.property("shaderCompatibilityOverrides"))
        assert overrides["bloom.frag"] is True
        assert root.property("forceDesktopShaderProfile") is False

        missing_variants = _to_variant_map(root.property("shaderVariantMissingWarnings"))
        assert missing_variants.get("bloom_es.frag") is True
    finally:
        root.deleteLater()


@pytest.mark.gui
def test_fog_effect_prefers_fallback_when_gles_variant_missing(qapp) -> None:  # type: ignore[missing-type-doc]
    """FogEffect should use fallback GLSL 330 shader when GLES resources are absent."""

    engine = _create_engine_with_manifest(
        {
            "fog_es.frag": False,
            "fog_gles.frag": False,
            "fog_300es.frag": False,
        }
    )
    component = _create_component(engine, REPO_ROOT / "assets" / "qml" / "effects" / "FogEffect.qml")
    root = component.create()
    try:
        assert root.property("useGlesShaders") is True

        shader_url = _normalize_url(root.shaderPath("fog.frag"))
        assert shader_url.endswith("fog_fallback_es.frag")

        assert root.property("forceDesktopShaderProfile") is False

        missing_variants = _to_variant_map(root.property("shaderVariantMissingWarnings"))
        assert missing_variants.get("fog_es.frag") is True
    finally:
        root.deleteLater()


@pytest.mark.gui
def test_fog_effect_activates_depth_fallback_when_forced(qapp) -> None:  # type: ignore[missing-type-doc]
    """FogEffect should engage fallback shader when depth textures are unavailable."""

    engine = _create_engine_with_manifest({})
    component = _create_component(engine, REPO_ROOT / "assets" / "qml" / "effects" / "FogEffect.qml")
    root = component.createWithInitialProperties({"forceDepthTextureUnavailable": True})
    try:
        assert root.property("depthTextureAvailable") is False
        assert root.property("fallbackDueToDepth") is True
        assert root.property("fallbackActive") is True

        active_shaders = _to_sequence(root.property("activePassShaders"))
        assert len(active_shaders) == 2
        fallback_shader = active_shaders[1]
        shader_url = _normalize_url(fallback_shader.property("shader"))
        assert shader_url.endswith("fog_fallback_es.frag")
    finally:
        root.deleteLater()
