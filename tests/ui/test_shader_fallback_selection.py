"""Tests for GLES fallback shader selection in QML effects."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.helpers import require_qt_modules

require_qt_modules(
    "PySide6.QtWidgets",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtQml",
    "PySide6.QtQuick",
)

from PySide6.QtCore import QTimer, Qt, QUrl, qInstallMessageHandler
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtQml import QQmlComponent, QQmlEngine, QJSValue
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface
from PySide6.QtWidgets import QApplication

from src.app_runner import ApplicationRunner


REPO_ROOT = Path(__file__).resolve().parents[2]
SHADER_DIRS = (REPO_ROOT / "assets" / "shaders" / "effects",)
SHADER_ROOT = REPO_ROOT / "assets" / "shaders"


os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")
os.environ.setdefault("QSG_RHI_BACKEND", "opengl")


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
    *,
    graphics_api_name: str = "opengl-es",
    requires_desktop: bool | None = None,
) -> QQmlEngine:
    engine = QQmlEngine()
    context = engine.rootContext()

    manifest = _build_manifest()
    if manifest_overrides:
        manifest.update(manifest_overrides)

    context.setContextProperty("qtGraphicsApiName", graphics_api_name)
    if requires_desktop is None:
        requires_desktop = False
    context.setContextProperty("qtGraphicsApiRequiresDesktopShaders", requires_desktop)
    context.setContextProperty("effectShaderManifest", manifest)
    return engine


_SURFACE_CONFIGURED = False


def _configure_opengl_surface() -> None:
    global _SURFACE_CONFIGURED
    if _SURFACE_CONFIGURED:
        return

    runner = ApplicationRunner(QApplication, qInstallMessageHandler, Qt, QTimer)
    runner._surface_format_configured = False
    runner._configure_default_surface_format()
    _SURFACE_CONFIGURED = True


def _create_component(engine: QQmlEngine, qml_path: Path) -> QQmlComponent:
    component = QQmlComponent(engine)
    component.loadUrl(QUrl.fromLocalFile(str(qml_path.resolve())))
    if component.status() != QQmlComponent.Ready:
        raise RuntimeError(
            f"Failed to load component {qml_path}: {component.errorString()}"
        )
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
    component = _create_component(
        engine, REPO_ROOT / "assets" / "qml" / "effects" / "PostEffects.qml"
    )
    root = component.create()
    try:
        assert root.property("useGlesShaders") is True

        shader_url = _normalize_url(root.shaderPath("bloom.frag"))
        assert shader_url.endswith("bloom_fallback_es.frag")

        overrides = _to_variant_map(root.property("shaderCompatibilityOverrides"))
        assert overrides["bloom.frag"] is True
        assert root.property("forceDesktopShaderProfile") is False

        missing_variants = _to_variant_map(
            root.property("shaderVariantMissingWarnings")
        )
        assert missing_variants.get("bloom_es.frag") is True
    finally:
        root.deleteLater()


@pytest.mark.gui
def test_post_effects_disables_pass_shaders_when_effects_off(qapp) -> None:  # type: ignore[missing-type-doc]
    """Disabling a post-effect should remove its shaders from the render passes."""

    engine = _create_engine_with_manifest({})
    component = _create_component(
        engine, REPO_ROOT / "assets" / "qml" / "effects" / "PostEffects.qml"
    )
    root = component.create()
    assert root is not None, "Expected PostEffects to instantiate"

    try:
        effects = _to_sequence(root.property("effectList"))
        assert effects, "PostEffects should expose the list of effect instances"
        assert len(effects) >= 4, "Expected four post-processing effects"

        def _shader_counts(effect_object: object) -> list[int]:
            if not hasattr(effect_object, "property"):
                return []
            passes = _to_sequence(effect_object.property("passes"))
            if not passes:
                return []
            counts: list[int] = []
            for pass_object in passes:
                if hasattr(pass_object, "property"):
                    pass_shaders = _to_sequence(pass_object.property("shaders"))
                    counts.append(len(pass_shaders))
                else:
                    counts.append(0)
            return counts

        bloom_effect = effects[0]
        root.setProperty("bloomEnabled", True)
        qapp.processEvents()
        enabled_counts = _shader_counts(bloom_effect)
        if not any(count > 0 for count in enabled_counts):
            pytest.fail(
                (
                    "Bloom shaders unavailable in the current OpenGL configuration. "
                    "Provision OpenGL-capable rendering by running "
                    "`python -m tools.cross_platform_test_prep --use-uv --run-tests`."
                ),
                pytrace=False,
            )

        root.setProperty("bloomEnabled", False)
        qapp.processEvents()

        toggle_sequence = [
            ("bloomEnabled", 0),
            ("ssaoEnabled", 1),
            ("depthOfFieldEnabled", 2),
            ("motionBlurEnabled", 3),
        ]
        for property_name, _ in toggle_sequence:
            root.setProperty(property_name, False)
        qapp.processEvents()

        for property_name, index in toggle_sequence:
            counts = _shader_counts(effects[index])
            assert all(count == 0 for count in counts), (
                f"{property_name} should produce no pass shaders when disabled"
            )
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


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
    component = _create_component(
        engine, REPO_ROOT / "assets" / "qml" / "effects" / "FogEffect.qml"
    )
    root = component.create()
    try:
        assert root.property("useGlesShaders") is True

        shader_url = _normalize_url(root.shaderPath("fog.frag"))
        assert shader_url.endswith("fog_fallback_es.frag")

        assert root.property("forceDesktopShaderProfile") is False

        missing_variants = _to_variant_map(
            root.property("shaderVariantMissingWarnings")
        )
        assert missing_variants.get("fog_es.frag") is True
    finally:
        root.deleteLater()


@pytest.mark.gui
def test_fog_effect_activates_depth_fallback_when_forced(qapp) -> None:  # type: ignore[missing-type-doc]
    """FogEffect should engage fallback shader when depth textures are unavailable."""

    engine = _create_engine_with_manifest({})
    component = _create_component(
        engine, REPO_ROOT / "assets" / "qml" / "effects" / "FogEffect.qml"
    )
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


@pytest.mark.gui
def test_fog_effect_desktop_backend_avoids_fallback(qapp) -> None:  # type: ignore[missing-type-doc]
    """FogEffect should stay on the primary shader pipeline under the OpenGL RHI backend."""

    _configure_opengl_surface()

    engine = _create_engine_with_manifest(
        graphics_api_name="opengl",
        requires_desktop=True,
    )
    component = _create_component(
        engine, REPO_ROOT / "assets" / "qml" / "effects" / "FogEffect.qml"
    )
    root = component.create()
    try:
        qapp.processEvents()

        assert QQuickWindow.graphicsApi() == QSGRendererInterface.GraphicsApi.OpenGLRhi

        format_ = QSurfaceFormat.defaultFormat()
        assert format_.depthBufferSize() >= 24
        assert format_.stencilBufferSize() >= 8

        assert root.property("fallbackActive") is False
        assert root.property("enforceLegacyFallbackShaders") is False
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()


@pytest.mark.gui
def test_depth_of_field_primary_pipeline_active(qapp) -> None:  # type: ignore[missing-type-doc]
    """Depth of field effect should compile without engaging compatibility fallbacks."""

    _configure_opengl_surface()

    engine = _create_engine_with_manifest(
        graphics_api_name="opengl",
        requires_desktop=True,
    )
    component = _create_component(
        engine, REPO_ROOT / "assets" / "qml" / "effects" / "PostEffects.qml"
    )
    root = component.create()
    try:
        root.setProperty("depthOfFieldEnabled", True)
        qapp.processEvents()

        assert root.property("useGlesShaders") is False
        assert root.property("depthOfFieldDepthTextureAvailable") is True
        assert root.property("depthOfFieldFallbackActive") is False
        assert not root.property("legacyFallbackReason")
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
