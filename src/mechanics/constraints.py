"""
Geometric constraints and invariants for P13 kinematics

Implements:
- Track ? arm_length ? pivot_offset invariant
- Parameter bounds validation
- Linked parameters (front/rear rod diameter)

References:
- numpy: https://numpy.org/doc/stable/
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import numpy as np


class ConstraintMode(Enum):
    """Which parameter is fixed when enforcing track invariant"""
    FIX_TRACK = "fix_track"              # Adjust arm_length or pivot_offset
    FIX_ARM_LENGTH = "fix_arm_length"    # Adjust track or pivot_offset
    FIX_PIVOT_OFFSET = "fix_pivot_offset"  # Adjust track or arm_length


@dataclass
class GeometricBounds:
    """Bounds for geometric parameters"""
    
    # Lever bounds
    min_arm_length: float = 0.2  # m (200mm minimum)
    max_arm_length: float = 0.8  # m (800mm maximum)
    
    min_pivot_offset: float = 0.1  # m (100mm minimum)
    max_pivot_offset: float = 0.6  # m (600mm maximum)
    
    min_wheelbase: float = 1.0  # m
    max_wheelbase: float = 3.5  # m
    
    # Rod attachment fraction bounds
    min_rod_attach_fraction: float = 0.1  # 10% from pivot
    max_rod_attach_fraction: float = 0.9  # 90% from pivot
    
    # Cylinder bounds
    min_cylinder_diameter: float = 0.04  # m (40mm)
    max_cylinder_diameter: float = 0.15  # m (150mm)
    
    min_rod_diameter: float = 0.015  # m (15mm)
    max_rod_diameter: float = 0.06   # m (60mm)
    
    min_piston_thickness: float = 0.01  # m (10mm)
    max_piston_thickness: float = 0.05  # m (50mm)
    
    # Residual volume as fraction of full cylinder volume
    min_residual_fraction: float = 0.005  # 0.5%


class ConstraintValidator:
    """Validator for geometric constraints and invariants"""
    
    def __init__(self, bounds: Optional[GeometricBounds] = None):
        self.bounds = bounds or GeometricBounds()
        
    def validate_track_invariant(
        self, 
        wheelbase: float, 
        arm_length: float, 
        pivot_offset: float,
        tolerance: float = 1e-6
    ) -> bool:
        """Validate track = 2 * (arm_length + pivot_offset)
        
        Args:
            wheelbase: Track width (m)
            arm_length: Lever arm length (m)
            pivot_offset: Offset from frame to pivot (m)
            tolerance: Numerical tolerance (m)
            
        Returns:
            True if invariant holds
        """
        expected_track = 2.0 * (arm_length + pivot_offset)
        return abs(wheelbase - expected_track) < tolerance
    
    def enforce_track_invariant(
        self,
        wheelbase: float,
        arm_length: float,
        pivot_offset: float,
        mode: ConstraintMode
    ) -> tuple[float, float, float]:
        """Enforce track invariant by adjusting one parameter
        
        Args:
            wheelbase: Current track width
            arm_length: Current arm length
            pivot_offset: Current pivot offset
            mode: Which parameter to fix
            
        Returns:
            (wheelbase, arm_length, pivot_offset) satisfying invariant
        """
        if mode == ConstraintMode.FIX_TRACK:
            # Adjust arm_length or pivot_offset to match track
            # Keep pivot_offset, adjust arm_length
            arm_length = (wheelbase / 2.0) - pivot_offset
            
        elif mode == ConstraintMode.FIX_ARM_LENGTH:
            # Adjust track or pivot_offset
            # Keep arm_length, adjust pivot_offset
            pivot_offset = (wheelbase / 2.0) - arm_length
            
        elif mode == ConstraintMode.FIX_PIVOT_OFFSET:
            # Adjust track or arm_length
            # Keep pivot_offset, adjust wheelbase
            wheelbase = 2.0 * (arm_length + pivot_offset)
            
        return wheelbase, arm_length, pivot_offset
    
    def validate_max_vertical_travel(
        self,
        arm_length: float,
        max_free_end_y: float
    ) -> bool:
        """Validate max vertical travel ? 2 * arm_length
        
        Args:
            arm_length: Lever arm length
            max_free_end_y: Maximum vertical displacement of free end
            
        Returns:
            True if within bounds
        """
        # Physical limit: free end can't move more than ±arm_length
        # Conservative limit: ±arm_length (total range = 2*arm_length)
        return abs(max_free_end_y) <= arm_length
    
    def validate_rod_attach_fraction(
        self,
        fraction: float
    ) -> bool:
        """Validate rod attachment point fraction ? [0.1, 0.9]"""
        return (self.bounds.min_rod_attach_fraction <= fraction <= 
                self.bounds.max_rod_attach_fraction)
    
    def validate_residual_volume(
        self,
        residual_volume: float,
        cylinder_diameter: float,
        cylinder_stroke: float
    ) -> bool:
        """Validate residual volume ? 0.5% of full cylinder volume
        
        Args:
            residual_volume: Dead zone volume (m?)
            cylinder_diameter: Inner diameter (m)
            cylinder_stroke: Full stroke (m)
            
        Returns:
            True if residual is sufficient
        """
        area = np.pi * (cylinder_diameter / 2.0) ** 2
        full_volume = area * cylinder_stroke
        min_required = full_volume * self.bounds.min_residual_fraction
        
        return residual_volume >= min_required
    
    def validate_geometry_params(
        self,
        wheelbase: float,
        arm_length: float,
        pivot_offset: float,
        rod_attach_fraction: float,
        cylinder_diameter: float,
        rod_diameter: float
    ) -> tuple[bool, list[str]]:
        """Validate all geometric parameters
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Track invariant
        if not self.validate_track_invariant(wheelbase, arm_length, pivot_offset):
            errors.append(
                f"Track invariant violated: {wheelbase:.3f} ? 2*({arm_length:.3f}+{pivot_offset:.3f})"
            )
        
        # Bounds checks
        if not (self.bounds.min_arm_length <= arm_length <= self.bounds.max_arm_length):
            errors.append(
                f"Arm length {arm_length:.3f}m out of range "
                f"[{self.bounds.min_arm_length}, {self.bounds.max_arm_length}]"
            )
        
        if not (self.bounds.min_pivot_offset <= pivot_offset <= self.bounds.max_pivot_offset):
            errors.append(
                f"Pivot offset {pivot_offset:.3f}m out of range "
                f"[{self.bounds.min_pivot_offset}, {self.bounds.max_pivot_offset}]"
            )
        
        if not (self.bounds.min_wheelbase <= wheelbase <= self.bounds.max_wheelbase):
            errors.append(
                f"Wheelbase {wheelbase:.3f}m out of range "
                f"[{self.bounds.min_wheelbase}, {self.bounds.max_wheelbase}]"
            )
        
        if not self.validate_rod_attach_fraction(rod_attach_fraction):
            errors.append(
                f"Rod attach fraction {rod_attach_fraction:.2f} out of range "
                f"[{self.bounds.min_rod_attach_fraction}, {self.bounds.max_rod_attach_fraction}]"
            )
        
        # Cylinder geometry
        if rod_diameter >= cylinder_diameter:
            errors.append(
                f"Rod diameter {rod_diameter:.4f}m >= cylinder diameter {cylinder_diameter:.4f}m"
            )
        
        return len(errors) == 0, errors


