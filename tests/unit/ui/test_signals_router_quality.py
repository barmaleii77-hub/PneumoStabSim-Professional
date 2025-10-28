import math

from src.ui.main_window_pkg.signals_router import SignalsRouter


def test_normalize_quality_payload_converts_numeric_types() -> None:
    payload = {
        "preset": "ultra",
        "shadows": {
            "enabled": "true",
            "resolution": "4096",
            "filter": "32",
            "bias": "8.0",
            "darkness": "80",
        },
        "antialiasing": {
            "primary": "ssaa",
            "quality": "high",
            "post": "taa",
        },
        "taa_enabled": 1,
        "taa_strength": "0.4",
        "taa_motion_adaptive": "false",
        "fxaa_enabled": 0,
        "specular_aa": "yes",
        "dithering": "on",
        "oit": "weighted",
        "render_scale": "1.05",
        "render_policy": "always",
        "frame_rate_limit": "144",
        "mesh": {
            "cylinder_segments": "128",
            "cylinder_rings": "32",
        },
    }

    normalized = SignalsRouter._normalize_quality_payload(payload)

    shadow_settings = normalized["shadowSettings"]
    assert shadow_settings["enabled"] is True
    assert shadow_settings["resolution"] == 4096
    assert isinstance(shadow_settings["resolution"], int)
    assert shadow_settings["filterSamples"] == 32
    assert isinstance(shadow_settings["filterSamples"], int)
    assert math.isclose(shadow_settings["bias"], 8.0)
    assert math.isclose(shadow_settings["factor"], 80.0)

    assert normalized["aaPrimaryMode"] == "ssaa"
    assert normalized["aaQualityLevel"] == "high"
    assert normalized["aaPostMode"] == "taa"
    assert normalized["taaEnabled"] is True
    assert math.isclose(normalized["taaStrength"], 0.4)
    assert normalized["taaMotionAdaptive"] is False
    assert normalized["fxaaEnabled"] is False
    assert normalized["specularAAEnabled"] is True
    assert normalized["ditheringEnabled"] is True
    assert normalized["oitMode"] == "weighted"
    assert math.isclose(normalized["renderScale"], 1.05)
    assert normalized["renderPolicy"] == "always"
    assert math.isclose(normalized["frameRateLimit"], 144.0)

    mesh_quality = normalized["meshQuality"]
    assert mesh_quality["cylinderSegments"] == 128
    assert mesh_quality["cylinderRings"] == 32


def test_normalize_quality_payload_accepts_flat_keys() -> None:
    payload = {
        "aaPrimaryMode": "msaa",
        "aaQualityLevel": "medium",
        "aaPostMode": "fxaa",
        "taaEnabled": False,
        "taaStrength": 0.2,
        "taaMotionAdaptive": True,
        "fxaaEnabled": True,
        "specularAAEnabled": False,
        "ditheringEnabled": False,
        "oitMode": "none",
        "shadowSettings": {
            "enabled": False,
            "resolution": 1024,
        },
    }

    normalized = SignalsRouter._normalize_quality_payload(payload)

    assert normalized["aaPrimaryMode"] == "msaa"
    assert normalized["aaQualityLevel"] == "medium"
    assert normalized["aaPostMode"] == "fxaa"
    assert normalized["taaEnabled"] is False
    assert math.isclose(normalized["taaStrength"], 0.2)
    assert normalized["taaMotionAdaptive"] is True
    assert normalized["fxaaEnabled"] is True
    assert normalized["specularAAEnabled"] is False
    assert normalized["ditheringEnabled"] is False
    assert normalized["oitMode"] == "none"
    assert normalized["shadowSettings"]["enabled"] is False
    assert normalized["shadowSettings"]["resolution"] == 1024
