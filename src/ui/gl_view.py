"""
OpenGL widget for 3D visualization
"""
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import QTimer
from PySide6.QtGui import QSurfaceFormat
from typing import Optional
import OpenGL.GL as gl
import numpy as np

from ..runtime.state import StateSnapshot


class GLView(QOpenGLWidget):
    """OpenGL widget for 3D rendering"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set OpenGL format
        format = QSurfaceFormat()
        format.setVersion(3, 3)
        format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        format.setDepthBufferSize(24)
        format.setStencilBufferSize(8)
        self.setFormat(format)
        
        # Current state for rendering
        self.current_state: Optional[StateSnapshot] = None
        
        # Rendering parameters
        self.frame_count = 0
        
    def set_current_state(self, snapshot: StateSnapshot):
        """Set current state snapshot for rendering
        
        Args:
            snapshot: Current system state snapshot
        """
        self.current_state = snapshot
        
    def initializeGL(self):
        """Initialize OpenGL context"""
        gl.glClearColor(0.2, 0.2, 0.3, 1.0)  # Dark blue background
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # Print OpenGL info for debugging
        print(f"OpenGL Version: {gl.glGetString(gl.GL_VERSION).decode()}")
        print(f"OpenGL Renderer: {gl.glGetString(gl.GL_RENDERER).decode()}")
        
    def paintGL(self):
        """Render OpenGL scene"""
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        # Set up basic 3D projection and view
        self._setup_projection()
        self._setup_view()
        
        # Render coordinate axes
        self._render_axes()
        
        # Render vehicle frame if state is available
        if self.current_state:
            self._render_vehicle_frame()
            self._render_suspension_points()
            self._render_status_overlay()
        
        self.frame_count += 1
        
    def resizeGL(self, width, height):
        """Handle OpenGL viewport resize"""
        gl.glViewport(0, 0, width, height)
        
    def _setup_projection(self):
        """Setup 3D projection matrix"""
        width = self.width()
        height = max(self.height(), 1)
        aspect = width / height
        
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        
        # Simple perspective projection
        fov = 45.0
        near = 0.1
        far = 100.0
        
        # Manual perspective calculation (simplified)
        f = 1.0 / np.tan(np.radians(fov) / 2.0)
        
        # Apply perspective transformation
        gl.glMultMatrixf([
            f/aspect, 0, 0, 0,
            0, f, 0, 0,
            0, 0, (far+near)/(near-far), (2*far*near)/(near-far),
            0, 0, -1, 0
        ])
    
    def _setup_view(self):
        """Setup view matrix"""
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        
        # Camera position and orientation
        # Look at vehicle from behind and above
        eye = np.array([0.0, -3.0, 8.0])    # Camera position
        target = np.array([0.0, 0.0, 0.0])  # Look at origin
        up = np.array([0.0, 1.0, 0.0])      # Up vector
        
        # Simple lookAt implementation
        self._apply_lookat(eye, target, up)
    
    def _apply_lookat(self, eye, target, up):
        """Apply lookAt transformation"""
        forward = target - eye
        forward = forward / np.linalg.norm(forward)
        
        side = np.cross(forward, up)
        side = side / np.linalg.norm(side)
        
        up = np.cross(side, forward)
        
        # Apply rotation and translation
        m = np.array([
            [side[0], up[0], -forward[0], 0.0],
            [side[1], up[1], -forward[1], 0.0],
            [side[2], up[2], -forward[2], 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float32)
        
        gl.glMultMatrixf(m.flatten())
        gl.glTranslatef(-eye[0], -eye[1], -eye[2])
    
    def _render_axes(self):
        """Render coordinate axes"""
        gl.glLineWidth(2.0)
        gl.glBegin(gl.GL_LINES)
        
        # X axis (red)
        gl.glColor3f(1.0, 0.0, 0.0)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glVertex3f(2.0, 0.0, 0.0)
        
        # Y axis (green) - vertical, down positive
        gl.glColor3f(0.0, 1.0, 0.0)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glVertex3f(0.0, 2.0, 0.0)
        
        # Z axis (blue)
        gl.glColor3f(0.0, 0.0, 1.0)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glVertex3f(0.0, 0.0, 2.0)
        
        gl.glEnd()
    
    def _render_vehicle_frame(self):
        """Render vehicle frame outline"""
        if not self.current_state:
            return
        
        # Get frame state
        frame = self.current_state.frame
        
        # Apply frame transformations
        gl.glPushMatrix()
        
        # Apply heave (Y translation)
        gl.glTranslatef(0.0, frame.heave, 0.0)
        
        # Apply roll (rotation around Z)
        gl.glRotatef(np.degrees(frame.roll), 0.0, 0.0, 1.0)
        
        # Apply pitch (rotation around X)
        gl.glRotatef(np.degrees(frame.pitch), 1.0, 0.0, 0.0)
        
        # Render frame outline (simplified rectangle)
        wheelbase = 3.2  # From config
        track = 1.6
        
        gl.glColor3f(0.8, 0.8, 0.8)  # Light gray
        gl.glLineWidth(3.0)
        gl.glBegin(gl.GL_LINE_LOOP)
        
        # Frame corners
        gl.glVertex3f(-track/2, -0.1, -wheelbase/2)  # Left front
        gl.glVertex3f(+track/2, -0.1, -wheelbase/2)  # Right front
        gl.glVertex3f(+track/2, -0.1, +wheelbase/2)  # Right rear
        gl.glVertex3f(-track/2, -0.1, +wheelbase/2)  # Left rear
        
        gl.glEnd()
        
        # Center of mass indicator
        gl.glPointSize(8.0)
        gl.glColor3f(1.0, 1.0, 0.0)  # Yellow
        gl.glBegin(gl.GL_POINTS)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glEnd()
        
        gl.glPopMatrix()
    
    def _render_suspension_points(self):
        """Render suspension points and wheel positions"""
        if not self.current_state:
            return
        
        # Standard wheel layout
        wheel_positions = {
            'LP': (-0.8, 0.0, -1.6),  # Left front
            'PP': (+0.8, 0.0, -1.6),  # Right front
            'LZ': (-0.8, 0.0, +1.6),  # Left rear
            'PZ': (+0.8, 0.0, +1.6)   # Right rear
        }
        
        gl.glPointSize(6.0)
        
        for wheel_name, (x, y, z) in wheel_positions.items():
            # Get wheel state if available
            wheel_key = getattr(self.current_state.wheels, wheel_name, None)
            if wheel_key:
                # Add road excitation
                y += wheel_key.road_excitation
            
            # Color code by wheel position
            if 'L' in wheel_name:  # Left side
                gl.glColor3f(1.0, 0.5, 0.5)  # Red-ish
            else:  # Right side
                gl.glColor3f(0.5, 0.5, 1.0)  # Blue-ish
            
            gl.glBegin(gl.GL_POINTS)
            gl.glVertex3f(x, y, z)
            gl.glEnd()
    
    def _render_status_overlay(self):
        """Render status information overlay"""
        if not self.current_state:
            return
        
        # This would require text rendering setup
        # For now, just indicate status with colors
        
        # Show simulation running status
        if self.current_state.step_number > 0:
            gl.glPointSize(10.0)
            gl.glColor3f(0.0, 1.0, 0.0)  # Green = running
        else:
            gl.glPointSize(10.0)
            gl.glColor3f(1.0, 0.0, 0.0)  # Red = stopped
        
        # Status indicator in corner
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glOrtho(0, self.width(), self.height(), 0, -1, 1)
        
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        
        gl.glBegin(gl.GL_POINTS)
        gl.glVertex2f(20, 20)  # Top-left corner
        gl.glEnd()
        
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)