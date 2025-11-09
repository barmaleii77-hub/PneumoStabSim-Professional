from __future__ import annotations

from pathlib import Path

import pytest

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine


QML_PATH = Path("assets/qml/effects/SceneEnvironmentController.qml")

pytestmark = pytest.mark.usefixtures("qt_runtime_ready")


def test_scene_environment_controller_applies_initial_defaults(qapp, settings_manager):
    try:
        from src.ui.main_window_pkg.ui_setup import UISetup
    except ImportError as exc:  # pragma: no cover - import behaviour depends on Qt packaging
        pytest.fail(
            "UISetup dependencies unavailable. Install Qt runtime via "
            "`python -m tools.cross_platform_test_prep --run-tests` and retry."
        )

    engine = QQmlEngine()
    context = engine.rootContext()

    payload = UISetup.build_qml_context_payload(settings_manager)

    context.setContextProperty("initialSceneSettings", payload["scene"])
    context.setContextProperty("initialGeometrySettings", payload["geometry"])
    context.setContextProperty("initialAnimationSettings", payload["animation"])
    context.setContextProperty("materialsDefaults", payload["materials"])
    context.setContextProperty("initialSharedMaterials", payload["materials"])
    context.setContextProperty("lightingAccess", payload.get("lighting", {}))
    context.setContextProperty(
        "initialDiagnosticsSettings", payload.get("diagnostics", {})
    )

    component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML_PATH.resolve())))
    assert component.isReady(), str(component.errors())

    root = component.create()
    assert root is not None, "SceneEnvironmentController failed to instantiate"

    try:
        environment_defaults = payload["scene"].get("environment", {})
        assert root.property("backgroundModeKey") == environment_defaults.get(
            "background_mode", "skybox"
        )
        assert bool(root.property("iblLightingEnabled")) == bool(
            environment_defaults.get(
                "ibl_lighting_enabled", environment_defaults.get("ibl_enabled", False)
            )
        )
        assert bool(root.property("iblMasterEnabled")) == bool(
            environment_defaults.get(
                "ibl_master_enabled",
                environment_defaults.get("ibl_enabled", False)
                or environment_defaults.get("skybox_enabled", True),
            )
        )

        expected_intensity = environment_defaults.get("ibl_intensity")
        if expected_intensity is not None:
            assert root.property("iblIntensity") == pytest.approx(
                expected_intensity, rel=1e-6
            )

        expected_brightness = environment_defaults.get(
            "skybox_brightness", environment_defaults.get("probe_brightness")
        )
        if expected_brightness is not None:
            assert root.property("skyboxBrightnessValue") == pytest.approx(
                expected_brightness, rel=1e-6
            )

        # With the default configuration the HDR probe is not preloaded.
        assert root.property("iblProbe") is None

        # Lighting payload is exposed through contextLightingDefaults.
        lighting_defaults = root.property("contextLightingDefaults")
        expected_lighting = payload["scene"].get("graphics", {}).get("lighting", {})
        assert lighting_defaults is not None
        assert expected_lighting
        assert lighting_defaults.get("key", {}).get("brightness") == pytest.approx(
            expected_lighting.get("key", {}).get("brightness"), rel=1e-6
        )

        # Materials defaults are proxied for downstream components.
        materials_defaults = root.property("contextMaterialsDefaults")
        assert materials_defaults == payload["materials"]

        quality_defaults = payload["scene"].get("graphics", {}).get("quality", {})
        if "taa_strength" in quality_defaults:
            assert root.property("taaStrength") == pytest.approx(
                quality_defaults["taa_strength"], rel=1e-6
            )
        if "taa_enabled" in quality_defaults:
            assert bool(root.property("taaEnabled")) == bool(
                quality_defaults["taa_enabled"]
            )

        effects_defaults = payload["scene"].get("graphics", {}).get("effects", {})
        if "tonemap_mode" in effects_defaults:
            assert root.property("tonemapModeName") == effects_defaults["tonemap_mode"]
        if "tonemap_enabled" in effects_defaults:
            assert bool(root.property("tonemapActive")) == bool(
                effects_defaults["tonemap_enabled"]
            )
        if "color_adjustments_enabled" in effects_defaults:
            assert bool(root.property("colorAdjustmentsEnabled")) == bool(
                effects_defaults["color_adjustments_enabled"]
            )
            assert bool(root.property("colorAdjustmentsActive")) == bool(
                effects_defaults["color_adjustments_enabled"]
            )
        if "adjustment_brightness" in effects_defaults:
            assert root.property("adjustmentBrightness") == pytest.approx(
                effects_defaults["adjustment_brightness"],
                rel=1e-6,
            )
        if "adjustment_contrast" in effects_defaults:
            assert root.property("adjustmentContrast") == pytest.approx(
                effects_defaults["adjustment_contrast"],
                rel=1e-6,
            )
        if "adjustment_saturation" in effects_defaults:
            assert root.property("adjustmentSaturation") == pytest.approx(
                effects_defaults["adjustment_saturation"],
                rel=1e-6,
            )
    finally:
        root.deleteLater()
        engine.collectGarbage()
