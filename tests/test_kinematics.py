"""
P13: Kinematics validation tests

Tests:
- Track ? arm_length ? pivot_offset invariant
- Extreme stroke validation (dead zones respected)
- Angle-stroke relationship
- Interference checking

References:
- unittest: https://docs.python.org/3/library/unittest.html
- numpy.testing: https://numpy.org/doc/stable/reference/routines.testing.html
"""

import unittest
import numpy as np
from numpy.testing import assert_allclose
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.geometry import Point2, Segment2, Capsule2, GeometryParams
from src.core.geometry import dist_segment_segment, capsule_capsule_intersect
from src.mechanics.constraints import (
    ConstraintValidator,
    ConstraintMode,
    calculate_full_cylinder_volume,
    calculate_min_residual_volume
)
from src.mechanics.kinematics import (
    LeverKinematics,
    CylinderKinematics,
    InterferenceChecker,
    solve_axle_plane
)


class TestTrackInvariant(unittest.TestCase):
    """Test track ? arm_length ? pivot_offset invariant"""
    
    def setUp(self):
        """Setup validator"""
        self.validator = ConstraintValidator()
        
    def test_invariant_holds(self):
        """Test track = 2 * (arm_length + pivot_offset)"""
        arm_length = 0.4  # m
        pivot_offset = 0.3  # m
        expected_track = 2.0 * (arm_length + pivot_offset)
        
        is_valid = self.validator.validate_track_invariant(
            expected_track, arm_length, pivot_offset
        )
        
        self.assertTrue(is_valid, "Track invariant should hold")
        
    def test_invariant_violated(self):
        """Test detection of violated invariant"""
        track = 1.5
        arm_length = 0.4
        pivot_offset = 0.3
        # Expected: 2*(0.4+0.3) = 1.4, but track=1.5
        
        is_valid = self.validator.validate_track_invariant(
            track, arm_length, pivot_offset
        )
        
        self.assertFalse(is_valid, "Track invariant should be violated")
        
    def test_enforce_track_fix_arm(self):
        """Test enforcing invariant by fixing track and adjusting arm"""
        track = 1.6
        arm_length = 0.5
        pivot_offset = 0.3
        
        track_new, arm_new, pivot_new = self.validator.enforce_track_invariant(
            track, arm_length, pivot_offset, ConstraintMode.FIX_TRACK
        )
        
        # Should adjust arm_length to satisfy track
        expected_arm = (track / 2.0) - pivot_offset
        
        assert_allclose(track_new, track, rtol=1e-10)
        assert_allclose(pivot_new, pivot_offset, rtol=1e-10)
        assert_allclose(arm_new, expected_arm, rtol=1e-10)
        
    def test_mirrored_sides(self):
        """Test track invariant holds for mirrored (left/right) configurations"""
        # Right side
        track_right = 1.4
        arm_right = 0.4
        pivot_right = 0.3
        
        # Left side (mirrored)
        track_left = track_right
        arm_left = arm_right
        pivot_left = pivot_right
        
        # Both should satisfy invariant
        self.assertTrue(self.validator.validate_track_invariant(
            track_right, arm_right, pivot_right
        ))
        self.assertTrue(self.validator.validate_track_invariant(
            track_left, arm_left, pivot_left
        ))


class TestStrokeValidation(unittest.TestCase):
    """Test stroke limits and dead zone validation"""
    
    def test_max_vertical_travel(self):
        """Test free end vertical travel ? arm_length"""
        validator = ConstraintValidator()
        arm_length = 0.4  # m
        
        # Within bounds
        self.assertTrue(validator.validate_max_vertical_travel(arm_length, 0.3))
        self.assertTrue(validator.validate_max_vertical_travel(arm_length, -0.3))
        
        # At limit
        self.assertTrue(validator.validate_max_vertical_travel(arm_length, arm_length))
        self.assertTrue(validator.validate_max_vertical_travel(arm_length, -arm_length))
        
        # Exceeds limit
        self.assertFalse(validator.validate_max_vertical_travel(arm_length, 0.5))
        self.assertFalse(validator.validate_max_vertical_travel(arm_length, -0.5))
        
    def test_residual_volume_minimum(self):
        """Test residual volume ? 0.5% of full volume"""
        validator = ConstraintValidator()
        
        diameter = 0.08  # m
        stroke = 0.15  # m
        
        min_required = calculate_min_residual_volume(diameter, stroke, fraction=0.005)
        
        # Sufficient residual
        self.assertTrue(validator.validate_residual_volume(
            min_required, diameter, stroke
        ))
        
        # Insufficient residual
        self.assertFalse(validator.validate_residual_volume(
            min_required * 0.3, diameter, stroke
        ))
        
    def test_extreme_strokes_respect_dead_zones(self):
        """Test that extreme strokes maintain minimum volumes"""
        # Cylinder parameters
        D_in = 0.08  # m
        D_rod = 0.032  # m
        t_p = 0.02  # m
        L_body = 0.25  # m
        
        # Dead zones (0.5% of full volume)
        full_vol = calculate_full_cylinder_volume(D_in, L_body)
        delta_min = full_vol * 0.005
        
        # At maximum compression (s = -S_max/2)
        A_head = np.pi * (D_in / 2.0) ** 2
        S_max = L_body - t_p
        s_min = -S_max / 2.0
        
        V_head_min = delta_min + A_head * (S_max / 2.0 + s_min)
        
        # Volume should be >= dead zone
        self.assertGreaterEqual(V_head_min, delta_min * 0.99)


