"""Regression coverage for :mod:`src.pneumo.geometry` lever helpers."""

from __future__ import annotations

import math

import pytest

from src.pneumo.geometry import CylinderGeom, LeverGeom


@pytest.fixture()
def lever_geom() -> LeverGeom:
    return LeverGeom(L_lever=0.75, rod_joint_frac=0.45, d_frame_to_lever_hinge=0.42)


def _example_cylinder() -> CylinderGeom:
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


def test_displacement_to_angle_roundtrip_without_cylinder(lever_geom: LeverGeom) -> None:
    """The analytical inverse should behave like ``asin`` for the simple model."""

    angles = [
        0.0,
        math.radians(4.0),
        -math.radians(7.5),
        math.radians(18.0),
        -math.radians(25.0),
    ]

    for angle in angles:
        displacement = lever_geom.angle_to_displacement(angle)
        solved = lever_geom.displacement_to_angle(displacement)
        assert math.isclose(solved, angle, rel_tol=1e-7, abs_tol=1e-7)


def test_displacement_to_angle_handles_attached_cylinder(lever_geom: LeverGeom) -> None:
    """When a cylinder is attached the blended solver should still converge."""

    lever_geom.attach_cylinder_geometry(_example_cylinder())

    test_angles = [math.radians(value) for value in (-15.0, -6.0, 0.0, 8.0, 22.0)]
    for angle in test_angles:
        displacement = lever_geom.angle_to_displacement(angle)
        solved = lever_geom.displacement_to_angle(displacement)
        assert math.isclose(solved, angle, rel_tol=1e-6, abs_tol=1e-6)


def test_displacement_to_angle_respects_initial_guess(lever_geom: LeverGeom) -> None:
    """Custom initial guesses should be honoured to speed up convergence."""

    target_angle = math.radians(12.0)
    displacement = lever_geom.angle_to_displacement(target_angle)

    poor_guess = math.radians(-45.0)
    refined = lever_geom.displacement_to_angle(displacement, initial_guess=poor_guess)
    assert math.isclose(refined, target_angle, rel_tol=1e-6, abs_tol=1e-6)
