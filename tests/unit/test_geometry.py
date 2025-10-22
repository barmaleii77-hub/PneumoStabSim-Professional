"""
Unit tests for geometry calculations
"""
import pytest
import numpy as np
from src.core.geometry import Point2, GeometryParams
from src.mechanics.kinematics import CylinderKinematics, LeverState


@pytest.mark.unit
class TestGeometryParams:
    """Test GeometryParams class"""

    def test_create_default(self):
        """Test creating default geometry"""
        geom = GeometryParams()
        assert geom.wheelbase > 0
        assert geom.lever_length > 0

    def test_enforce_track(self, sample_geometry_params):
        """Test track width enforcement"""
        geom = sample_geometry_params
        geom.enforce_track_from_geometry()
        assert geom.track_width > 0


@pytest.mark.unit
class TestCylinderKinematics:
    """Test CylinderKinematics class"""

    def test_create_kinematics(self, sample_cylinder_params):
        """Test creating CylinderKinematics"""
        kinematics = CylinderKinematics(
            frame_hinge=Point2(x=-0.1, y=0.5), **sample_cylinder_params
        )
        assert kinematics.D_in == 0.08
        assert kinematics.D_rod == 0.035

    def test_solve_from_lever(self, sample_cylinder_params):
        """Test solving cylinder state from lever"""
        kinematics = CylinderKinematics(
            frame_hinge=Point2(x=-0.1, y=0.5), **sample_cylinder_params
        )

        lever_state = LeverState(
            pivot=Point2(0.0, 0.0),
            attach=Point2(0.3, 0.1),
            free_end=Point2(0.4, 0.15),
            angle=np.deg2rad(5.0),
            arm_length=0.4,
            rod_attach_fraction=0.7,
        )

        cylinder_state = kinematics.solve_from_lever_state(lever_state)

        assert abs(cylinder_state.stroke) < 0.5  # Reasonable range
        assert cylinder_state.volume_head > 0
        assert cylinder_state.volume_rod > 0


@pytest.mark.unit
class TestGeometryBridge:
    """Test GeometryBridge functionality"""

    def test_create_converter(self, geometry_bridge):
        """Test creating geometry converter"""
        assert geometry_bridge is not None

    def test_get_corner_coords(self, geometry_bridge):
        """Test getting corner 3D coordinates"""
        coords = geometry_bridge.get_corner_3d_coords("fl", lever_angle_deg=0.0)

        assert "j_arm" in coords
        assert "j_tail" in coords
        assert "j_rod" in coords
        assert "pistonPositionMm" in coords
        assert isinstance(coords["pistonPositionMm"], float)

    def test_all_corners(self, geometry_bridge):
        """Test getting all 4 corners"""
        lever_angles = {"fl": 5.0, "fr": -3.0, "rl": 2.0, "rr": -1.0}

        all_coords = geometry_bridge.get_all_corners_3d(lever_angles)

        assert len(all_coords) == 4
        for corner in ["fl", "fr", "rl", "rr"]:
            assert corner in all_coords
            assert "pistonPositionMm" in all_coords[corner]

    def test_integration_with_settings_manager(self, geometry_bridge, settings_manager):
        """Test GeometryBridge integration with SettingsManager"""
        # Example test that checks if settings_manager can be used to update geometry_bridge settings
        initial_wheelbase = geometry_bridge.wheelbase
        new_wheelbase = initial_wheelbase + 0.1

        settings_manager.set_wheelbase(new_wheelbase)
        geometry_bridge.update_from_settings_manager()

        assert geometry_bridge.wheelbase == new_wheelbase

        # Validate other properties as needed
        # ...
