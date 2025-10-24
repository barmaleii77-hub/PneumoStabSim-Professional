#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Custom 3D Sphere Geometry for Qt Quick 3D
Generates procedural sphere mesh
"""

import numpy as np
from PySide6.QtQuick3D import QQuick3DGeometry
from PySide6.QtCore import QByteArray
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "CustomGeometry"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class SphereGeometry(QQuick3DGeometry):
    """
    Procedural sphere geometry using WORKING PATTERN from ExampleTriangleGeometry
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._radius = 1.0
        self._segments = 16  # Reduced for stability
        self._rings = 8  # Reduced for stability

        # Use WORKING PATTERN: call updateData() and connect signal
        self.updateData()
        self.geometryNodeDirty.connect(self.updateData)

    def setRadius(self, radius: float):
        """Set sphere radius"""
        self._radius = radius
        self.updateData()  # Use updateData instead of generate

    def setSegments(self, segments: int):
        """Set number of longitudinal segments"""
        self._segments = max(8, segments)
        self.updateData()

    def setRings(self, rings: int):
        """Set number of latitudinal rings"""
        self._rings = max(4, rings)
        self.updateData()

    def updateData(self):
        """Update geometry data - WORKING PATTERN from ExampleTriangleGeometry"""
        print("SphereGeometry.updateData() called")

        # Clear first - CRITICAL
        self.clear()

        r = self._radius
        segs = self._segments
        rings = self._rings

        vertices = []

        # Generate triangles directly (no indices) - WORKING PATTERN
        for lat in range(rings):
            for lon in range(segs):
                theta1 = lat * np.pi / rings
                theta2 = (lat + 1) * np.pi / rings
                phi1 = lon * 2 * np.pi / segs
                phi2 = (lon + 1) * 2 * np.pi / segs

                def sphere_vertex(theta, phi):
                    sin_theta = np.sin(theta)
                    cos_theta = np.cos(theta)
                    sin_phi = np.sin(phi)
                    cos_phi = np.cos(phi)

                    # Position
                    x = r * sin_theta * cos_phi
                    y = r * cos_theta
                    z = r * sin_theta * sin_phi

                    # Normal (same as normalized position for sphere)
                    nx = sin_theta * cos_phi
                    ny = cos_theta
                    nz = sin_theta * sin_phi

                    return [x, y, z, nx, ny, nz]  # Position + Normal (6 floats)

                # Four corners of quad
                v1 = sphere_vertex(theta1, phi1)
                v2 = sphere_vertex(theta1, phi2)
                v3 = sphere_vertex(theta2, phi1)
                v4 = sphere_vertex(theta2, phi2)

                # Triangle 1: v1, v3, v2 (counter-clockwise)
                vertices.extend(v1)
                vertices.extend(v3)
                vertices.extend(v2)

                # Triangle 2: v2, v3, v4 (counter-clockwise)
                vertices.extend(v2)
                vertices.extend(v3)
                vertices.extend(v4)

        # Convert to numpy - WORKING PATTERN
        vertex_data = np.array(vertices, dtype=np.float32)
        print(f"Sphere vertices: {len(vertices)} floats, {len(vertices) // 6} vertices")

        # Set vertex data - WORKING PATTERN
        self.setVertexData(QByteArray(vertex_data.tobytes()))

        # Set stride: 6 floats per vertex (3 pos + 3 normal) * 4 bytes - WORKING PATTERN
        self.setStride(6 * 4)

        # Add attributes - WORKING PATTERN (Position + Normal)
        self.addAttribute(
            QQuick3DGeometry.Attribute.PositionSemantic,
            0,  # offset
            QQuick3DGeometry.Attribute.F32Type,
        )

        self.addAttribute(
            QQuick3DGeometry.Attribute.NormalSemantic,
            12,  # offset (3 floats * 4 bytes)
            QQuick3DGeometry.Attribute.F32Type,
        )

        # Set primitive type - WORKING PATTERN
        self.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)

        # Set bounds - WORKING PATTERN
        from PySide6.QtGui import QVector3D

        self.setBounds(QVector3D(-r, -r, -r), QVector3D(r, r, r))

        print("SphereGeometry.updateData() completed")


