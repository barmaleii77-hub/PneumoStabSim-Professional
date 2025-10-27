import importlib.util
import math
from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtGui",
    reason="PySide6 requires system OpenGL libraries",
    exc_type=ImportError,
)
pytest.importorskip(
    "PySide6.QtQuick3D",
    reason="PySide6 requires system OpenGL libraries",
    exc_type=ImportError,
)

_GEOMETRY_BRIDGE_PATH = (
    Path(__file__).resolve().parent.parent / "src" / "ui" / "geometry_bridge.py"
)
_SPEC = importlib.util.spec_from_file_location("geometry_bridge", _GEOMETRY_BRIDGE_PATH)
assert _SPEC and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

create_geometry_converter = _MODULE.create_geometry_converter


class _DummySettingsManager:
    def __init__(self, payload):
        self._payload = payload

    def get_category(self, category: str):
        assert category == "geometry"
        return self._payload


@pytest.mark.gui
def test_create_geometry_converter_normalizes_mm_lengths(qapp):
    geometry_settings = {
        "initial_state": {
            "frame_length_mm": 2000.0,
            "frame_height_mm": 650.0,
            "frame_beam_size_mm": 120.0,
            "lever_length_mm": 315.0,
            "cylinder_body_length_mm": 250.0,
            "tail_rod_length_mm": 100.0,
        }
    }

    converter = create_geometry_converter(_DummySettingsManager(geometry_settings))

    assert math.isclose(converter.frameLength, 2.0)
    assert math.isclose(converter.frameHeight, 0.65)
    assert math.isclose(converter.frameBeamSize, 0.12)
    assert math.isclose(converter.leverLength, 0.315)
    assert math.isclose(converter.cylinderBodyLength, 0.25)
    assert math.isclose(converter.tailRodLength, 0.1)


def test_create_geometry_converter_accepts_metric_overrides(qapp):
    converter = create_geometry_converter(
        wheelbase=2.5,
        lever_length=0.4,
        cylinder_diameter=0.08,
    )

    assert math.isclose(converter.leverLength, 0.4)
    frame = converter.get_frame_params()
    assert frame["frameLength"] > 0.0
