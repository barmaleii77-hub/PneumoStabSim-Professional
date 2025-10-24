#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Property-based geometry approach - ensuring proper lifetime management
"""

import logging
import numpy as np
from PySide6.QtQuick3D import QQuick3DGeometry
from PySide6.QtCore import QByteArray, QObject, Property, Signal
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = "StableGeometry"
QML_IMPORT_MAJOR_VERSION = 1

_logger = logging.getLogger(__name__)


@QmlElement
class StableTriangleGeometry(QQuick3DGeometry):
    """
    Stable geometry with proper lifetime management
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        _logger.debug("StableTriangleGeometry.__init__: %s", self)
        self._initialized = False

        # Defer geometry creation until first paint
        self.componentComplete()

    def componentComplete(self):
        """Called when component is fully constructed"""
        _logger.debug("StableTriangleGeometry.componentComplete() called")
        if not self._initialized:
            self._initialized = True
            self.rebuildGeometry()

    def rebuildGeometry(self):
        """Build geometry with guaranteed lifetime"""
        _logger.debug(
            "StableTriangleGeometry.rebuildGeometry() - creating stable geometry"
        )

        # Create very simple triangle - large and obvious
        vertices = np.array(
            [
                # Large triangle, centered at origin
                # Bottom-left
                -2.0,
                -2.0,
                0.0,  # position
                0.0,
                0.0,
                1.0,  # normal (towards camera)
                # Bottom-right
                2.0,
                -2.0,
                0.0,  # position
                0.0,
                0.0,
                1.0,  # normal
                # Top-center
                0.0,
                2.0,
                0.0,  # position
                0.0,
                0.0,
                1.0,  # normal
            ],
            dtype=np.float32,
        )

        _logger.debug(
            "Stable vertices: %d floats = %d vertices",
            len(vertices),
            len(vertices) // 6,
        )

        # Store data as instance variables to prevent garbage collection
        self._vertex_data = QByteArray(vertices.tobytes())

        # Clear and rebuild completely
        self.clear()

        # Set data
        self.setVertexData(self._vertex_data)
        self.setStride(6 * 4)  # 6 floats * 4 bytes

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

        # Set type
        self.setPrimitiveType(QQuick3DGeometry.PrimitiveType.Triangles)

        # Set large bounds to ensure visibility
        from PySide6.QtGui import QVector3D

        self.setBounds(QVector3D(-2, -2, 0), QVector3D(2, 2, 0))

        _logger.debug("StableTriangleGeometry.rebuildGeometry() - calling update()")
        self.update()

        _logger.debug("StableTriangleGeometry.rebuildGeometry() - completed")


@QmlElement
class GeometryProvider(QObject):
    """
    Provider that manages geometry lifetime
    """

    geometryChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        _logger.debug("GeometryProvider.__init__: %s", self)
        self._geometry = StableTriangleGeometry(self)

    @Property(QQuick3DGeometry, notify=geometryChanged)
    def geometry(self):
        _logger.debug("GeometryProvider.geometry getter called: %s", self._geometry)
        return self._geometry