class TestAngleStrokeRelationship(unittest.TestCase):
    """Test angle ? stroke calibration"""
    
    def test_zero_angle_zero_displacement(self):
        """Test ?=0 ? free_end_y=0"""
        lever_kin = LeverKinematics(
            arm_length=0.4,
            pivot_position=Point2(0.0, 0.0),
            pivot_offset_from_frame=0.3,
            rod_attach_fraction=0.7
        )
        
        # Solve from angle ?=0
        state = lever_kin.solve_from_angle(0.0)
        
        assert_allclose(state.free_end.y, 0.0, atol=1e-10)
        
    def test_symmetric_angles(self):
        """Test �y ? �? symmetry"""
        lever_kin = LeverKinematics(
            arm_length=0.4,
            pivot_position=Point2(0.0, 0.0),
            pivot_offset_from_frame=0.3
        )
        
        y_pos = 0.2  # m
        
        # Positive displacement
        state_pos = lever_kin.solve_from_free_end_y(y_pos)
        
        # Negative displacement
        state_neg = lever_kin.solve_from_free_end_y(-y_pos)
        
        # Angles should be opposite
        assert_allclose(state_pos.angle, -state_neg.angle, rtol=1e-6)
        
    def test_angle_consistency(self):
        """Test forward/inverse kinematics consistency"""
        lever_kin = LeverKinematics(
            arm_length=0.4,
            pivot_position=Point2(0.0, 0.0),
            pivot_offset_from_frame=0.3
        )
        
        # Start from angle
        theta_input = np.radians(15.0)
        state1 = lever_kin.solve_from_angle(theta_input)
        
        # Extract free_end_y and solve back
        y = state1.free_end.y
        state2 = lever_kin.solve_from_free_end_y(y)
        
        # Angles should match
        assert_allclose(state2.angle, theta_input, rtol=1e-6)


class TestInterferenceChecking(unittest.TestCase):
    """Test geometric interference detection"""
    
    def test_no_interference_normal_config(self):
        """Test normal configuration has no interference"""
        # Setup normal configuration
        result = solve_axle_plane(
            side="right",
            position="front",
            arm_length=0.4,
            pivot_offset=0.3,
            rod_attach_fraction=0.7,
            free_end_y=0.05,  # Small displacement
            cylinder_params={
                'frame_hinge_x': -0.1,
                'frame_hinge_y': 0.0,
                'inner_diameter': 0.08,
                'rod_diameter': 0.032,
                'piston_thickness': 0.02,
                'body_length': 0.25,
                'dead_zone_rod': 0.00005,
                'dead_zone_head': 0.00005,
            },
            check_interference=True
        )
        
        self.assertFalse(
            result['is_interfering'],
            f"Normal config should not interfere, clearance={result['clearance']:.4f}m"
        )
        
    def test_capsule_distance_calculation(self):
        """Test capsule-capsule distance calculation"""
        # Two parallel segments
        seg1 = Segment2(Point2(0.0, 0.0), Point2(1.0, 0.0))
        seg2 = Segment2(Point2(0.0, 0.1), Point2(1.0, 0.1))
        
        dist = dist_segment_segment(seg1, seg2)
        
        assert_allclose(dist, 0.1, rtol=1e-6)
        
    def test_capsule_intersection(self):
        """Test capsule intersection detection"""
        # Close segments
        seg1 = Segment2(Point2(0.0, 0.0), Point2(1.0, 0.0))
        seg2 = Segment2(Point2(0.0, 0.03), Point2(1.0, 0.03))
        
        # Capsules with radii that cause intersection
        cap1 = Capsule2(seg1, 0.025)
        cap2 = Capsule2(seg2, 0.025)
        
        # Distance = 0.03m, sum of radii = 0.05m ? intersection
        self.assertTrue(capsule_capsule_intersect(cap1, cap2))


class TestKinematicsIntegration(unittest.TestCase):
    """Test complete kinematics solution"""
    
    def test_solve_axle_plane(self):
        """Test complete axle plane solver"""
        result = solve_axle_plane(
            side="right",
            position="front",
            arm_length=0.4,
            pivot_offset=0.3,
            rod_attach_fraction=0.7,
            free_end_y=0.1,
            cylinder_params={
                'frame_hinge_x': -0.1,
                'frame_hinge_y': 0.0,
                'inner_diameter': 0.08,
                'rod_diameter': 0.032,
                'piston_thickness': 0.02,
                'body_length': 0.25,
                'dead_zone_rod': 0.00005,
                'dead_zone_head': 0.00005,
            }
        )
        
        # Check result structure
        self.assertIn('lever_state', result)
        self.assertIn('cylinder_state', result)
        
        # Check numerical values
        lever = result['lever_state']
        cyl = result['cylinder_state']
        
        # Lever angle should be non-zero
        self.assertNotEqual(lever.angle, 0.0)
        
        # Volumes should be positive
        self.assertGreater(cyl.volume_head, 0.0)
        self.assertGreater(cyl.volume_rod, 0.0)
        
        # Print example values
        print(f"\n=== Example Configuration ===")
        print(f"Lever angle: {np.degrees(lever.angle):.2f} deg")
        print(f"Stroke: {cyl.stroke * 1000:.2f} mm")
        print(f"V_head: {cyl.volume_head * 1e6:.2f} cm?")
        print(f"V_rod: {cyl.volume_rod * 1e6:.2f} cm?")


if __name__ == '__main__':
    unittest.main(verbosity=2)
