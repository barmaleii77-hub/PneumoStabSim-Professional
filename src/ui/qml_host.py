# -*- coding: utf-8 -*-
"""
QML Host for full suspension 3D visualization
Embeds UFrameScene.qml with all 4 corners (FL/FR/RL/RR) into PySide6 application
"""
from pathlib import Path
from PySide6.QtCore import QUrl, QObject, Signal, Slot
from PySide6.QtGui import QVector3D  # »—œ–¿¬À≈ÕŒ: QVector3D ‚ QtGui, ÌÂ QtCore!
from PySide6.QtQuickWidgets import QQuickWidget


class SuspensionSceneHost(QQuickWidget):
    """Host widget for full suspension scene with 4 corners"""
    
    # Signals for user interaction
    view_reset_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Scene parameters (defaults)
        self._params = {
            # Frame
            'beamSize': 100.0,
            'frameHeight': 600.0,
            'frameLength': 2000.0,
            
            # FL - Front Left
            'fl_j_arm': QVector3D(-800, 100, -1600),
            'fl_armLength': 500.0,
            'fl_armAngleDeg': 0.0,
            'fl_attachFrac': 0.7,
            'fl_j_tail': QVector3D(-500, 200, -1400),
            'fl_j_rod': QVector3D(-750, 150, -1500),
            'fl_bore_d': 80.0,
            'fl_rod_d': 40.0,
            'fl_L_body': 300.0,
            'fl_piston_thickness': 20.0,
            'fl_dead_bo_vol': 0.0001,
            'fl_dead_sh_vol': 0.0001,
            'fl_s_min': 50.0,
            'fl_mass_unsprung': 50.0,
            
            # FR - Front Right (mirror FL ÔÓ X)
            'fr_j_arm': QVector3D(800, 100, -1600),
            'fr_armLength': 500.0,
            'fr_armAngleDeg': 0.0,
            'fr_attachFrac': 0.7,
            'fr_j_tail': QVector3D(500, 200, -1400),
            'fr_j_rod': QVector3D(750, 150, -1500),
            'fr_bore_d': 80.0,
            'fr_rod_d': 40.0,
            'fr_L_body': 300.0,
            'fr_piston_thickness': 20.0,
            'fr_dead_bo_vol': 0.0001,
            'fr_dead_sh_vol': 0.0001,
            'fr_s_min': 50.0,
            'fr_mass_unsprung': 50.0,
            
            # RL - Rear Left
            'rl_j_arm': QVector3D(-800, 100, 1600),
            'rl_armLength': 500.0,
            'rl_armAngleDeg': 0.0,
            'rl_attachFrac': 0.7,
            'rl_j_tail': QVector3D(-500, 200, 1400),
            'rl_j_rod': QVector3D(-750, 150, 1500),
            'rl_bore_d': 80.0,
            'rl_rod_d': 40.0,
            'rl_L_body': 300.0,
            'rl_piston_thickness': 20.0,
            'rl_dead_bo_vol': 0.0001,
            'rl_dead_sh_vol': 0.0001,
            'rl_s_min': 50.0,
            'rl_mass_unsprung': 50.0,
            
            # RR - Rear Right (mirror RL ÔÓ X)
            'rr_j_arm': QVector3D(800, 100, 1600),
            'rr_armLength': 500.0,
            'rr_armAngleDeg': 0.0,
            'rr_attachFrac': 0.7,
            'rr_j_tail': QVector3D(500, 200, 1400),
            'rr_j_rod': QVector3D(750, 150, 1500),
            'rr_bore_d': 80.0,
            'rr_rod_d': 40.0,
            'rr_L_body': 300.0,
            'rr_piston_thickness': 20.0,
            'rr_dead_bo_vol': 0.0001,
            'rr_dead_sh_vol': 0.0001,
            'rr_s_min': 50.0,
            'rr_mass_unsprung': 50.0,
        }
        
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
        
        # Expose properties to QML
        self._apply_all_parameters()
    
    def _apply_all_parameters(self):
        """Apply all parameters to QML root object"""
        root = self.rootObject()
        if not root:
            print("?? WARNING: QML root object is None!")
            return
        
        for key, value in self._params.items():
            root.setProperty(key, value)
        
        print(f"? All {len(self._params)} parameters set in QML")
    
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
