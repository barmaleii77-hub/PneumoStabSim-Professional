#!/usr/bin/env python
"""
Qt Quick 3D Custom Geometry - Following Qt Documentation Exactly
Based on official Qt documentation and examples
"""

import numpy as np
from PySide6.QtQuick3D import QQuick3DGeometry
from PySide6.QtCore import QByteArray, QObject, Property
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "GeometryExample"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class ExampleTriangleGeometry(QQuick3DGeometry):
    """
    Example triangle following Qt documentation exactly
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.updateData()

        # Connect to internal signals
        self.geometryNodeDirty.connect(self.updateData)

    def updateData(self):
        """Update geometry data - called by Qt when needed"""
        print("ExampleTriangleGeometry.updateData() called")

        # Clear existing data
        self.clear()

        # Define triangle vertices exactly as in Qt examples
        # Format: position(xyz) + normal(xyz)
        vertices = np.array(
            [
                # Triangle vertices (counter-clockwise)
                # Bottom-left
                -1.0,
                -1.0,
                0.0,  # position
                0.0,
                0.0,
                1.0,  # normal (pointing towards camera)
                # Bottom-right
                1.0,
                -1.0,
                0.0,  # position
                0.0,
                0.0,
                1.0,  # normal
                # Top-center
                0.0,
                1.0,
                0.0,  # position
                0.0,
                0.0,
                1.0,  # normal
            ],
            dtype=np.float32,
        )

        print(
            f"Triangle vertices: {len(vertices)} floats, {len(vertices) // 6} vertices"
        )

        # Set vertex data
        self.setVertexData(QByteArray(vertices.tobytes()))

        # Set stride: 6 floats per vertex (3 pos + 3 normal) * 4 bytes
        self.setStride(6 * 4)

        # Add position attribute at offset 0
        self.addAttribute(
            QQuick3DGeometry.Attribute.PositionSemantic,
            0,  # offset
            QQuick3DGeometry.Attribute.F32Type,
        )

        # Add normal attribute at offset 12 (3 floats * 4 bytes)
        self.addAttribute(
            QQuick3DGeometry.Attribute.NormalSemantic,
            12,  # offset
            QQuick3DGeometry.Attribute.F32Type,
        )

        # Set primitive type
        self.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)

        # Set bounds
        from PySide6.QtGui import QVector3D

        self.setBounds(QVector3D(-1, -1, 0), QVector3D(1, 1, 0))

        print("ExampleTriangleGeometry.updateData() completed")


@QmlElement
class ExampleGeometryModel(QObject):
    """
    Model class that manages geometry - following Qt patterns
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._geometry = ExampleTriangleGeometry()

    @Property(QObject, constant=True)
    def geometry(self):
        return self._geometry
