"""
OpenGL scene manager for 3D visualization
Handles geometry, shaders, and rendering of pneumatic suspension system
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from PySide6.QtOpenGL import (QOpenGLShaderProgram, QOpenGLBuffer, 
                              QOpenGLVertexArrayObject)
from PySide6.QtGui import QMatrix4x4, QVector3D, QOpenGLFunctions
from OpenGL import GL

from ..runtime.state import StateSnapshot


@dataclass
class MeshData:
    """Geometry mesh data"""
    vertices: np.ndarray  # Nx3 positions
    normals: Optional[np.ndarray] = None  # Nx3 normals
    colors: Optional[np.ndarray] = None   # Nx4 RGBA
    indices: Optional[np.ndarray] = None  # Triangles


class GLScene:
    """OpenGL scene with geometry, shaders, and rendering state"""
    
    def __init__(self, gl_functions: QOpenGLFunctions):
        """Initialize scene
        
        Args:
            gl_functions: OpenGL functions provider
        """
        self.gl = gl_functions
        
        # Rendering state
        self.initialized = False
        self.view_matrix = QMatrix4x4()
        self.proj_matrix = QMatrix4x4()
        
        # Shaders
        self.basic_shader: Optional[QOpenGLShaderProgram] = None
        self.gradient_shader: Optional[QOpenGLShaderProgram] = None
        
        # Geometry buffers (VAO/VBO)
        self.vaos: Dict[str, QOpenGLVertexArrayObject] = {}
        self.vbos: Dict[str, QOpenGLBuffer] = {}
        
        # Scene parameters (from configuration)
        self.wheelbase = 3.2  # m
        self.track = 1.6  # m
        self.scale = 1.0  # mm to GL units
        
        # Current simulation state
        self.current_snapshot: Optional[StateSnapshot] = None
        
    def initialize(self):
        """Initialize OpenGL resources
        
        Must be called from GL context (initializeGL)
        """
        if self.initialized:
            return
        
        # Create shaders
        self._create_shaders()
        
        # Create geometry
        self._create_frame_geometry()
        self._create_cylinder_geometry()
        self._create_tube_geometry()
        
        self.initialized = True
        
    def _create_shaders(self):
        """Create and compile shader programs"""
        # Basic color shader
        self.basic_shader = QOpenGLShaderProgram()
        
        # Vertex shader
        vert_src = """
        #version 330 core
        layout(location = 0) in vec3 position;
        layout(location = 1) in vec3 normal;
        layout(location = 2) in vec4 color;
        
        uniform mat4 mvp;
        uniform mat4 model;
        
        out vec3 fragNormal;
        out vec4 fragColor;
        out vec3 fragPosition;
        
        void main() {
            gl_Position = mvp * vec4(position, 1.0);
            fragNormal = mat3(model) * normal;
            fragColor = color;
            fragPosition = (model * vec4(position, 1.0)).xyz;
        }
        """
        
        # Fragment shader
        frag_src = """
        #version 330 core
        in vec3 fragNormal;
        in vec4 fragColor;
        in vec3 fragPosition;
        
        out vec4 outColor;
        
        void main() {
            // Simple directional lighting
            vec3 lightDir = normalize(vec3(0.5, -1.0, 0.3));
            vec3 normal = normalize(fragNormal);
            float diffuse = max(dot(normal, -lightDir), 0.0);
            float ambient = 0.3;
            
            vec3 lighting = vec3(ambient + diffuse * 0.7);
            outColor = vec4(fragColor.rgb * lighting, fragColor.a);
        }
        """
        
        self.basic_shader.addShaderFromSourceCode(
            QOpenGLShaderProgram.ShaderTypeBit.Vertex, vert_src)
        self.basic_shader.addShaderFromSourceCode(
            QOpenGLShaderProgram.ShaderTypeBit.Fragment, frag_src)
        
        if not self.basic_shader.link():
            print(f"Shader link error: {self.basic_shader.log()}")
        
    def _create_frame_geometry(self):
        """Create vehicle frame geometry"""
        # Simple rectangular frame outline
        half_track = self.track / 2.0
        half_wb = self.wheelbase / 2.0
        height = -0.1
        
        vertices = np.array([
            # Frame outline (box)
            [-half_track, height, -half_wb],  # 0: Left front bottom
            [+half_track, height, -half_wb],  # 1: Right front bottom
            [+half_track, height, +half_wb],  # 2: Right rear bottom
            [-half_track, height, +half_wb],  # 3: Left rear bottom
            [-half_track, height+0.2, -half_wb],  # 4: Left front top
            [+half_track, height+0.2, -half_wb],  # 5: Right front top
            [+half_track, height+0.2, +half_wb],  # 6: Right rear top
            [-half_track, height+0.2, +half_wb],  # 7: Left rear top
        ], dtype=np.float32)
        
        # Frame edges indices
        indices = np.array([
            # Bottom
            0, 1,  1, 2,  2, 3,  3, 0,
            # Top
            4, 5,  5, 6,  6, 7,  7, 4,
            # Verticals
            0, 4,  1, 5,  2, 6,  3, 7
        ], dtype=np.uint32)
        
        # Colors (gray frame)
        colors = np.tile([0.8, 0.8, 0.8, 1.0], (len(vertices), 1)).astype(np.float32)
        
        # Create VAO/VBO
        vao = QOpenGLVertexArrayObject()
        vao.create()
        vao.bind()
        
        vbo = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        vbo.create()
        vbo.bind()
        
        # Interleave vertices and colors
        vertex_data = np.hstack([vertices, colors]).flatten().astype(np.float32)
        vbo.allocate(vertex_data.tobytes(), vertex_data.nbytes)
        
        # Setup vertex attributes
        stride = 7 * 4  # 3 pos + 4 color, each float32
        self.gl.glEnableVertexAttribArray(0)
        self.gl.glVertexAttribPointer(0, 3, GL.GL_FLOAT, False, stride, 0)
        self.gl.glEnableVertexAttribArray(2)
        self.gl.glVertexAttribPointer(2, 4, GL.GL_FLOAT, False, stride, 3*4)
        
        vao.release()
        vbo.release()
        
        self.vaos['frame'] = vao
        self.vbos['frame'] = vbo
        self.vbos['frame_indices'] = indices
        
    def _create_cylinder_geometry(self):
        """Create pneumatic cylinder geometry
        
        Cylinder consists of:
        - Transparent outer tube (glass)
        - Piston disk (with thickness)
        - Rod cylinder
        - End caps
        """
        # Simple cylinder (will be instanced per wheel)
        segments = 16
        radius = 0.04  # 80mm diameter = 40mm radius
        length = 0.5   # 500mm length
        
        vertices = []
        normals = []
        
        # Generate cylinder vertices
        for i in range(segments + 1):
            angle = 2.0 * np.pi * i / segments
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            
            # Bottom circle
            vertices.append([x, y, 0.0])
            normals.append([np.cos(angle), np.sin(angle), 0.0])
            
            # Top circle
            vertices.append([x, y, length])
            normals.append([np.cos(angle), np.sin(angle), 0.0])
        
        vertices = np.array(vertices, dtype=np.float32)
        normals = np.array(normals, dtype=np.float32)
        
        # Cylinder body is transparent
        colors = np.tile([0.7, 0.7, 0.9, 0.3], (len(vertices), 1)).astype(np.float32)
        
        # Create VAO/VBO for cylinder
        vao = QOpenGLVertexArrayObject()
        vao.create()
        vao.bind()
        
        vbo = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        vbo.create()
        vbo.bind()
        
        # Pack vertex data
        vertex_data = np.hstack([vertices, normals, colors]).flatten().astype(np.float32)
        vbo.allocate(vertex_data.tobytes(), vertex_data.nbytes)
        
        stride = 10 * 4  # 3 pos + 3 normal + 4 color
        self.gl.glEnableVertexAttribArray(0)
        self.gl.glVertexAttribPointer(0, 3, GL.GL_FLOAT, False, stride, 0)
        self.gl.glEnableVertexAttribArray(1)
        self.gl.glVertexAttribPointer(1, 3, GL.GL_FLOAT, False, stride, 3*4)
        self.gl.glEnableVertexAttribArray(2)
        self.gl.glVertexAttribPointer(2, 4, GL.GL_FLOAT, False, stride, 6*4)
        
        vao.release()
        vbo.release()
        
        self.vaos['cylinder'] = vao
        self.vbos['cylinder'] = vbo
        
    def _create_tube_geometry(self):
        """Create pneumatic tube/pipe geometry for flow visualization"""
        # Tubes will be created dynamically based on system configuration
        # For now, create a simple line strip template
        pass
        
    def update_from_snapshot(self, snapshot: StateSnapshot):
        """Update scene from simulation snapshot
        
        Args:
            snapshot: Current simulation state
        """
        self.current_snapshot = snapshot
        
    def render(self, proj: QMatrix4x4, view: QMatrix4x4):
        """Render the scene
        
        Args:
            proj: Projection matrix
            view: View matrix
        """
        if not self.initialized or not self.basic_shader:
            return
        
        self.proj_matrix = proj
        self.view_matrix = view
        
        # Enable blending for transparency
        self.gl.glEnable(GL.GL_BLEND)
        self.gl.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        
        # Render opaque objects first
        self._render_frame()
        
        # Then transparent objects
        self.gl.glDepthMask(False)  # Don't write to depth buffer
        self._render_cylinders()
        self.gl.glDepthMask(True)
        
    def _render_frame(self):
        """Render vehicle frame"""
        if 'frame' not in self.vaos:
            return
        
        self.basic_shader.bind()
        
        # Setup matrices
        model = QMatrix4x4()
        
        # Apply frame transformations from snapshot
        if self.current_snapshot and self.current_snapshot.frame:
            frame = self.current_snapshot.frame
            model.translate(0.0, frame.heave, 0.0)
            model.rotate(np.degrees(frame.roll), 0, 0, 1)
            model.rotate(np.degrees(frame.pitch), 1, 0, 0)
        
        mvp = self.proj_matrix * self.view_matrix * model
        
        self.basic_shader.setUniformValue("mvp", mvp)
        self.basic_shader.setUniformValue("model", model)
        
        # Render frame lines
        vao = self.vaos['frame']
        vao.bind()
        
        indices = self.vbos['frame_indices']
        self.gl.glDrawElements(GL.GL_LINES, len(indices), GL.GL_UNSIGNED_INT, indices)
        
        vao.release()
        self.basic_shader.release()
        
    def _render_cylinders(self):
        """Render pneumatic cylinders (transparent)"""
        if 'cylinder' not in self.vaos:
            return
        
        self.basic_shader.bind()
        vao = self.vaos['cylinder']
        vao.bind()
        
        # Render cylinder for each wheel
        wheel_positions = {
            'LP': (-0.8, 0.0, -1.6),
            'PP': (+0.8, 0.0, -1.6),
            'LZ': (-0.8, 0.0, +1.6),
            'PZ': (+0.8, 0.0, +1.6)
        }
        
        for wheel_name, (x, y, z) in wheel_positions.items():
            model = QMatrix4x4()
            model.translate(x, y, z)
            
            mvp = self.proj_matrix * self.view_matrix * model
            
            self.basic_shader.setUniformValue("mvp", mvp)
            self.basic_shader.setUniformValue("model", model)
            
            # Draw cylinder as triangle strip
            vertex_count = 34  # (16+1) * 2
            self.gl.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, vertex_count)
        
        vao.release()
        self.basic_shader.release()
        
    def cleanup(self):
        """Clean up OpenGL resources"""
        for vao in self.vaos.values():
            vao.destroy()
        for vbo in self.vbos.values():
            if isinstance(vbo, QOpenGLBuffer):
                vbo.destroy()
        
        if self.basic_shader:
            self.basic_shader.deleteLater()
        if self.gradient_shader:
            self.gradient_shader.deleteLater()
        
        self.initialized = False
