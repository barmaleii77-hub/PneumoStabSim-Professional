#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Custom 3D Sphere Geometry for Qt Quick 3D
Generates procedural sphere mesh
"""

import numpy as np
from PySide6.QtQuick3D import QQuick3DGeometry
from PySide6.QtCore import QByteArray, Property
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
class ProceduralCylinderGeometry(QQuick3DGeometry):
    """Procedural cylinder mesh with adjustable tesselation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._segments = 32
        self._rings = 1
        self._vertex_count = 0
        self._index_count = 0
        self._radius = 1.0
        self._length = 2.0

        self.updateData()
        self.geometryNodeDirty.connect(self.updateData)

    @Property(int)
    def segments(self) -> int:
        return self._segments

    @segments.setter
    def segments(self, value: int) -> None:
        coerced = max(3, int(value))
        if coerced != self._segments:
            self._segments = coerced
            self.updateData()

    @Property(int)
    def rings(self) -> int:
        return self._rings

    @rings.setter
    def rings(self, value: int) -> None:
        coerced = max(1, int(value))
        if coerced != self._rings:
            self._rings = coerced
            self.updateData()

    @property
    def vertex_count(self) -> int:
        return self._vertex_count

    @property
    def index_count(self) -> int:
        return self._index_count

    @Property(float)
    def radius(self) -> float:
        return self._radius

    @radius.setter
    def radius(self, value: float) -> None:
        coerced = max(1e-5, float(value))
        if coerced != self._radius:
            self._radius = coerced
            self.updateData()

    @Property(float)
    def length(self) -> float:
        return self._length

    @length.setter
    def length(self, value: float) -> None:
        coerced = max(1e-5, float(value))
        if coerced != self._length:
            self._length = coerced
            self.updateData()

    def updateData(self) -> None:  # noqa: C901 - geometry generation requires loops
        print("ProceduralCylinderGeometry.updateData() called")

        self.clear()

        segments = max(3, int(self._segments))
        rings = max(1, int(self._rings))
        radius = max(1e-5, float(self._radius))
        half_length = max(1e-5, float(self._length) / 2.0)

        two_pi = 2.0 * np.pi
        angles = np.linspace(0.0, two_pi, segments + 1, dtype=np.float32)
        cos_angles = np.cos(angles)
        sin_angles = np.sin(angles)
        ring_positions = np.linspace(-1.0, 1.0, rings + 1, dtype=np.float32)

        side_positions = []
        side_normals = []
        side_uvs = []

        for ring_index, y in enumerate(ring_positions):
            v_coord = ring_index / rings
            for seg_index in range(segments + 1):
                x_unit = cos_angles[seg_index]
                z_unit = sin_angles[seg_index]
                x = x_unit * radius
                z = z_unit * radius
                y_pos = y * half_length
                u_coord = seg_index / segments
                side_positions.append([x, y_pos, z])
                side_normals.append([x_unit, 0.0, z_unit])
                side_uvs.append([u_coord, v_coord])

        side_positions = np.array(side_positions, dtype=np.float32)
        side_normals = np.array(side_normals, dtype=np.float32)
        side_uvs = np.array(side_uvs, dtype=np.float32)

        indices: list[int] = []
        stride = segments + 1
        for ring_index in range(rings):
            ring_start = ring_index * stride
            next_ring_start = (ring_index + 1) * stride
            for seg_index in range(segments):
                top_left = ring_start + seg_index
                top_right = ring_start + seg_index + 1
                bottom_left = next_ring_start + seg_index
                bottom_right = next_ring_start + seg_index + 1
                indices.extend((top_left, bottom_left, top_right))
                indices.extend((top_right, bottom_left, bottom_right))

        top_center = np.array([[0.0, half_length, 0.0]], dtype=np.float32)
        bottom_center = np.array([[0.0, -half_length, 0.0]], dtype=np.float32)

        top_ring_positions = []
        bottom_ring_positions = []
        top_ring_normals = []
        bottom_ring_normals = []
        top_ring_uvs = []
        bottom_ring_uvs = []

        for seg_index in range(segments):
            angle = two_pi * seg_index / segments
            cos_val = np.cos(angle)
            sin_val = np.sin(angle)
            top_ring_positions.append([cos_val * radius, half_length, sin_val * radius])
            bottom_ring_positions.append(
                [cos_val * radius, -half_length, sin_val * radius]
            )
            top_ring_normals.append([0.0, 1.0, 0.0])
            bottom_ring_normals.append([0.0, -1.0, 0.0])
            u = 0.5 + cos_val * 0.5
            v = 0.5 - sin_val * 0.5
            top_ring_uvs.append([u, v])
            bottom_ring_uvs.append([u, 1.0 - v])

        top_ring_positions = np.array(top_ring_positions, dtype=np.float32)
        bottom_ring_positions = np.array(bottom_ring_positions, dtype=np.float32)
        top_ring_normals = np.array(top_ring_normals, dtype=np.float32)
        bottom_ring_normals = np.array(bottom_ring_normals, dtype=np.float32)
        top_ring_uvs = np.array(top_ring_uvs, dtype=np.float32)
        bottom_ring_uvs = np.array(bottom_ring_uvs, dtype=np.float32)

        positions = np.concatenate(
            (
                side_positions,
                top_center,
                top_ring_positions,
                bottom_center,
                bottom_ring_positions,
            ),
            axis=0,
        )
        normals = np.concatenate(
            (
                side_normals,
                np.array([[0.0, 1.0, 0.0]], dtype=np.float32),
                top_ring_normals,
                np.array([[0.0, -1.0, 0.0]], dtype=np.float32),
                bottom_ring_normals,
            ),
            axis=0,
        )
        uvs = np.concatenate(
            (
                side_uvs,
                np.array([[0.5, 0.0]], dtype=np.float32),
                top_ring_uvs,
                np.array([[0.5, 1.0]], dtype=np.float32),
                bottom_ring_uvs,
            ),
            axis=0,
        )

        top_center_index = side_positions.shape[0]
        top_ring_start = top_center_index + 1
        bottom_center_index = top_ring_start + top_ring_positions.shape[0]
        bottom_ring_start = bottom_center_index + 1

        for seg_index in range(segments):
            current = top_ring_start + seg_index
            next_index = top_ring_start + ((seg_index + 1) % segments)
            indices.extend((top_center_index, current, next_index))

        for seg_index in range(segments):
            current = bottom_ring_start + seg_index
            next_index = bottom_ring_start + ((seg_index + 1) % segments)
            indices.extend((bottom_center_index, next_index, current))

        normals = np.array(normals, dtype=np.float32)
        uvs = np.array(uvs, dtype=np.float32)

        vertex_data = np.hstack((positions, normals, uvs)).astype(np.float32)
        index_data = np.array(indices, dtype=np.uint32)

        self._vertex_count = vertex_data.shape[0]
        self._index_count = index_data.shape[0]

        self.setVertexData(QByteArray(vertex_data.tobytes()))
        self.setIndexData(QByteArray(index_data.tobytes()))
        self.setStride(8 * 4)

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
            QQuick3DGeometry.Attribute.TexCoordSemantic,
            24,
            QQuick3DGeometry.Attribute.F32Type,
        )  # Qt defaults texcoord component count to 2 for this semantic

        self.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)

        from PySide6.QtGui import QVector3D

        self.setBounds(
            QVector3D(-radius, -half_length, -radius),
            QVector3D(radius, half_length, radius),
        )

        print("ProceduralCylinderGeometry.updateData() completed")


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
