#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ultra simple triangle geometry - if this doesn't work, nothing will
"""
import numpy as np
from PySide6.QtQuick3D import QQuick3DGeometry
from PySide6.QtCore import QByteArray
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "TestGeometry"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class SimpleTriangle(QQuick3DGeometry):
    """
    Single triangle - simplest possible geometry
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.generate()

    def generate(self):
        """Generate single triangle"""
        # Single triangle vertices
        # Format: [x, y, z, nx, ny, nz, u, v] per vertex
        vertices = np.array(
            [
                # Triangle pointing up
                # Vertex 1 (bottom-left)
                -1.0,
                -1.0,
                0.0,  # position
                0.0,
                0.0,
                1.0,  # normal (pointing toward camera)
                0.0,
                0.0,  # uv
                # Vertex 2 (bottom-right)
                1.0,
                -1.0,
                0.0,  # position
                0.0,
                0.0,
                1.0,  # normal
                1.0,
                0.0,  # uv
                # Vertex 3 (top-center)
                0.0,
                1.0,
                0.0,  # position
                0.0,
                0.0,
                1.0,  # normal
                0.5,
                1.0,  # uv
            ],
            dtype=np.float32,
        )

        print(f"SimpleTriangle: Generated {len(vertices)//8} vertices")

        # Clear and set data
        self.clear()
        self.setVertexData(QByteArray(vertices.tobytes()))
        self.setStride(32)  # 8 floats * 4 bytes

        # Add attributes
        self.addAttribute(
            QQuick3DGeometry.Attribute.PositionSemantic,
            0,
            QQuick3DGeometry.Attribute.F32Type,
        )
        self.addAttribute(
            QQuick3DGeometry.Attribute.NormalSemantic,
            12,
            QQuick3DGeometry.Attribute.F32Type,
        )
        self.addAttribute(
            QQuick3DGeometry.Attribute.TexCoord0Semantic,
            24,
            QQuick3DGeometry.Attribute.F32Type,
        )

        self.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)

        from PySide6.QtGui import QVector3D

        self.setBounds(QVector3D(-1, -1, 0), QVector3D(1, 1, 0))

        self.update()
        print("SimpleTriangle: Updated")