@QmlElement
class CubeGeometry(QQuick3DGeometry):
    """
    Procedural cube geometry
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._size = 1.0
        self.generate()

    def setSize(self, size: float):
        """Set cube size"""
        self._size = size
        self.generate()

    def generate(self):
        """Generate cube geometry"""
        s = self._size / 2  # half-size

        # 24 vertices (4 per face, 6 faces)
        # Each face has its own vertices for proper normals
        vertices = np.array(
            [
                # Front face (z+)
                -s,
                -s,
                s,
                s,
                -s,
                s,
                s,
                s,
                s,
                -s,
                s,
                s,
                # Back face (z-)
                s,
                -s,
                -s,
                -s,
                -s,
                -s,
                -s,
                s,
                -s,
                s,
                s,
                -s,
                # Top face (y+)
                -s,
                s,
                s,
                s,
                s,
                s,
                s,
                s,
                -s,
                -s,
                s,
                -s,
                # Bottom face (y-)
                -s,
                -s,
                -s,
                s,
                -s,
                -s,
                s,
                -s,
                s,
                -s,
                -s,
                s,
                # Right face (x+)
                s,
                -s,
                s,
                s,
                -s,
                -s,
                s,
                s,
                -s,
                s,
                s,
                s,
                # Left face (x-)
                -s,
                -s,
                -s,
                -s,
                -s,
                s,
                -s,
                s,
                s,
                -s,
                s,
                -s,
            ],
            dtype=np.float32,
        )

        # Normals (one per face)
        normals = np.array(
            [
                # Front
                0,
                0,
                1,
                0,
                0,
                1,
                0,
                0,
                1,
                0,
                0,
                1,
                # Back
                0,
                0,
                -1,
                0,
                0,
                -1,
                0,
                0,
                -1,
                0,
                0,
                -1,
                # Top
                0,
                1,
                0,
                0,
                1,
                0,
                0,
                1,
                0,
                0,
                1,
                0,
                # Bottom
                0,
                -1,
                0,
                0,
                -1,
                0,
                0,
                -1,
                0,
                0,
                -1,
                0,
                # Right
                1,
                0,
                0,
                1,
                0,
                0,
                1,
                0,
                0,
                1,
                0,
                0,
                # Left
                -1,
                0,
                0,
                -1,
                0,
                0,
                -1,
                0,
                0,
                -1,
                0,
                0,
            ],
            dtype=np.float32,
        )

        # UVs
        uvs = np.array(
            [
                0,
                0,
                1,
                0,
                1,
                1,
                0,
                1,  # Front
                0,
                0,
                1,
                0,
                1,
                1,
                0,
                1,  # Back
                0,
                0,
                1,
                0,
                1,
                1,
                0,
                1,  # Top
                0,
                0,
                1,
                0,
                1,
                1,
                0,
                1,  # Bottom
                0,
                0,
                1,
                0,
                1,
                1,
                0,
                1,  # Right
                0,
                0,
                1,
                0,
                1,
                1,
                0,
                1,  # Left
            ],
            dtype=np.float32,
        )

        # Indices (2 triangles per face)
        indices = np.array(
            [
                0,
                1,
                2,
                0,
                2,
                3,  # Front
                4,
                5,
                6,
                4,
                6,
                7,  # Back
                8,
                9,
                10,
                8,
                10,
                11,  # Top
                12,
                13,
                14,
                12,
                14,
                15,  # Bottom
                16,
                17,
                18,
                16,
                18,
                19,  # Right
                20,
                21,
                22,
                20,
                22,
                23,  # Left
            ],
            dtype=np.uint32,
        )

        # Interleave
        interleaved = []
        for i in range(24):
            interleaved.extend(vertices[i * 3 : i * 3 + 3])
            interleaved.extend(normals[i * 3 : i * 3 + 3])
            interleaved.extend(uvs[i * 2 : i * 2 + 2])

        interleaved_data = np.array(interleaved, dtype=np.float32)

        # Clear attributes BEFORE setting data
        self.clear()

        # Set data AFTER clearing
        self.setVertexData(QByteArray(interleaved_data.tobytes()))
        self.setIndexData(
            QByteArray(indices.tobytes())
        )  # ? FIX: use 'indices', not 'index_data'
        self.setStride(32)

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

        # Index attribute for triangle indices
        self.addAttribute(
            QQuick3DGeometry.Attribute.IndexSemantic,
            0,
            QQuick3DGeometry.Attribute.U32Type,
        )

        self.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)

        from PySide6.QtGui import QVector3D

        self.setBounds(QVector3D(-s, -s, -s), QVector3D(s, s, s))
        self.update()
