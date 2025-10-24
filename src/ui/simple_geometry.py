#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple sphere without indices - direct triangle vertices
"""

import numpy as np
from PySide6.QtQuick3D import QQuick3DGeometry
from PySide6.QtCore import QByteArray
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "SimpleGeometry"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class SimpleSphere(QQuick3DGeometry):
    """
    Simple sphere without indices - direct triangles
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._radius = 1.0
        self.generate()

    def generate(self):
        """Generate sphere using direct triangles (no indices)"""
        r = self._radius
        segments = 16  # Reduced for simplicity
        rings = 8

        vertices = []

        # Generate triangles directly
        for lat in range(rings):
            for lon in range(segments):
                # Current quad corners
                theta1 = lat * np.pi / rings
                theta2 = (lat + 1) * np.pi / rings
                phi1 = lon * 2 * np.pi / segments
                phi2 = (lon + 1) * 2 * np.pi / segments

                # Four corners of quad
                def sphere_point(theta, phi):
                    x = r * np.sin(theta) * np.cos(phi)
                    y = r * np.cos(theta)
                    z = r * np.sin(theta) * np.sin(phi)
                    return [x, y, z]

                p1 = sphere_point(theta1, phi1)  # Top-left
                p2 = sphere_point(theta1, phi2)  # Top-right
                p3 = sphere_point(theta2, phi1)  # Bottom-left
                p4 = sphere_point(theta2, phi2)  # Bottom-right

                # Triangle 1: p1, p3, p2
                vertices.extend(p1)
                vertices.extend(p3)
                vertices.extend(p2)

                # Triangle 2: p2, p3, p4
                vertices.extend(p2)
                vertices.extend(p3)
                vertices.extend(p4)

        # Convert to numpy array
        vertex_data = np.array(vertices, dtype=np.float32)

        print(
            f"SimpleSphere: Generated {len(vertices) // 3} vertices, {len(vertices)} floats"
        )

        # Clear and set data
        self.clear()

        # Set vertex data
        self.setVertexData(QByteArray(vertex_data.tobytes()))

        # Set stride (3 floats per vertex: x, y, z only)
        self.setStride(12)  # 3 floats * 4 bytes

        # Add position attribute only
        self.addAttribute(
            QQuick3DGeometry.Attribute.PositionSemantic,
            0,
            QQuick3DGeometry.Attribute.F32Type,
        )

        # Set primitive type
        self.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)

        # Set bounds
        from PySide6.QtGui import QVector3D

        self.setBounds(QVector3D(-r, -r, -r), QVector3D(r, r, r))

        # Update
        self.update()
        print("SimpleSphere: Geometry updated")
