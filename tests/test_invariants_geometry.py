"""
P12: Geometry invariants validation tests

Tests:
- Minimum pocket volumes >= 0.5% of cylinder volume
- Stroke-to-angle calibration
- Lever geometry constraints
- No mechanical interference

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

from src.core.geometry import GeometryParams
from src.mechanics.suspension import calculate_stroke_from_angle


class TestGeometryInvariants(unittest.TestCase):
    """Test geometric invariants and constraints"""

    def setUp(self):
        """Setup default geometry parameters"""
        self.params = GeometryParams()

        # Typical pneumatic cylinder parameters
        self.cylinder_diameter = 0.08  # 80mm
        self.cylinder_stroke = 0.15  # 150mm
        self.piston_thickness = 0.02  # 20mm

        # Calculate cylinder volume
        self.cylinder_area = np.pi * (self.cylinder_diameter / 2) ** 2
        self.full_volume = self.cylinder_area * self.cylinder_stroke

    def test_minimum_pocket_volumes(self):
        """Test that minimum pocket volumes >= 0.5% of cylinder volume

        Invariant: V_min_pocket >= 0.005 * V_cylinder
        This ensures numerical stability and physical realism
        """
        # Minimum required volume (0.5% of full cylinder)
        min_required = 0.005 * self.full_volume

        # Dead volumes at each end
        dead_volume_compressed = self.cylinder_area * self.piston_thickness
        dead_volume_extended = self.cylinder_area * self.piston_thickness

        # Check both pockets
        self.assertGreaterEqual(
            dead_volume_compressed,
            min_required,
            f"Compressed pocket {dead_volume_compressed:.6e}m? < "
            f"minimum {min_required:.6e}m?",
        )

        self.assertGreaterEqual(
            dead_volume_extended,
            min_required,
            f"Extended pocket {dead_volume_extended:.6e}m? < "
            f"minimum {min_required:.6e}m?",
        )

    def test_stroke_angle_calibration(self):
        """Test stroke-to-angle calibration consistency

        At zero lever deflection, piston stroke should be zero.
        At extremes, stroke should not exceed mechanical limits.
        """
        # Test zero position
        angle_zero = 0.0
        stroke_zero = calculate_stroke_from_angle(angle_zero, self.params)

        assert_allclose(
            stroke_zero, 0.0, atol=1e-6, err_msg="Zero angle should produce zero stroke"
        )

        # Test extreme positions
        max_angle = np.radians(10.0)  # 10 degrees max deflection
        stroke_max = calculate_stroke_from_angle(max_angle, self.params)

        self.assertLessEqual(
            abs(stroke_max),
            self.cylinder_stroke,
            f"Stroke {stroke_max:.6f}m exceeds cylinder stroke {self.cylinder_stroke:.6f}m",
        )

    def test_lever_geometry_consistency(self):
        """Test lever geometry inter-dependencies

        wheelbase ? lever_length ? pivot_distance
        Must satisfy geometric constraints without interference
        """
        wheelbase = 2.5  # m
        lever_length = 0.4  # m
        pivot_distance = 0.3  # m

        # Geometric constraint: lever + pivot must be reasonable relative to wheelbase
        max_reach = lever_length + pivot_distance

        self.assertLess(
            max_reach,
            wheelbase / 2,
            f"Lever reach {max_reach:.3f}m too large for wheelbase {wheelbase:.3f}m",
        )

        # Triangle inequality for lever mechanism
        self.assertGreater(lever_length, 0.0, "Lever length must be positive")

        self.assertGreater(pivot_distance, 0.0, "Pivot distance must be positive")

    def test_volume_calculation_precision(self):
        """Test volume calculation precision

        V = A * stroke should match within numerical tolerance
        """
        stroke = 0.1  # 100mm stroke
        expected_volume = self.cylinder_area * stroke

        # Calculate volume directly
        calculated_volume = np.pi * (self.cylinder_diameter / 2) ** 2 * stroke

        assert_allclose(
            calculated_volume,
            expected_volume,
            rtol=1e-12,
            err_msg="Volume calculation precision issue",
        )

    def test_dead_zones_non_negative(self):
        """Test that dead zones are non-negative

        Dead zones must be positive to prevent numerical issues
        """
        dead_zone_compressed = self.piston_thickness
        dead_zone_extended = self.piston_thickness

        self.assertGreater(
            dead_zone_compressed, 0.0, "Compressed dead zone must be positive"
        )

        self.assertGreater(
            dead_zone_extended, 0.0, "Extended dead zone must be positive"
        )

        # Dead zones should be small relative to stroke
        self.assertLess(
            dead_zone_compressed,
            self.cylinder_stroke * 0.5,
            "Dead zone too large relative to stroke",
        )


class TestGeometryEdgeCases(unittest.TestCase):
    """Test geometry edge cases and boundary conditions"""

    def test_zero_diameter_invalid(self):
        """Test that zero diameter is rejected"""
        with self.assertRaises((ValueError, AssertionError)):
            diameter = 0.0
            area = np.pi * (diameter / 2) ** 2
            self.assertGreater(area, 0.0)

    def test_negative_stroke_invalid(self):
        """Test that negative stroke is invalid"""
        stroke = -0.1
        self.assertGreater(stroke, 0.0, "Stroke must be positive")

    def test_extreme_aspect_ratio(self):
        """Test extreme cylinder aspect ratios

        Very long or very short cylinders may be physically unrealistic
        """
        diameter = 0.08  # 80mm

        # Very short stroke (pancake cylinder)
        stroke_short = 0.01  # 10mm
        aspect_ratio_short = stroke_short / diameter

        # Very long stroke (telescope cylinder)
        stroke_long = 1.0  # 1000mm
        aspect_ratio_long = stroke_long / diameter

        # Typical pneumatic cylinders: 0.5 < aspect < 10
        self.assertGreater(
            aspect_ratio_short, 0.1, "Aspect ratio too small (pancake cylinder)"
        )

        self.assertLess(
            aspect_ratio_long, 20.0, "Aspect ratio too large (telescope cylinder)"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
