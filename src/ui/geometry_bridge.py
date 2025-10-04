# -*- coding: utf-8 -*-
"""
Geometry-to-3D bridge module
Converts 2D kinematics geometry to 3D visualization coordinates
INTEGRATED WITH USER INTERFACE CONTROLS
"""
import numpy as np
from PySide6.QtGui import QVector3D
from PySide6.QtCore import QObject, Signal, Property
from typing import Dict, Any, Optional

from ..core.geometry import GeometryParams, Point2


class GeometryTo3DConverter(QObject):
    """Converts 2D geometry parameters to 3D visualization coordinates
    WITH USER INTERFACE INTEGRATION"""
    
    # Signals for parameter changes
    geometryChanged = Signal()
    frameChanged = Signal()
    
    def __init__(self, geometry: GeometryParams):
        """Initialize geometry bridge converter"""
        super().__init__()
        self.geometry = geometry
        
        # USER-CONTROLLABLE PARAMETERS (will be connected to UI)
        self._frame_beam_size = 120.0       # mm - beam size
        self._frame_height = 650.0          # mm - horn height  
        self._frame_length = 2000.0         # mm - frame length (2 meters!)
        self._lever_length = 315.0          # mm - lever length
        self._cylinder_body_length = 250.0  # mm - cylinder working length
        self._tail_rod_length = 100.0       # mm - tail extension length
        
        # Z-coordinates for front/rear - calculated from frame length
        self._front_z = -self._frame_length / 2.0   # Front at -1000mm
        self._rear_z = self._frame_length / 2.0     # Rear at +1000mm
        
        print(f"    GeometryBridge initialized:")
        print(f"      Frame: {self._frame_length:.0f}x{self._frame_height:.0f}x{self._frame_beam_size:.0f}mm")
        print(f"      Lever: {self._lever_length:.0f}mm")
        print(f"      Cylinder: {self._cylinder_body_length:.0f}mm + {self._tail_rod_length:.0f}mm tail")
        
    # USER-CONTROLLABLE PROPERTIES (connected to UI sliders/spinboxes)
    
    @Property(float, notify=frameChanged)
    def frameLength(self):
        return self._frame_length
    
    @frameLength.setter
    def frameLength(self, value):
        if self._frame_length != value:
            self._frame_length = value
            self._front_z = -value / 2.0
            self._rear_z = value / 2.0
            self.frameChanged.emit()
            self.geometryChanged.emit()
    
    @Property(float, notify=frameChanged)
    def frameHeight(self):
        return self._frame_height
    
    @frameHeight.setter
    def frameHeight(self, value):
        if self._frame_height != value:
            self._frame_height = value
            self.frameChanged.emit()
            self.geometryChanged.emit()
    
    @Property(float, notify=frameChanged)
    def frameBeamSize(self):
        return self._frame_beam_size
    
    @frameBeamSize.setter
    def frameBeamSize(self, value):
        if self._frame_beam_size != value:
            self._frame_beam_size = value
            self.frameChanged.emit()
            self.geometryChanged.emit()
    
    @Property(float, notify=geometryChanged)
    def leverLength(self):
        return self._lever_length
    
    @leverLength.setter
    def leverLength(self, value):
        if self._lever_length != value:
            self._lever_length = value
            self.geometryChanged.emit()
    
    @Property(float, notify=geometryChanged)
    def cylinderBodyLength(self):
        return self._cylinder_body_length
    
    @cylinderBodyLength.setter
    def cylinderBodyLength(self, value):
        if self._cylinder_body_length != value:
            self._cylinder_body_length = value
            self.geometryChanged.emit()
    
    @Property(float, notify=geometryChanged)
    def tailRodLength(self):
        return self._tail_rod_length
    
    @tailRodLength.setter
    def tailRodLength(self, value):
        if self._tail_rod_length != value:
            self._tail_rod_length = value
            self.geometryChanged.emit()
        
    def get_frame_params(self) -> Dict[str, float]:
        """Get frame parameters for 3D visualization"""
        return {
            'beamSize': self._frame_beam_size,
            'frameHeight': self._frame_height,
            'frameLength': self._frame_length
        }
    
    def get_corner_3d_coords(self, corner: str, lever_angle_deg: float = 0.0) -> Dict[str, Any]:
        """Convert 2D kinematics to 3D coordinates for one corner
        USING CORRECTED SUSPENSION MECHANICS FROM test_2m_suspension.py
        
        Args:
            corner: 'fl', 'fr', 'rl', 'rr'
            lever_angle_deg: Current lever angle in degrees
            
        Returns:
            Dictionary with 3D coordinates for QML (compatible with CorrectedSuspensionCorner)
        """
        # Determine side and position
        is_left = corner.endswith('l')    # fl, rl = left side
        is_front = corner.startswith('f') # fl, fr = front
        
        # Side multiplier for mirroring
        side_mult = -1.0 if is_left else 1.0
        
        # Z position (longitudinal)
        z_plane = self._front_z if is_front else self._rear_z
        
        # FIXED FRAME ATTACHMENT POINTS (never change)
        
        # Lever pivot (j_arm) - FIXED attachment to frame
        pivot_offset_x = 150.0  # mm from center
        pivot_height = self._frame_beam_size / 2.0  # ON BEAM AXIS
        
        j_arm = QVector3D(
            pivot_offset_x * side_mult,  # ±150mm from center
            pivot_height,                # beam axis height
            z_plane                      # EXACTLY in plane
        )
        
        # Cylinder tail (j_tail) - FIXED attachment to frame
        horn_height = self._frame_beam_size + self._frame_height  # total horn height
        tail_height = horn_height - self._frame_beam_size / 2    # horn top minus offset
        tail_offset_x = 100.0  # mm from center
        
        j_tail = QVector3D(
            tail_offset_x * side_mult,   # ±100mm from center
            tail_height,                 # horn height
            z_plane                      # EXACTLY in plane
        )
        
        # MOVING PARTS (depend on lever angle)
        
        # Base angle: LEFT side points LEFT (180°), RIGHT side points RIGHT (0°)
        base_angle_deg = 180.0 if is_left else 0.0
        total_angle_deg = base_angle_deg + lever_angle_deg
        total_angle_rad = np.deg2rad(total_angle_deg)
        
        # Rod attachment point on lever (at lever end)
        rod_attach_x = j_arm.x() + self._lever_length * np.cos(total_angle_rad)
        rod_attach_y = j_arm.y() + self._lever_length * np.sin(total_angle_rad)
        
        j_rod = QVector3D(
            rod_attach_x,
            rod_attach_y,
            z_plane
        )
        
        # Return data compatible with CorrectedSuspensionCorner.qml
        result = {
            # FIXED joints
            'j_arm': j_arm,          # Lever pivot (orange joint)
            'j_tail': j_tail,        # Cylinder mount (blue joint)
            'j_rod': j_rod,          # Rod attachment (green joint)
            
            # Animation
            'leverAngle': lever_angle_deg,
            
            # Dimensions (for QML calculations)
            'leverLength': self._lever_length,
            'cylinderBodyLength': self._cylinder_body_length,
            'tailRodLength': self._tail_rod_length,
            
            # Additional data for UI
            'corner': corner,
            'totalAngle': total_angle_deg,
            'baseAngle': base_angle_deg,
            'side': 'left' if is_left else 'right',
            'position': 'front' if is_front else 'rear'
        }
        
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
        
        if 'lever_angles' in sim_state:
            lever_angles = sim_state['lever_angles']
        else:
            # Extract from individual angle fields
            lever_angles = {
                'fl': sim_state.get('fl_angle', 0.0),
                'fr': sim_state.get('fr_angle', 0.0), 
                'rl': sim_state.get('rl_angle', 0.0),
                'rr': sim_state.get('rr_angle', 0.0)
            }
        
        return {
            'frame': self.get_frame_params(),
            'corners': self.get_all_corners_3d(lever_angles),
            # Add user-controllable parameters
            'userParams': {
                'frameLength': self._frame_length,
                'frameHeight': self._frame_height,
                'frameBeamSize': self._frame_beam_size,
                'leverLength': self._lever_length,
                'cylinderBodyLength': self._cylinder_body_length,
                'tailRodLength': self._tail_rod_length
            }
        }
    
    def update_user_parameters(self, params: Dict[str, float]):
        """Update multiple user parameters at once
        
        Args:
            params: Dictionary with parameter names and values
        """
        changed = False
        
        if 'frameLength' in params and params['frameLength'] != self._frame_length:
            self.frameLength = params['frameLength']
            changed = True
            
        if 'frameHeight' in params and params['frameHeight'] != self._frame_height:
            self.frameHeight = params['frameHeight']
            changed = True
            
        if 'frameBeamSize' in params and params['frameBeamSize'] != self._frame_beam_size:
            self.frameBeamSize = params['frameBeamSize']
            changed = True
            
        if 'leverLength' in params and params['leverLength'] != self._lever_length:
            self.leverLength = params['leverLength']
            changed = True
            
        if 'cylinderBodyLength' in params and params['cylinderBodyLength'] != self._cylinder_body_length:
            self.cylinderBodyLength = params['cylinderBodyLength']
            changed = True
            
        if 'tailRodLength' in params and params['tailRodLength'] != self._tail_rod_length:
            self.tailRodLength = params['tailRodLength']
            changed = True
        
        if changed:
            print(f"    GeometryBridge updated: {params}")


# Convenience function for easy integration
def create_geometry_converter(wheelbase: float = 2.0, 
                            lever_length: float = 0.315,
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