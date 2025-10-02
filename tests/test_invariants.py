"""
Tests for domain invariants
"""

import unittest
import math
from src.pneumo.geometry import FrameGeom, LeverGeom, CylinderGeom
from src.pneumo.cylinder import CylinderSpec, CylinderState
from src.app.config_defaults import create_default_system_configuration
from src.common.units import MIN_VOLUME_FRACTION
from src.common.errors import GeometryError, InvariantViolation


class TestGeometryInvariants(unittest.TestCase):
    """Test geometric invariants"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.config = create_default_system_configuration()
        self.cylinder_geom = self.config['cylinder_geom']
        self.lever_geom = self.config['lever_geom']
    
    def test_frame_geometry_invariants(self):
        """Test frame geometry invariants"""
        frame = self.config['frame_geom']
        
        # Valid frame should pass
        result = frame.validate_invariants()
        self.assertTrue(result['is_valid'])
        
        # Invalid wheelbase should fail
        with self.assertRaises(GeometryError):
            FrameGeom(L_wb=-1.0)
    
    def test_lever_geometry_invariants(self):
        """Test lever geometry invariants"""
        lever = self.lever_geom
        
        # Valid lever should pass
        result = lever.validate_invariants()
        self.assertTrue(result['is_valid'])
        
        # Invalid rod joint fraction should fail
        with self.assertRaises(GeometryError):
            LeverGeom(
                L_lever=1.0,
                rod_joint_frac=1.5,  # > 0.9
                d_frame_to_lever_hinge=0.5
            )
        
        with self.assertRaises(GeometryError):
            LeverGeom(
                L_lever=1.0,
                rod_joint_frac=0.05,  # < 0.1  
                d_frame_to_lever_hinge=0.5
            )
    
    def test_cylinder_travel_invariant(self):
        """Test L_travel_max > 0 invariant"""
        geom = self.cylinder_geom
        
        # Valid geometry should have positive travel
        self.assertGreater(geom.L_travel_max, 0)
        
        # Geometry with excessive dead zones should fail
        with self.assertRaises(GeometryError):
            CylinderGeom(
                D_in_front=0.08, D_in_rear=0.08,
                D_out_front=0.12, D_out_rear=0.12,
                L_inner=0.1,  # Short internal length
                t_piston=0.02,
                D_rod=0.03,
                link_rod_diameters_front_rear=True,
                L_dead_head=0.05,  # Large dead zones
                L_dead_rod=0.05,   # Large dead zones
                residual_frac_min=MIN_VOLUME_FRACTION
            )
    
    def test_minimum_volume_invariants(self):
        """Test minimum volume invariants at travel extremes"""
        geom = self.cylinder_geom
        
        # Test at both extremes for both front and rear
        half_travel = geom.L_travel_max / 2.0
        
        for is_front in [True, False]:
            # At maximum extension (x = +half_travel)
            vol_head_max = geom.area_head(is_front) * (geom.L_inner/2.0 - half_travel - geom.L_dead_head)
            vol_rod_max = geom.area_rod(is_front) * (geom.L_inner/2.0 + half_travel - geom.L_dead_rod)
            
            # At maximum compression (x = -half_travel)
            vol_head_min = geom.area_head(is_front) * (geom.L_inner/2.0 + half_travel - geom.L_dead_head)
            vol_rod_min = geom.area_rod(is_front) * (geom.L_inner/2.0 - half_travel - geom.L_dead_rod)
            
            min_vol_head = geom.min_volume_head(is_front)
            min_vol_rod = geom.min_volume_rod(is_front)
            
            # All volumes should be above minimum
            self.assertGreaterEqual(vol_head_max, min_vol_head)
            self.assertGreaterEqual(vol_head_min, min_vol_head)
            self.assertGreaterEqual(vol_rod_max, min_vol_rod)
            self.assertGreaterEqual(vol_rod_min, min_vol_rod)
    
    def test_rod_diameter_linking(self):
        """Test rod diameter linking functionality"""
        geom = self.cylinder_geom
        
        # When linking is enabled, should use same rod diameter for both
        self.assertTrue(geom.link_rod_diameters_front_rear)
        
        # Rod areas should account for rod presence
        area_head_front = geom.area_head(True)
        area_head_rear = geom.area_head(False)
        area_rod_front = geom.area_rod(True)  
        area_rod_rear = geom.area_rod(False)
        
        # Head areas should be full cylinder area
        self.assertAlmostEqual(area_head_front, math.pi * (geom.D_in_front/2)**2)
        self.assertAlmostEqual(area_head_rear, math.pi * (geom.D_in_rear/2)**2)
        
        # Rod areas should be reduced by rod cross-section
        rod_area = math.pi * (geom.D_rod/2)**2
        self.assertAlmostEqual(area_rod_front, area_head_front - rod_area)
        self.assertAlmostEqual(area_rod_rear, area_head_rear - rod_area)


class TestCylinderStateInvariants(unittest.TestCase):
    """Test cylinder state invariants"""
    
    def setUp(self):
        """Setup test fixtures"""
        config = create_default_system_configuration()
        from src.pneumo.enums import Wheel
        self.cylinder_spec = config['cylinder_specs'][Wheel.LP]
        self.cylinder_state = CylinderState(spec=self.cylinder_spec)
    
    def test_position_limits(self):
        """Test position stays within travel limits"""
        geom = self.cylinder_spec.geometry
        max_travel = geom.L_travel_max
        
        # Position at center should be valid
        self.cylinder_state.x = 0.0
        result = self.cylinder_state.validate_invariants()
        self.assertTrue(result['is_valid'])
        
        # Position at extremes should be valid
        self.cylinder_state.x = max_travel / 2.0 * 0.99  # Just within limit
        result = self.cylinder_state.validate_invariants()
        self.assertTrue(result['is_valid'])
        
        self.cylinder_state.x = -max_travel / 2.0 * 0.99  # Just within limit
        result = self.cylinder_state.validate_invariants()
        self.assertTrue(result['is_valid'])
        
        # Position beyond limits should be invalid
        self.cylinder_state.x = max_travel / 2.0 * 1.01  # Beyond limit
        result = self.cylinder_state.validate_invariants()
        self.assertFalse(result['is_valid'])
    
    def test_volume_calculation_consistency(self):
        """Test volume calculations are consistent and positive"""
        # Test at various positions
        positions = [-0.05, -0.02, 0.0, 0.02, 0.05]
        
        for x in positions:
            if abs(x) <= self.cylinder_spec.geometry.L_travel_max / 2.0:
                self.cylinder_state.x = x
                
                vol_head = self.cylinder_state.vol_head()
                vol_rod = self.cylinder_state.vol_rod()
                
                # Volumes should be positive
                self.assertGreater(vol_head, 0)
                self.assertGreater(vol_rod, 0)
                
                # Volumes should respect minimum requirements
                min_head = self.cylinder_spec.geometry.min_volume_head(self.cylinder_spec.is_front)
                min_rod = self.cylinder_spec.geometry.min_volume_rod(self.cylinder_spec.is_front)
                
                self.assertGreaterEqual(vol_head, min_head * 0.999)  # Small tolerance
                self.assertGreaterEqual(vol_rod, min_rod * 0.999)
    
    def test_lever_angle_update(self):
        """Test lever angle to piston position conversion"""
        # Start at center position
        self.cylinder_state.x = 0.0
        initial_x = self.cylinder_state.x
        
        # Small angle change should produce small position change
        small_angle = 0.1  # ~6 degrees
        self.cylinder_state.update_from_lever_angle(small_angle)
        
        # Position should have changed
        self.assertNotEqual(self.cylinder_state.x, initial_x)
        
        # Position should still be within travel limits
        max_travel = self.cylinder_spec.geometry.L_travel_max
        self.assertLessEqual(abs(self.cylinder_state.x), max_travel / 2.0)


if __name__ == '__main__':
    unittest.main()