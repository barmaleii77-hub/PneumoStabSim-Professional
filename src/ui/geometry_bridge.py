# -*- coding: utf-8 -*-
"""
Geometry-to-3D bridge module
Converts 2D kinematics geometry to 3D visualization coordinates
"""
import numpy as np
from PySide6.QtGui import QVector3D
from typing import Dict, Any, Optional

from ..core.geometry import GeometryParams, Point2


class GeometryTo3DConverter:
    """Converts 2D geometry parameters to 3D visualization coordinates"""
    
    def __init__(self, geometry: GeometryParams):
        self.geometry = geometry
        
        # 3D coordinate mapping from 2D kinematics
        # 2D kinematics: X=transverse, Y=vertical
        # 3D visualization: X=lateral, Y=vertical, Z=longitudinal
        
        # Frame dimensions for 3D
        self.frame_beam_size = 120.0  # mm, cross-section
        self.frame_height = 650.0     # mm, vertical posts
        
        # Convert 2D wheelbase to 3D frame length
        self.frame_length = geometry.wheelbase * 1000.0  # m -> mm
        
        # Z-coordinates for front/rear (along vehicle) - более компактно
        wheelbase_mm = self.frame_length
        self.front_z = -wheelbase_mm * 0.3   # Front at -30% (closer to center)
        self.rear_z = wheelbase_mm * 0.3     # Rear at +30% (closer to center)
        
        print(f"    ??? Frame setup: length={self.frame_length:.0f}mm, front_z={self.front_z:.0f}, rear_z={self.rear_z:.0f}")
        
    def get_frame_params(self) -> Dict[str, float]:
        """Get frame parameters for 3D visualization"""
        return {
            'beamSize': self.frame_beam_size,
            'frameHeight': self.frame_height,
            'frameLength': self.frame_length
        }
    
    def get_corner_3d_coords(self, corner: str, lever_angle_deg: float = 0.0) -> Dict[str, Any]:
        """Convert 2D kinematics to 3D coordinates for one corner
        
        Args:
            corner: 'fl', 'fr', 'rl', 'rr'
            lever_angle_deg: Current lever angle in degrees
            
        Returns:
            Dictionary with 3D coordinates for QML
        """
        # Determine side and position
        is_left = corner[0] in ['f', 'r'] and corner[1] == 'l'   # fl, rl = left side
        is_front = corner[0] == 'f'                              # fl, fr = front
        
        # Debug print
        print(f"    ?? Corner {corner}: left={is_left}, front={is_front}")
        
        # Side multiplier for mirroring
        side_mult = -1.0 if is_left else 1.0
        
        # Z position (longitudinal) - front is negative, rear positive
        z_pos = self.front_z if is_front else self.rear_z
        
        # 2D kinematics in local wheel plane
        # Lever pivot point (attachment to frame)
        x_pivot_2d = self.geometry.pivot_offset_from_frame * 1000.0  # m -> mm
        y_pivot_2d = 150.0  # mm above ground (typical suspension height)
        
        # 3D lever pivot (j_arm) - MUST be on frame structure
        frame_edge_x = self.frame_beam_size / 2.0  # Distance to frame edge
        j_arm = QVector3D(
            (frame_edge_x + x_pivot_2d) * side_mult,  # X: extend outward from frame
            y_pivot_2d,                               # Y: height above ground
            z_pos                                     # Z: front/rear position
        )
        
        # Lever end position (with current angle)
        lever_length_mm = self.geometry.lever_length * 1000.0
        angle_rad = np.deg2rad(lever_angle_deg)
        
        # Lever extends horizontally outward from pivot
        x_lever_end = (frame_edge_x + x_pivot_2d + lever_length_mm * np.cos(angle_rad))
        y_lever_end = y_pivot_2d + lever_length_mm * np.sin(angle_rad)
        
        # Rod attachment point on lever
        attach_frac = self.geometry.rod_attach_fraction
        x_rod_attach = (frame_edge_x + x_pivot_2d + lever_length_mm * attach_frac * np.cos(angle_rad))
        y_rod_attach = y_pivot_2d + lever_length_mm * attach_frac * np.sin(angle_rad)
        
        # Cylinder attachment points (j_tail, j_rod)
        # Tail connects to frame structure (closer to centerline)
        j_tail = QVector3D(
            frame_edge_x * 0.5 * side_mult,         # Closer to frame centerline
            y_pivot_2d + 80.0,                      # Higher up on frame
            z_pos * 0.8                             # Slightly closer to center
        )
        
        # Rod connects to lever at attachment point
        j_rod = QVector3D(
            x_rod_attach * side_mult,
            y_rod_attach,
            z_pos
        )
        
        # Cylinder dimensions from geometry
        bore_d_mm = self.geometry.cylinder_inner_diameter * 1000.0
        rod_d_mm = self.geometry.rod_diameter * 1000.0
        L_body_mm = self.geometry.cylinder_body_length * 1000.0
        piston_thickness_mm = self.geometry.piston_thickness * 1000.0
        
        # Dead volumes (convert to consistent units)
        dead_bo_vol = self.geometry.dead_zone_head      # m?
        dead_sh_vol = self.geometry.dead_zone_rod       # m?
        
        # Mass estimation (typical unsprung mass per wheel)
        mass_unsprung = 65.0  # kg (wheel + brake + suspension components)
        
        result = {
            # Lever geometry
            'j_arm': j_arm,
            'armLength': lever_length_mm,
            'armAngleDeg': lever_angle_deg,
            'attachFrac': attach_frac,
            
            # Cylinder geometry  
            'j_tail': j_tail,
            'j_rod': j_rod,
            'bore_d': bore_d_mm,
            'rod_d': rod_d_mm,
            'L_body': L_body_mm,  # Python uses L_body, QML expects lBody
            'piston_thickness': piston_thickness_mm,
            'dead_bo_vol': dead_bo_vol,
            'dead_sh_vol': dead_sh_vol,
            's_min': 50.0,  # mm, minimum rod extension
            
            # Mass
            'mass_unsprung': mass_unsprung
        }
        
        # Debug coordinates
        print(f"      j_arm: ({j_arm.x():.0f}, {j_arm.y():.0f}, {j_arm.z():.0f})")
        print(f"      j_tail: ({j_tail.x():.0f}, {j_tail.y():.0f}, {j_tail.z():.0f})")
        print(f"      j_rod: ({j_rod.x():.0f}, {j_rod.y():.0f}, {j_rod.z():.0f})")
        
        return result
    
    def get_all_corners_3d(self, lever_angles: Optional[Dict[str, float]] = None) -> Dict[str, Dict[str, Any]]:
        """Get 3D coordinates for all 4 corners
        
        Args:
            lever_angles: Optional dict with current lever angles {'fl': deg, 'fr': deg, ...}
            
        Returns:
            Dictionary with all corner coordinates
        """
        if lever_angles is None:
            lever_angles = {'fl': 0.0, 'fr': 0.0, 'rl': 0.0, 'rr': 0.0}
        
        corners = {}
        for corner in ['fl', 'fr', 'rl', 'rr']:
            angle = lever_angles.get(corner, 0.0)
            corners[corner] = self.get_corner_3d_coords(corner, angle)
        
        return corners
    
    def update_from_simulation(self, sim_state: Dict[str, Any]) -> Dict[str, Any]:
        """Update 3D coordinates from simulation state
        
        Args:
            sim_state: Current simulation state with lever angles, etc.
            
        Returns:
            Complete geometry data for 3D scene update
        """
        # Extract lever angles from simulation
        lever_angles = {}
        
        # TODO: Connect to real simulation state structure
        # For now, use example angles
        if 'lever_angles' in sim_state:
            lever_angles = sim_state['lever_angles']
        else:
            # Default/test angles
            lever_angles = {
                'fl': sim_state.get('fl_angle', 0.0),
                'fr': sim_state.get('fr_angle', 0.0), 
                'rl': sim_state.get('rl_angle', 0.0),
                'rr': sim_state.get('rr_angle', 0.0)
            }
        
        return {
            'frame': self.get_frame_params(),
            **self.get_all_corners_3d(lever_angles)
        }


# Convenience function for easy integration
def create_geometry_converter(wheelbase: float = 2.5, 
                            lever_length: float = 0.4,
                            cylinder_diameter: float = 0.08) -> GeometryTo3DConverter:
    """Create geometry converter with common parameters
    
    Args:
        wheelbase: Vehicle track width in meters
        lever_length: Suspension lever length in meters  
        cylinder_diameter: Cylinder bore diameter in meters
        
    Returns:
        Configured GeometryTo3DConverter
    """
    geometry = GeometryParams()
    geometry.wheelbase = wheelbase
    geometry.lever_length = lever_length
    geometry.cylinder_inner_diameter = cylinder_diameter
    geometry.enforce_track_from_geometry()  # Ensure consistency
    
    return GeometryTo3DConverter(geometry)