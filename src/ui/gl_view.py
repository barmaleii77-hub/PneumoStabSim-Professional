"""
OpenGL widget for 3D visualization (P9: Modern OpenGL with shaders)
"""
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, QPoint, Slot
from PySide6.QtGui import QSurfaceFormat, QMatrix4x4, QVector3D, QPainter, QFont, QOpenGLFunctions
from typing import Optional
import numpy as np

from ..runtime.state import StateSnapshot
from .gl_scene import GLScene


class GLView(QOpenGLWidget, QOpenGLFunctions):
    """Modern OpenGL widget for 3D rendering with isometric camera"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set OpenGL format (Core Profile 3.3)
        format = QSurfaceFormat()
        format.setVersion(3, 3)
        format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        format.setDepthBufferSize(24)
        format.setStencilBufferSize(8)
        format.setSamples(4)  # MSAA
        self.setFormat(format)
        
        # Scene manager
        self.scene: Optional[GLScene] = None
        
        # Current state for rendering
        self.current_state: Optional[StateSnapshot] = None
        
        # Camera parameters (isometric view)
        self.camera_distance = 10.0
        self.camera_pan = QVector3D(0.0, 0.0, 0.0)
        self.camera_pitch = 35.264  # Isometric angle
        self.camera_yaw = 45.0      # Isometric angle
        
        # Mouse interaction
        self.last_mouse_pos: Optional[QPoint] = None
        self.is_panning = False
        self.is_rotating = False
        
        # Rendering statistics
        self.frame_count = 0
        self.show_overlay = True
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
    @Slot(object)
    def set_current_state(self, snapshot: StateSnapshot):
        """Set current state snapshot for rendering
        
        Args:
            snapshot: Current system state snapshot
        """
        self.current_state = snapshot
        if self.scene:
            self.scene.update_from_snapshot(snapshot)
        
    def initializeGL(self):
        """Initialize OpenGL context and resources"""
        # Initialize OpenGL functions
        self.initializeOpenGLFunctions()
        
        # Print OpenGL info
        import OpenGL.GL as gl
        print(f"OpenGL Version: {gl.glGetString(gl.GL_VERSION).decode()}")
        print(f"GLSL Version: {gl.glGetString(gl.GL_SHADING_LANGUAGE_VERSION).decode()}")
        print(f"Renderer: {gl.glGetString(gl.GL_RENDERER).decode()}")
        
        # Create scene
        self.scene = GLScene(self)
        self.scene.initialize()
        
        # Set up OpenGL state
        self.glClearColor(0.15, 0.15, 0.2, 1.0)  # Dark blue-gray background
        self.glEnable(self.GL_DEPTH_TEST)
        self.glEnable(self.GL_BLEND)
        self.glBlendFunc(self.GL_SRC_ALPHA, self.GL_ONE_MINUS_SRC_ALPHA)
        self.glEnable(self.GL_MULTISAMPLE)
        self.glEnable(self.GL_LINE_SMOOTH)
        self.glHint(self.GL_LINE_SMOOTH_HINT, self.GL_NICEST)
        
    def paintGL(self):
        """Render OpenGL scene"""
        self.glClear(self.GL_COLOR_BUFFER_BIT | self.GL_DEPTH_BUFFER_BIT)
        
        if not self.scene:
            return
        
        # Setup projection and view matrices
        proj = self._create_projection_matrix()
        view = self._create_view_matrix()
        
        # Render scene
        self.scene.render(proj, view)
        
        # Render 2D overlay
        if self.show_overlay:
            self._render_overlay()
        
        self.frame_count += 1
        
    def resizeGL(self, width, height):
        """Handle OpenGL viewport resize"""
        self.glViewport(0, 0, width, height)
        
    def _create_projection_matrix(self) -> QMatrix4x4:
        """Create orthographic projection matrix for isometric view
        
        Returns:
            Projection matrix
        """
        proj = QMatrix4x4()
        
        aspect = self.width() / max(self.height(), 1)
        ortho_height = self.camera_distance
        ortho_width = ortho_height * aspect
        
        # Orthographic projection for isometric view
        proj.ortho(-ortho_width, ortho_width,
                   -ortho_height, ortho_height,
                   0.1, 100.0)
        
        return proj
        
    def _create_view_matrix(self) -> QMatrix4x4:
        """Create view matrix for isometric camera
        
        Returns:
            View matrix
        """
        view = QMatrix4x4()
        
        # Camera position (looking from above and side)
        view.translate(0, 0, -self.camera_distance * 2)
        
        # Apply isometric rotations
        view.rotate(self.camera_pitch, 1, 0, 0)  # Pitch (up/down tilt)
        view.rotate(self.camera_yaw, 0, 1, 0)    # Yaw (left/right rotation)
        
        # Apply pan
        view.translate(
            -self.camera_pan.x(),
            -self.camera_pan.y(),
            -self.camera_pan.z()
        )
        
        return view
        
    def _render_overlay(self):
        """Render 2D overlay with status information"""
        # Use QPainter for 2D overlay (allowed in paintGL)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set font
        font = QFont("Consolas", 10)
        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.white)
        
        # Draw status info
        y_offset = 20
        line_height = 16
        
        if self.current_state:
            info_lines = [
                f"Time: {self.current_state.simulation_time:.3f}s",
                f"Step: {self.current_state.step_number}",
                f"FPS: {1.0/max(self.current_state.dt_physics, 0.001):.0f}",
                f"Heave: {self.current_state.frame.heave:.3f}m",
                f"Roll: {np.degrees(self.current_state.frame.roll):.2f}deg",
                f"Pitch: {np.degrees(self.current_state.frame.pitch):.2f}deg",
            ]
        else:
            info_lines = ["No simulation data"]
        
        for i, line in enumerate(info_lines):
            painter.drawText(10, y_offset + i * line_height, line)
        
        # Camera info
        painter.setPen(Qt.GlobalColor.lightGray)
        cam_info = [
            f"Zoom: {self.camera_distance:.1f}",
            f"Pan: ({self.camera_pan.x():.1f}, {self.camera_pan.y():.1f})"
        ]
        
        for i, line in enumerate(cam_info):
            painter.drawText(10, self.height() - 40 + i * line_height, line)
        
        painter.end()
        
    # Mouse interaction
    def wheelEvent(self, event):
        """Handle mouse wheel for zoom"""
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9
        
        self.camera_distance *= zoom_factor
        self.camera_distance = np.clip(self.camera_distance, 2.0, 50.0)
        
        self.update()
        
    def mousePressEvent(self, event):
        """Handle mouse button press"""
        self.last_mouse_pos = event.pos()
        
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_rotating = True
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
        
    def mouseReleaseEvent(self, event):
        """Handle mouse button release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_rotating = False
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
        
        self.last_mouse_pos = None
        
    def mouseMoveEvent(self, event):
        """Handle mouse move for pan/rotate"""
        if not self.last_mouse_pos:
            return
        
        delta = event.pos() - self.last_mouse_pos
        self.last_mouse_pos = event.pos()
        
        if self.is_rotating:
            # Rotate camera (adjust yaw/pitch)
            self.camera_yaw += delta.x() * 0.5
            self.camera_pitch += delta.y() * 0.5
            self.camera_pitch = np.clip(self.camera_pitch, -89.0, 89.0)
            self.update()
            
        elif self.is_panning:
            # Pan camera
            pan_speed = self.camera_distance * 0.003
            self.camera_pan += QVector3D(
                delta.x() * pan_speed,
                -delta.y() * pan_speed,
                0.0
            )
            self.update()