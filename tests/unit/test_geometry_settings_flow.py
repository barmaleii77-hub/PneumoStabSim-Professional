import json
from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtGui",
    reason="PySide6 QtGui module is required for geometry bridge tests",
    exc_type=ImportError,
)

from config import constants as constants_module
from src.core.settings_service import SETTINGS_SERVICE_TOKEN, SettingsService
from src.infrastructure.container import get_default_container
from src.core.geometry import GeometryParams
from src.ui.geometry_bridge import create_geometry_converter


def _write_settings(payload: dict, path: Path) -> None:
    payload["defaults_snapshot"] = json.loads(json.dumps(payload["current"]))
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


@pytest.fixture()
def geometry_settings(tmp_path: Path) -> Path:
    payload = {
        "metadata": {
            "version": "1.0.0",
            "last_modified": "2025-01-01T00:00:00",
            "units_version": "si_v2",
        },
        "current": {
            "geometry": {"wheelbase": 2.0},
            "constants": {
                "geometry": {
                    "kinematics": {
                        "track_width_m": 1.6,
                        "lever_length_m": 0.45,
                        "pivot_offset_from_frame_m": 0.35,
                        "rod_attach_fraction": 0.55,
                    },
                    "cylinder": {
                        "inner_diameter_m": 0.1,
                        "rod_diameter_m": 0.04,
                        "piston_thickness_m": 0.025,
                        "body_length_m": 0.32,
                        "dead_zone_rod_m3": 0.001,
                        "dead_zone_head_m3": 0.001,
                    },
                    "visualization": {
                        "arm_radius_m": 0.06,
                        "cylinder_radius_m": 0.05,
                    },
                    "initial_state": {
                        "frame_length_m": 2.0,
                        "lever_length_m": 0.45,
                        "tail_rod_length_m": 0.2,
                        "frame_beam_size_m": 0.14,
                        "frame_height_m": 0.7,
                        "cylinder_body_length_m": 0.32,
                    },
                }
            },
        },
    }

    target = tmp_path / "app_settings.json"
    _write_settings(payload, target)
    return target


def test_geometry_params_reflect_settings(geometry_settings: Path) -> None:
    service = SettingsService(settings_path=geometry_settings, validate_schema=False)
    container = get_default_container()
    with container.override(SETTINGS_SERVICE_TOKEN, service):
        constants_module.refresh_cache()

        params = GeometryParams()

        assert params.track_width == pytest.approx(1.6)
        assert params.lever_length == pytest.approx(0.45)
        assert params.cylinder_inner_diameter == pytest.approx(0.1)

    constants_module.refresh_cache()


def test_geometry_converter_uses_persisted_values(geometry_settings: Path) -> None:
    service = SettingsService(settings_path=geometry_settings, validate_schema=False)
    container = get_default_container()
    with container.override(SETTINGS_SERVICE_TOKEN, service):
        constants_module.refresh_cache()

        class DummyManager:
            def get_category(self, name: str):
                if name == "geometry":
                    return {}
                raise KeyError(name)

            def set(self, *_args, **_kwargs):
                pass

            def save(self):
                pass

        converter = create_geometry_converter(settings_manager=DummyManager())
        exported = converter.export_geometry_params()

        assert exported["frameLength"] == pytest.approx(2.0)
        assert converter.geometry.cylinder_inner_diameter == pytest.approx(0.1)

    constants_module.refresh_cache()
