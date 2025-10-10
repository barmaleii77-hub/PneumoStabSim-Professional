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
from src.ui.geometry_bridge import GeometryTo3DConverter


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
            
            # Convert to QML property names (use correct keys from geometry_bridge)
            self._params.update({
                f'{corner_key}_j_arm': corner_data['j_arm'],
                f'{corner_key}_leverLength': corner_data['leverLength'],  # ? Correct key
                f'{corner_key}_leverAngle': corner_data['leverAngle'],   # ? New key
                f'{corner_key}_totalAngle': corner_data['totalAngle'],   # ? New key
                f'{corner_key}_baseAngle': corner_data['baseAngle'],     # ? New key
                f'{corner_key}_j_tail': corner_data['j_tail'],
                f'{corner_key}_j_rod': corner_data['j_rod'],
                f'{corner_key}_cylinderBodyLength': corner_data['cylinderBodyLength'],  # ? Correct key
                f'{corner_key}_tailRodLength': corner_data['tailRodLength'],           # ? Correct key
                
                # Additional properties for compatibility
                f'{corner_key}_corner': corner_data['corner'],
                f'{corner_key}_side': corner_data['side'],
                f'{corner_key}_position': corner_data['position'],
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
            print("?? WARNING: QML root object is None!")
            return
        
        applied_count = 0
        failed_count = 0
        
        print(f"?? Applying {len(self._params)} parameters to QML:")
        
        for key, value in self._params.items():
            try:
                root.setProperty(key, value)
                applied_count += 1
                
                # Debug key coordinates and lever lengths
                if key in ['fl_j_arm', 'fr_j_arm', 'fl_leverLength', 'fr_leverLength']:
                    print(f"   ? Set {key} = {value}")
                elif 'cylinderBodyLength' in key or 'tailRodLength' in key:
                    print(f"   ?? Set {key} = {value}")
                    
            except Exception as e:
                print(f"   ? Failed to set {key} = {value}: {e}")
                failed_count += 1
                
        print(f"? Applied {applied_count}/{len(self._params)} parameters to QML")
        if failed_count > 0:
            print(f"? Failed to apply {failed_count} parameters")
        
        # Debug: Try to read some values back
        print(f"?? Reading back some key values:")
        try:
            beamSize = root.property("beamSize") 
            frameLength = root.property("frameLength")
            fl_leverLength = root.property("fl_leverLength")
            print(f"   beamSize: {beamSize}")
            print(f"   frameLength: {frameLength}")
            print(f"   fl_leverLength: {fl_leverLength}")
        except Exception as e:
            print(f"   ? Failed to read back values: {e}")
    
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
