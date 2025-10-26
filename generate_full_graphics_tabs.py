#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор МАКСИМАЛЬНО ПОЛНЫХ табов GraphicsPanel
Основано на:
- Qt 6.10 ExtendedSceneEnvironment официальная документация
- Существующий main.qml со всеми параметрами
- Монолит panel_graphics.py

Принцип: ВСЕ параметры доступны юзеру, никаких ограничений!
"""


# ============================================================================
# ПОЛНЫЙ СПИСОК ПАРАМЕТРОВ Qt 6.10 ExtendedSceneEnvironment
# Источник: https://doc.qt.io/qt-6/qml-qtquick3d-extendedsceneenvironment.html
# ============================================================================

QT_EXTENDED_SCENE_ENVIRONMENT_PARAMS = {
    "antialiasing": [
        ("antialiasingMode", "ComboBox", ["NoAA", "SSAA", "MSAA", "ProgressiveAA"]),
        ("antialiasingQuality", "ComboBox", ["Medium", "High", "VeryHigh"]),
        ("temporalAAEnabled", "CheckBox", None),
        ("temporalAAStrength", "Slider", (0.0, 2.0, 0.01)),
        ("specularAAEnabled", "CheckBox", None),
    ],
    "tonemapping": [
        (
            "tonemapMode",
            "ComboBox",
            [
                "TonemapModeNone",
                "TonemapModeLinear",
                "TonemapModeFilmic",
                "TonemapModeReinhard",
            ],
        ),
        ("exposure", "Slider", (0.0, 10.0, 0.1)),
        ("whitePoint", "Slider", (0.1, 10.0, 0.1)),
    ],
    "effects": [
        ("glowEnabled", "CheckBox", None),
        ("glowIntensity", "Slider", (0.0, 10.0, 0.1)),
        ("glowHDRMinimumValue", "Slider", (0.0, 10.0, 0.1)),  # Bloom threshold
        ("glowBloom", "Slider", (0.0, 1.0, 0.01)),  # Bloom spread
        ("glowQualityHigh", "CheckBox", None),
        ("glowUseBicubicUpscale", "CheckBox", None),
        ("glowHDRMaximumValue", "Slider", (1.0, 20.0, 0.5)),
        ("glowHDRScale", "Slider", (0.5, 5.0, 0.1)),
        ("aoEnabled", "CheckBox", None),
        ("aoDistance", "Slider", (0.0, 100.0, 0.5)),  # SSAO radius
        ("aoStrength", "Slider", (0, 500, 5)),  # SSAO intensity * 100
        ("aoSoftness", "Slider", (0, 50, 1)),
        ("aoDither", "CheckBox", None),
        ("aoSampleRate", "Slider", (2, 4, 1)),
        ("depthOfFieldEnabled", "CheckBox", None),
        ("depthOfFieldFocusDistance", "Slider", (100.0, 50000.0, 100.0)),
        ("depthOfFieldBlurAmount", "Slider", (0.0, 20.0, 0.1)),
        ("vignetteEnabled", "CheckBox", None),
        ("vignetteStrength", "Slider", (0.0, 2.0, 0.02)),
        ("vignetteRadius", "Slider", (0.0, 2.0, 0.02)),
        ("lensFlareEnabled", "CheckBox", None),
        ("lensFlareGhostCount", "Slider", (0, 10, 1)),
        ("lensFlareGhostDispersal", "Slider", (0.0, 1.0, 0.01)),
        ("lensFlareHaloWidth", "Slider", (0.0, 1.0, 0.01)),
        ("lensFlareBloomBias", "Slider", (0.0, 1.0, 0.01)),
        ("lensFlareStretchToAspect", "Slider", (0.5, 2.0, 0.1)),
    ],
    "color_adjustments": [
        ("colorAdjustmentsEnabled", "CheckBox", None),
        ("adjustmentBrightness", "Slider", (0.0, 2.0, 0.01)),
        ("adjustmentContrast", "Slider", (0.0, 2.0, 0.01)),
        ("adjustmentSaturation", "Slider", (0.0, 2.0, 0.01)),
    ],
    "environment": [
        ("backgroundMode", "ComboBox", ["Color", "Transparent", "SkyBox"]),
        ("clearColor", "ColorButton", None),
        ("lightProbe", "TextureSelect", None),  # IBL probe
        ("skyBoxCubeMap", "TextureSelect", None),  # Skybox texture
        ("probeExposure", "Slider", (0.0, 10.0, 0.1)),  # IBL intensity
        ("probeOrientation", "Vector3D", None),  # IBL rotation (x, y, z)
        ("probeHorizon", "Slider", (-1.0, 1.0, 0.01)),
        ("probeBrightness", "Slider", (0.0, 10.0, 0.1)),
    ],
    "fog": [
        ("fog.enabled", "CheckBox", None),
        ("fog.color", "ColorButton", None),
        ("fog.density", "Slider", (0.0, 1.0, 0.001)),
        ("fog.depthEnabled", "CheckBox", None),
        ("fog.depthNear", "Slider", (0.0, 100000.0, 100.0)),
        ("fog.depthFar", "Slider", (0.0, 100000.0, 100.0)),
        ("fog.depthCurve", "Slider", (0.1, 10.0, 0.1)),
        ("fog.heightEnabled", "CheckBox", None),
        ("fog.leastIntenseY", "Slider", (-10000.0, 10000.0, 100.0)),
        ("fog.mostIntenseY", "Slider", (-10000.0, 10000.0, 100.0)),
        ("fog.heightCurve", "Slider", (0.1, 10.0, 0.1)),
        ("fog.transmitEnabled", "CheckBox", None),
        ("fog.transmitCurve", "Slider", (0.1, 10.0, 0.1)),
    ],
    "rendering": [
        ("renderScale", "Slider", (0.1, 4.0, 0.01)),
        ("maximumFrameRate", "Slider", (10.0, 240.0, 1.0)),
        ("renderPolicy", "ComboBox", ["Always", "OnDemand"]),
        ("oitMethod", "ComboBox", ["OITNone", "OITWeightedBlended"]),
        ("ditheringEnabled", "CheckBox", None),  # Qt 6.10+
    ],
}

# ============================================================================
# ПОЛНЫЙ СПИСОК ПАРАМЕТРОВ DirectionalLight / PointLight / SpotLight
# ============================================================================

LIGHT_PARAMS = {
    "directional": [
        ("brightness", "Slider", (0.0, 20.0, 0.05)),
        ("color", "ColorButton", None),
        ("eulerRotation.x", "Slider", (-180.0, 180.0, 1.0)),
        ("eulerRotation.y", "Slider", (-180.0, 180.0, 1.0)),
        ("eulerRotation.z", "Slider", (-180.0, 180.0, 1.0)),
        ("position.x", "Slider", (-10000.0, 10000.0, 10.0)),
        ("position.y", "Slider", (-10000.0, 10000.0, 10.0)),
        ("position.z", "Slider", (-10000.0, 10000.0, 10.0)),
        ("castsShadow", "CheckBox", None),
        (
            "shadowMapQuality",
            "ComboBox",
            [
                "ShadowMapQualityLow",
                "ShadowMapQualityMedium",
                "ShadowMapQualityHigh",
                "ShadowMapQualityVeryHigh",
            ],
        ),
        ("shadowFactor", "Slider", (0.0, 100.0, 1.0)),  # Darkness
        ("shadowBias", "Slider", (0.0, 100.0, 0.1)),
        (
            "shadowFilter",
            "ComboBox",
            [
                "ShadowFilterNone",
                "ShadowFilterPCF4",
                "ShadowFilterPCF8",
                "ShadowFilterPCF16",
                "ShadowFilterPCF32",
            ],
        ),
    ],
    "point": [
        ("brightness", "Slider", (0.0, 100000.0, 100.0)),
        ("color", "ColorButton", None),
        ("position.x", "Slider", (-10000.0, 10000.0, 10.0)),
        ("position.y", "Slider", (-10000.0, 10000.0, 10.0)),
        ("position.z", "Slider", (-10000.0, 10000.0, 10.0)),
        ("castsShadow", "CheckBox", None),
        ("constantFade", "Slider", (0.0, 10.0, 0.1)),
        ("linearFade", "Slider", (0.0, 10.0, 0.001)),
        ("quadraticFade", "Slider", (0.0, 10.0, 0.0001)),
    ],
}

# ============================================================================
# ПОЛНЫЙ СПИСОК ПАРАМЕТРОВ PrincipledMaterial (PBR)
# ============================================================================

MATERIAL_PARAMS = [
    ("baseColor", "ColorButton", None),
    ("metalness", "Slider", (0.0, 1.0, 0.01)),
    ("roughness", "Slider", (0.0, 1.0, 0.01)),
    ("clearcoatAmount", "Slider", (0.0, 1.0, 0.01)),
    ("clearcoatRoughnessAmount", "Slider", (0.0, 1.0, 0.01)),
    ("transmissionFactor", "Slider", (0.0, 1.0, 0.01)),
    ("opacity", "Slider", (0.0, 1.0, 0.01)),
    ("indexOfRefraction", "Slider", (1.0, 3.0, 0.01)),
    ("attenuationDistance", "Slider", (1.0, 50000.0, 100.0)),
    ("attenuationColor", "ColorButton", None),
    ("emissiveFactor", "Vector3D", None),  # R, G, B
    ("emissiveIntensity", "Slider", (0.0, 10.0, 0.1)),  # Custom param
    ("alphaMode", "ComboBox", ["Default", "Blend", "Opaque", "Mask"]),
    ("alphaCutoff", "Slider", (0.0, 1.0, 0.01)),
    ("normalStrength", "Slider", (0.0, 2.0, 0.01)),
    ("occlusionAmount", "Slider", (0.0, 2.0, 0.01)),
]

# ============================================================================
# CAMERA PARAMS (PerspectiveCamera)
# ============================================================================

CAMERA_PARAMS = [
    ("fieldOfView", "Slider", (10.0, 120.0, 0.5)),
    ("clipNear", "Slider", (0.01, 1000.0, 0.1)),
    ("clipFar", "Slider", (100.0, 1000000.0, 100.0)),
    ("position.x", "Slider", (-10000.0, 10000.0, 10.0)),
    ("position.y", "Slider", (-10000.0, 10000.0, 10.0)),
    ("position.z", "Slider", (-10000.0, 10000.0, 10.0)),
    ("eulerRotation.x", "Slider", (-180.0, 180.0, 1.0)),
    ("eulerRotation.y", "Slider", (-180.0, 180.0, 1.0)),
    ("eulerRotation.z", "Slider", (-180.0, 180.0, 1.0)),
]


def main():
    """Основная функция - генерация отчёта"""
    print("=" * 80)
    print("📋 ПОЛНЫЙ СПИСОК ПАРАМЕТРОВ Qt 6.10 GRAPHICSPANEL")
    print("=" * 80)

    # Подсчёт общего количества
    total = 0

    print("\n🎨 ExtendedSceneEnvironment:")
    for category, params in QT_EXTENDED_SCENE_ENVIRONMENT_PARAMS.items():
        print(f"\n  {category.upper()} ({len(params)} параметров):")
        for param_name, widget_type, values in params:
            print(f"    - {param_name} ({widget_type})")
            total += 1

    print(f"\n💡 DirectionalLight ({len(LIGHT_PARAMS['directional'])} параметров):")
    for param_name, widget_type, values in LIGHT_PARAMS["directional"]:
        print(f"    - {param_name} ({widget_type})")
        total += len(LIGHT_PARAMS["directional"])

    print(f"\n💡 PointLight ({len(LIGHT_PARAMS['point'])} параметров):")
    for param_name, widget_type, values in LIGHT_PARAMS["point"]:
        print(f"    - {param_name} ({widget_type})")
        total += len(LIGHT_PARAMS["point"])

    print(f"\n🎨 PrincipledMaterial ({len(MATERIAL_PARAMS)} параметров):")
    for param_name, widget_type, values in MATERIAL_PARAMS:
        print(f"    - {param_name} ({widget_type})")
        total += len(MATERIAL_PARAMS)

    print(f"\n📷 Camera ({len(CAMERA_PARAMS)} параметров):")
    for param_name, widget_type, values in CAMERA_PARAMS:
        print(f"    - {param_name} ({widget_type})")
        total += len(CAMERA_PARAMS)

    print("\n" + "=" * 80)
    print(f"📊 ИТОГО: {total} параметров доступны в Qt 6.10")
    print("=" * 80)

    print("\n💡 РЕКОМЕНДАЦИИ:")
    print("  1. Создать табы на основе этого списка")
    print("  2. Добавить ВСЕ параметры без ограничений")
    print("  3. Юзер сам контролирует всё")
    print("  4. Никаких связей между параметрами")

    print("\n✅ Следующий шаг: Генерация кода табов")


if __name__ == "__main__":
    main()
