from __future__ import annotations

from decimal import Decimal

import pytest

from src.ui.geometry_schema import GeometryValidationError, validate_geometry_settings


VALID_PAYLOAD = {
    "wheelbase": 2.0,
    "track": 0.391,
    "frame_to_pivot": 0.351,
    "lever_length": 0.609,
    "rod_position": 0.754,
    "cylinder_length": 0.491,
    "cyl_diam_m": 0.251,
    "stroke_m": 0.3,
    "dead_gap_m": 0.005,
    "rod_diameter_m": 0.118,
    "rod_diameter_rear_m": 0.117,
    "piston_rod_length_m": 0.5,
    "piston_thickness_m": 0.1,
    "frame_height_m": 0.65,
    "frame_beam_size_m": 0.12,
    "tail_rod_length_m": 0.1,
    "interference_check": True,
    "link_rod_diameters": False,
}


def test_validate_geometry_settings():
    # Should not raise any exceptions
    validated = validate_geometry_settings(dict(VALID_PAYLOAD))
    assert validated.to_config_dict() == VALID_PAYLOAD

    invalid_payload = dict(VALID_PAYLOAD)
    invalid_payload["wheelbase"] = -1.0

    with pytest.raises(GeometryValidationError):
        validate_geometry_settings(invalid_payload)


def test_validate_geometry_settings_accepts_decimal_scalars():
    payload = {
        key: (Decimal(str(value)) if isinstance(value, float) else value)
        for key, value in VALID_PAYLOAD.items()
    }

    validated = validate_geometry_settings(payload)
    assert validated.to_config_dict() == VALID_PAYLOAD


def test_validate_geometry_settings_accepts_numpy_scalars():
    numpy = pytest.importorskip("numpy")

    payload = dict(VALID_PAYLOAD)
    payload["wheelbase"] = numpy.float64(payload["wheelbase"])
    payload["track"] = numpy.float32(payload["track"])

    validated = validate_geometry_settings(payload)
    assert validated.to_config_dict()["wheelbase"] == pytest.approx(
        VALID_PAYLOAD["wheelbase"]
    )
