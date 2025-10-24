#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CORRECT QQuick3DGeometry implementation based on DOCUMENTATION STUDY
Using EXACT API discovered from documentation analysis
"""

import numpy as np
from PySide6.QtQuick3D import QQuick3DGeometry
from PySide6.QtCore import QByteArray
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "CorrectGeometry"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class DocumentationBasedTriangle(QQuick3DGeometry):
    """
    Triangle geometry following EXACT documentation patterns discovered
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        print("DocumentationBasedTriangle: Creating with EXACT API usage")

        # Build geometry immediately using documented approach
        self.buildGeometryFromDocumentation()

    def buildGeometryFromDocumentation(self):
        """Build geometry using EXACT API patterns from documentation study"""
        print("DocumentationBasedTriangle: Building with documented API")

        # Simple triangle - position only first
        vertices = np.array(
            [
                # Large triangle for visibility
                -2.0,
                -2.0,
                0.0,  # vertex 1
                2.0,
                -2.0,
                0.0,  # vertex 2
                0.0,
                2.0,
                0.0,  # vertex 3
            ],
            dtype=np.float32,
        )

        print(
            f"Triangle vertices: {len(vertices)} floats = {len(vertices) // 3} vertices"
        )

        # Step 1: Clear (as per API study)
        self.clear()
        print("  1. clear() called")

        # Step 2: Set vertex data
        vertex_buffer = QByteArray(vertices.tobytes())
        self.setVertexData(vertex_buffer)
        print(f"  2. setVertexData() called with {len(vertex_buffer)} bytes")

        # Step 3: Set stride (3 floats * 4 bytes = 12 bytes per vertex)
        self.setStride(12)
        print("  3. setStride(12) called")

        # Step 4: Add attributes using EXACT semantic names from documentation
        self.addAttribute(
            QQuick3DGeometry.Attribute.Semantic.PositionSemantic,  # EXACT from docs
            0,  # offset
            QQuick3DGeometry.Attribute.ComponentType.F32Type,  # EXACT from docs
        )
        print("  4. addAttribute(PositionSemantic, 0, F32Type) called")

        # Step 5: Set primitive type using EXACT enum from documentation
        self.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)
        print("  5. setPrimitiveType(Triangles) called")

        # Step 6: Set bounds using proper Qt types
        from PySide6.QtGui import QVector3D

        self.setBounds(QVector3D(-2, -2, 0), QVector3D(2, 2, 0))
        print("  6. setBounds() called")

        # Verify final state
        print("Final state:")
        print(f"  - attributeCount(): {self.attributeCount()}")
        print(f"  - stride(): {self.stride()}")
        print(f"  - primitiveType(): {self.primitiveType()}")
        print(f"  - vertexData(): {len(self.vertexData())} bytes")
        print(f"  - indexData(): {len(self.indexData())} bytes")

        print("DocumentationBasedTriangle: Geometry complete")
