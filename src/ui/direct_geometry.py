#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Direct geometry usage - bypassing Property system completely
"""
import numpy as np
from PySide6.QtQuick3D import QQuick3DGeometry
from PySide6.QtCore import QByteArray
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "DirectGeometry"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class DirectTriangle(QQuick3DGeometry):
    """
    Ultra-simple direct triangle without any complex lifetime management
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        print("DirectTriangle.__init__")

        # Create geometry immediately and simply
        self.createSimpleTriangle()

    def createSimpleTriangle(self):
        """Create the simplest possible triangle"""
        print("DirectTriangle.createSimpleTriangle()")

        # Ultra-simple triangle: 3 vertices, position only
        vertices = np.array(
            [
                # Triangle in XY plane, facing camera
                -1.0,
                -1.0,
                0.0,  # vertex 1
                1.0,
                -1.0,
                0.0,  # vertex 2
                0.0,
                1.0,
                0.0,  # vertex 3
            ],
            dtype=np.float32,
        )

        print(f"Triangle: {len(vertices)} floats = {len(vertices)//3} vertices")

        # Clear first
        self.clear()

        # Set vertex data
        vertex_buffer = QByteArray(vertices.tobytes())
        self.setVertexData(vertex_buffer)

        # Stride: 3 floats * 4 bytes = 12 bytes per vertex
        self.setStride(12)

        # Only position attribute (no normals, no UVs)
        self.addAttribute(
            QQuick3DGeometry.Attribute.PositionSemantic,
            0,  # offset
            QQuick3DGeometry.Attribute.F32Type,
        )

        # Set primitive type
        self.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)

        # Set bounds
        from PySide6.QtGui import QVector3D

        self.setBounds(QVector3D(-1, -1, 0), QVector3D(1, 1, 0))

        # Update
        self.update()
        print("DirectTriangle: geometry updated")
