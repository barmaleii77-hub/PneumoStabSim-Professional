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
        """Initialize geometry bridge converter"""
        self.geometry = geometry
        
        # NEW 2-meter dimensions (matching test_2m_suspension.py)
        self.frame_beam_size = 120.0       # mm - beam size
        self.frame_height = 650.0          # mm - horn height  
        self.frame_length = 2000.0         # mm - frame length (2 meters!)
        
        # Z-coordinates for front/rear - 2 meters between planes
        self.front_z = -1000.0   # Front at -1000mm
        self.rear_z = 1000.0     # Rear at +1000mm (distance 2000mm)
        
        print(f"    Frame setup: length={self.frame_length:.0f}mm, front_z={self.front_z:.0f}, rear_z={self.rear_z:.0f}")
        
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
        print(f"    Corner {corner}: left={is_left}, front={is_front}, angle={lever_angle_deg:.1f}deg")
        
        # Side multiplier for mirroring
        side_mult = -1.0 if is_left else 1.0
        
        # Z position (longitudinal) - front is negative, rear positive
        z_plane = self.front_z if is_front else self.rear_z
        
        # FIXED FRAME ATTACHMENT POINTS (never change)
        
        # Lever pivot (j_arm) - FIXED attachment to frame
        pivot_offset_x = 150.0  # mm from center (300mm between levers: ±150)
        pivot_height = self.frame_beam_size / 2.0  # ON BEAM AXIS: 120/2 = 60mm
        
        j_arm = QVector3D(
            pivot_offset_x * side_mult,  # ±150mm from center
            pivot_height,                # 60mm (axis of lower beam)
            z_plane                      # EXACTLY in plane
        )
        
        # Cylinder tail (j_tail) - FIXED attachment to frame
        horn_height = self.frame_beam_size + self.frame_height  # 120 + 650 = 770mm
        tail_height = horn_height - self.frame_beam_size / 2    # 770 - 60 = 710mm  
        tail_offset_x = 100.0  # mm from center (200mm between tails: ±100)
        
        j_tail = QVector3D(
            tail_offset_x * side_mult,   # ±100mm from center
            tail_height,                 # 710mm (horn height minus half section)
            z_plane                      # EXACTLY in plane
        )
        
        # MOVING PARTS (depend on lever angle)
        
        # Lever geometry
        lever_length_mm = self.geometry.lever_length * 1000.0  # 450mm
        angle_rad = np.deg2rad(lever_angle_deg)
        
        # Rod attachment point on lever (70% from pivot)
        attach_frac = self.geometry.rod_attach_fraction  # 0.7
        rod_attach_x = pivot_offset_x + lever_length_mm * attach_frac * np.cos(angle_rad)
        rod_attach_y = pivot_height + lever_length_mm * attach_frac * np.sin(angle_rad)
        
        j_rod_on_lever = QVector3D(
            rod_attach_x * side_mult,
            rod_attach_y,
            z_plane
        )
        
        # CYLINDER MECHANICS (fixed length, rod extends/retracts)
        
        # Cylinder body parameters
        cylinder_length_mm = self.geometry.cylinder_body_length * 1000.0  # 250mm - CONSTANT!
        
        # Direction from tail to rod attachment
        dx = j_rod_on_lever.x() - j_tail.x()
        dy = j_rod_on_lever.y() - j_tail.y()
        distance = np.hypot(dx, dy)
        
        # Unit direction vector
        if distance > 0:
            dir_x = dx / distance
            dir_y = dy / distance
        else:
            dir_x, dir_y = 1.0, 0.0
        
        # Cylinder END position (fixed distance from tail)
        cylinder_end_x = j_tail.x() + cylinder_length_mm * dir_x  
        cylinder_end_y = j_tail.y() + cylinder_length_mm * dir_y
        
        j_cylinder_end = QVector3D(cylinder_end_x, cylinder_end_y, z_plane)
        
        # Rod extends from cylinder end to lever attachment
        rod_extension = distance - cylinder_length_mm  # How much rod sticks out
        
        # Piston position (inside cylinder, depends on rod extension)
        # When rod is fully retracted, piston is at cylinder end
        # When rod extends, piston moves back proportionally
        max_stroke = 150.0  # mm - maximum stroke
        piston_position_ratio = max(0.0, min(1.0, rod_extension / max_stroke))
        
        piston_x = j_tail.x() + cylinder_length_mm * (1.0 - piston_position_ratio * 0.8) * dir_x
        piston_y = j_tail.y() + cylinder_length_mm * (1.0 - piston_position_ratio * 0.8) * dir_y
        
        j_piston = QVector3D(piston_x, piston_y, z_plane)
        
        # Cylinder dimensions
        bore_d_mm = self.geometry.cylinder_inner_diameter * 1000.0  # 85mm
        rod_d_mm = self.geometry.rod_diameter * 1000.0              # 32mm  
        piston_thickness_mm = self.geometry.piston_thickness * 1000.0  # 20mm
        
        # Dead volumes
        dead_bo_vol = self.geometry.dead_zone_head
        dead_sh_vol = self.geometry.dead_zone_rod
        
        # Mass
        mass_unsprung = 65.0  # kg
        
        result = {
            # Lever geometry (FIXED pivot, MOVING attachment)
            'j_arm': j_arm,                    # FIXED pivot point
            'j_rod': j_rod_on_lever,           # MOVING rod attachment on lever
            'armLength': lever_length_mm,
            'armAngleDeg': lever_angle_deg,
            'attachFrac': attach_frac,
            
            # Cylinder geometry (FIXED length and position)
            'j_tail': j_tail,                  # FIXED tail attachment  
            'j_cylinder_end': j_cylinder_end,  # FIXED cylinder end
            'j_piston': j_piston,              # MOVING piston position
            'cylinder_length': cylinder_length_mm,  # CONSTANT!
            'rod_extension': rod_extension,    # How much rod sticks out
            'bore_d': bore_d_mm,
            'rod_d': rod_d_mm,
            'L_body': cylinder_length_mm,      # Same as cylinder_length
            'piston_thickness': piston_thickness_mm,
            'dead_bo_vol': dead_bo_vol,
            'dead_sh_vol': dead_sh_vol,
            's_min': 50.0,  # mm
            
            # Mass
            'mass_unsprung': mass_unsprung
        }
        
        # Debug coordinates
        print(f"      j_arm: ({j_arm.x():.0f}, {j_arm.y():.0f}, {j_arm.z():.0f}) [FIXED]")
        print(f"      j_tail: ({j_tail.x():.0f}, {j_tail.y():.0f}, {j_tail.z():.0f}) [FIXED]")
        print(f"      j_rod: ({j_rod_on_lever.x():.0f}, {j_rod_on_lever.y():.0f}, {j_rod_on_lever.z():.0f}) [MOVING]")
        print(f"      cylinder_end: ({cylinder_end_x:.0f}, {cylinder_end_y:.0f}) [FIXED LENGTH]")
        print(f"      rod_extension: {rod_extension:.1f}mm")
        
        return result
    
    def get_all_corners_3d(self, lever_angles: Optional[Dict[str, float]] = None) -> Dict[str, Dict[str, Any]]:
        """Get 3D coordinates for all 4 corners
        
        Args:
            lever_angles: Optional dict with current lever angles {'fl': deg, 'fr': deg, 'rl': deg, 'rr': deg}
            
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