class LinkedParameters:
    """Manager for linked parameter relationships"""
    
    def __init__(self):
        self.link_front_rear_rod_diameter = False
        
    def sync_rod_diameters(
        self,
        front_diameter: float,
        rear_diameter: float,
        changed_side: str = "front"
    ) -> tuple[float, float]:
        """Synchronize front and rear rod diameters if linked
        
        Args:
            front_diameter: Front rod diameter
            rear_diameter: Rear rod diameter
            changed_side: Which side was modified ("front" or "rear")
            
        Returns:
            (front_diameter, rear_diameter) after sync
        """
        if not self.link_front_rear_rod_diameter:
            return front_diameter, rear_diameter
        
        if changed_side == "front":
            # Copy front to rear
            return front_diameter, front_diameter
        else:
            # Copy rear to front
            return rear_diameter, rear_diameter


# ==============================================================================
# Convenience functions
# ==============================================================================

def calculate_full_cylinder_volume(diameter: float, stroke: float) -> float:
    """Calculate full cylinder volume
    
    Args:
        diameter: Inner diameter (m)
        stroke: Full stroke (m)
        
    Returns:
        Volume (m?)
    """
    area = np.pi * (diameter / 2.0) ** 2
    return area * stroke


def calculate_min_residual_volume(diameter: float, stroke: float, fraction: float = 0.005) -> float:
    """Calculate minimum residual volume (default 0.5%)
    
    Args:
        diameter: Inner diameter (m)
        stroke: Full stroke (m)
        fraction: Residual fraction (default 0.005 = 0.5%)
        
    Returns:
        Minimum residual volume (m?)
    """
    return calculate_full_cylinder_volume(diameter, stroke) * fraction


__all__ = [
    'ConstraintMode',
    'GeometricBounds',
    'ConstraintValidator',
    'LinkedParameters',
    'calculate_full_cylinder_volume',
    'calculate_min_residual_volume',
]
