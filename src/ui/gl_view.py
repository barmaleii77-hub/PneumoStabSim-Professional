"""
OpenGL widget for 3D visualization
"""
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import QTimer
from PySide6.QtGui import QSurfaceFormat
import OpenGL.GL as gl


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
        
        # Setup timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS
        
    def initializeGL(self):
        """Initialize OpenGL context"""
        gl.glClearColor(0.2, 0.2, 0.2, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)
        
    def paintGL(self):
        """Render OpenGL scene"""
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        # TODO: Add 3D rendering code here
        # For now, just clear the buffer with background color
        
    def resizeGL(self, width, height):
        """Handle OpenGL viewport resize"""
        gl.glViewport(0, 0, width, height)
        
        # TODO: Update projection matrix here