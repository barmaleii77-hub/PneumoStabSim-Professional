import math

from src.mechanics.linkage_geometry import SuspensionLinkage


def build_reference_linkage() -> SuspensionLinkage:
    return SuspensionLinkage.from_mm(
        pivot=(200.0, 0.0),
        free_end=(500.0, 0.0),
        rod_joint=(450.0, 0.0),
        cylinder_tail=(150.0, 500.0),
        cylinder_body_length=300.0,
    )


def test_basic_geometry_relationships() -> None:
    linkage = build_reference_linkage()

    assert math.isclose(linkage.lever_length, 0.3, rel_tol=1e-9)
    assert math.isclose(linkage.rod_attach_distance, 0.25, rel_tol=1e-9)
    assert math.isclose(linkage.rod_joint_fraction, 5.0 / 6.0, rel_tol=1e-9)
    assert linkage.rod_joint_is_on_lever()


def test_cylinder_lengths() -> None:
    linkage = build_reference_linkage()

    expected_nominal = math.sqrt(0.34)
    assert math.isclose(linkage.nominal_cylinder_length, expected_nominal, rel_tol=1e-9)

    expected_min_rod = max(0.0, expected_nominal - 0.3)
    assert math.isclose(linkage.minimum_rod_length, expected_min_rod, rel_tol=1e-9)


def test_amplitude_limits_respect_cylinder_travel() -> None:
    linkage = build_reference_linkage()

    neg_amp, pos_amp = linkage.free_end_amplitude_limits()

    assert math.isclose(neg_amp, -0.3, rel_tol=1e-9)
    assert math.isclose(pos_amp, 0.28964316266516904, rel_tol=1e-9)

    base_length = linkage.nominal_cylinder_length
    pos_angle = linkage.max_angle_for_stroke_limit(1)
    neg_angle = linkage.max_angle_for_stroke_limit(-1)

    assert math.isclose(
        abs(linkage.cylinder_length_at_angle(pos_angle) - base_length),
        linkage.cylinder_body_length,
        rel_tol=1e-9,
    )
    assert (
        abs(linkage.cylinder_length_at_angle(neg_angle) - base_length)
        <= linkage.cylinder_body_length
    )
