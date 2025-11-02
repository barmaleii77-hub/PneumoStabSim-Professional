from __future__ import annotations

import pytest

pytest.importorskip(
    "PySide6.QtQuick3D",
    reason="PySide6 QtQuick3D module is required for procedural geometry tests",
    exc_type=ImportError,
)

from src.ui.custom_geometry import ProceduralCylinderGeometry


def test_procedural_cylinder_geometry_vertex_counts(qtbot) -> None:
    geometry = ProceduralCylinderGeometry()

    base_vertex_count = geometry.vertex_count
    base_index_count = geometry.index_count
    stride = geometry.stride()

    assert base_vertex_count > 0
    assert base_index_count > 0
    assert geometry.vertexData().size() == base_vertex_count * stride

    geometry.segments = 48
    geometry.rings = 3
    qtbot.wait(0)

    assert geometry.vertex_count > base_vertex_count
    assert geometry.index_count > base_index_count
    assert geometry.index_count % 3 == 0
