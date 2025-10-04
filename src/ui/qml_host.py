# -*- coding: utf-8 -*-
"""
QML Host for full suspension 3D visualization
Embeds UFrameScene.qml with all 4 corners (FL/FR/RL/RR) into PySide6 application
Uses geometry_bridge.py for correct coordinate calculation
"""
from pathlib import Path
from PySide6.QtCore import QUrl, QObject, Signal, Slot
from PySide6.QtGui import QVector3D
from PySide6.QtQuickWidgets import QQuickWidget

# Import geometry bridge for correct coordinate calculation
from ..core.geometry import GeometryParams
from .geometry_bridge import GeometryTo3DConverter


class SuspensionSceneHost(QQuickWidget):
    """Host widget for full suspension scene with 4 corners"""
    
    # Signals for user interaction
    view_reset_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create geometry converter with 2-meter dimensions
        geometry_params = GeometryParams()
        geometry_params.lever_length = 0.45  # 450mm
        geometry_params.cylinder_inner_diameter = 0.085  # 85mm  
        geometry_params.rod_diameter = 0.032  # 32mm
        geometry_params.cylinder_body_length = 0.25  # 250mm
        geometry_params.piston_thickness = 0.02  # 20mm
        
        self.geometry_converter = GeometryTo3DConverter(geometry_params)
        
        # Get calculated coordinates for all corners
        all_corners = self.geometry_converter.get_all_corners_3d()
        frame_params = self.geometry_converter.get_frame_params()
        
        # Build parameters dictionary from geometry_bridge calculations
        self._params = {
            # Frame (from geometry_bridge)
            'beamSize': frame_params['beamSize'],
            'frameHeight': frame_params['frameHeight'], 
            'frameLength': frame_params['frameLength'],
        }
        
        # Add all corner parameters from geometry_bridge
        for corner_key in ['fl', 'fr', 'rl', 'rr']:
            corner_data = all_corners[corner_key]
            
            # Convert to QML property names
            self._params.update({
                f'{corner_key}_j_arm': corner_data['j_arm'],
                f'{corner_key}_armLength': corner_data['armLength'],
                f'{corner_key}_armAngleDeg': corner_data['armAngleDeg'],
                f'{corner_key}_attachFrac': corner_data['attachFrac'],
                f'{corner_key}_j_tail': corner_data['j_tail'],
                f'{corner_key}_j_rod': corner_data['j_rod'],
                f'{corner_key}_j_cylinder_end': corner_data.get('j_cylinder_end', corner_data['j_rod']),
                f'{corner_key}_j_piston': corner_data.get('j_piston', corner_data['j_rod']),
                f'{corner_key}_cylinder_length': corner_data.get('cylinder_length', corner_data['L_body']),
                f'{corner_key}_rod_extension': corner_data.get('rod_extension', 0.0),
                f'{corner_key}_bore_d': corner_data['bore_d'],
                f'{corner_key}_rod_d': corner_data['rod_d'],
                f'{corner_key}_L_body': corner_data['L_body'],
                f'{corner_key}_piston_thickness': corner_data['piston_thickness'],
                f'{corner_key}_dead_bo_vol': corner_data['dead_bo_vol'],
                f'{corner_key}_dead_sh_vol': corner_data['dead_sh_vol'],
                f'{corner_key}_s_min': corner_data['s_min'],
                f'{corner_key}_mass_unsprung': corner_data['mass_unsprung'],
            })
        
        print(f"? Loaded coordinates from geometry_bridge:")
        print(f"   Frame: {frame_params}")
        print(f"   FL j_arm: {all_corners['fl']['j_arm']}")
        print(f"   FR j_arm: {all_corners['fr']['j_arm']}")
        
        # Setup QML
        self.setResizeMode(QQuickWidget.SizeRootObjectToView)
        
        # Load QML scene
        qml_path = Path(__file__).parent.parent.parent / "assets" / "qml" / "UFrameScene.qml"
        print(f"?? SuspensionSceneHost: Loading QML from: {qml_path}")
        print(f"?? Path exists: {qml_path.exists()}")
        
        self.setSource(QUrl.fromLocalFile(str(qml_path)))
        
        # Check for QML errors
        if self.status() == QQuickWidget.Status.Error:
            errors = self.errors()
            error_msg = "\n".join(str(e) for e in errors)
            print(f"? QML ERRORS in UFrameScene.qml:\n{error_msg}")
            raise RuntimeError(f"QML errors:\n{error_msg}")
        
        print(f"? UFrameScene.qml loaded, status: {self.status()}")
        
        # Wait for QML to be fully ready, then apply parameters
        if self.status() == QQuickWidget.Status.Ready:
            self._apply_all_parameters()
        else:
            # Use a timer to apply parameters when ready
            from PySide6.QtCore import QTimer
            def delayed_apply():
                if self.status() == QQuickWidget.Status.Ready:
                    self._apply_all_parameters()
                else:
                    print("?? QML still not ready, retrying...")
                    QTimer.singleShot(100, delayed_apply)
            QTimer.singleShot(50, delayed_apply)
    
    def _apply_all_parameters(self):
        """Apply all parameters to QML root object"""
        root = self.rootObject()
        if not root:
            print("? WARNING: QML root object is None!")
            return
        
        applied_count = 0
        for key, value in self._params.items():
            try:
                root.setProperty(key, value)
                applied_count += 1
                if key in ['fl_j_arm', 'fr_j_arm']:  # Debug key coordinates
                    print(f"   Set {key} = {value}")
            except Exception as e:
                print(f"? Failed to set {key}: {e}")
                
        print(f"? Applied {applied_count}/{len(self._params)} parameters to QML")
    
    def update_corner(self, corner: str, **kwargs):
        """Update parameters for specific corner (FL/FR/RL/RR)
        
        Args:
            corner: "FL", "FR", "RL", or "RR"
            **kwargs: Parameter updates (e.g., armAngleDeg=5.0, j_rod=QVector3D(...))
        """
        root = self.rootObject()
        if not root:
            return
        
        for key, value in kwargs.items():
            prop_name = f"{corner}_{key}"
            if prop_name in self._params:
                self._params[prop_name] = value
                root.setProperty(prop_name, value)
    
    def update_frame(self, **kwargs):
        """Update frame parameters
        
        Args:
            **kwargs: beamSize, frameHeight, frameLength
        """
        root = self.rootObject()
        if not root:
            return
        
        for key in ['beamSize', 'frameHeight', 'frameLength']:
            if key in kwargs:
                self._params[key] = kwargs[key]
                root.setProperty(key, kwargs[key])
    
    def reset_view(self):
        """Reset camera to default view"""
        root = self.rootObject()
        if root:
            root.resetView()
    
    def auto_fit(self):
        """Auto-fit camera to entire scene"""
        root = self.rootObject()
        if root:
            root.autoFit()
    
    def get_parameters(self):
        """Get current parameters dictionary"""
        return self._params.copy()


# Backward compatibility alias
UFrameSceneHost = SuspensionSceneHost
