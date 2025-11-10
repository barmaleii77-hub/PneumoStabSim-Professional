"""Unit tests for :mod:`src.pneumo.geometry` lever helpers."""

from __future__ import annotations

import math

import pytest

from src.pneumo.geometry import CylinderGeom, LeverGeom


@pytest.fixture()
def lever_geom() -> LeverGeom:
    return LeverGeom(L_lever=0.75, rod_joint_frac=0.45, d_frame_to_lever_hinge=0.42)


@pytest.fixture()
def cylinder_geom() -> CylinderGeom:
    return CylinderGeom(
        D_in_front=0.11,
        D_in_rear=0.11,
        D_out_front=0.13,
        D_out_rear=0.13,
        L_inner=0.46,
        t_piston=0.025,
        D_rod=0.035,
        link_rod_diameters_front_rear=True,
        L_dead_head=0.018,
        L_dead_rod=0.02,
        residual_frac_min=0.01,
        Y_tail=0.45,
        Z_axle=0.55,
    )


def test_blend_between_simple_and_axis_projection(
    lever_geom: LeverGeom, cylinder_geom: CylinderGeom
) -> None:
    """The axial component should be computed from the Euclidean length."""

    lever_geom.attach_cylinder_geometry(cylinder_geom)
    angle = math.radians(12.0)

    lever_arm = lever_geom.rod_joint_frac * lever_geom.L_lever
    simple = lever_arm * math.sin(angle)

    rod_x, rod_y = lever_geom.rod_joint_pos(angle)
    tail_point = (0.0, cylinder_geom.Y_tail, cylinder_geom.Z_axle)
    joint_point = (0.0, rod_x, cylinder_geom.Z_axle + rod_y)

    dx = joint_point[0] - tail_point[0]
    dy = joint_point[1] - tail_point[1]
    dz = joint_point[2] - tail_point[2]
    axis_len = math.sqrt(dx * dx + dy * dy + dz * dz)

    assert lever_geom._neutral_length is not None  # noqa: SLF001
    neutral = lever_geom._neutral_length  # noqa: SLF001
    displacement_axis = axis_len - neutral
    signed_axis = math.copysign(abs(displacement_axis), angle)

    blend = lever_geom._displacement_blend  # noqa: SLF001
    assert blend is not None

    expected = blend * simple + (1.0 - blend) * signed_axis
    actual = lever_geom.angle_to_displacement(angle)

    assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)
