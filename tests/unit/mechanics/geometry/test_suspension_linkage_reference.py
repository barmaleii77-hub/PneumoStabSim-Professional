"""Geometry regression tests for the suspension linkage helper."""

import math

from src.mechanics.linkage_geometry import SuspensionLinkage


def test_reference_geometry_metrics(
    reference_suspension_linkage: SuspensionLinkage,
) -> None:
    """Validate lever metrics against the calibration spreadsheet values.

    The canonical linkage should yield a 0.30 m lever, with the rod joint placed
    5/6 along its length and a rod attachment distance of 0.25 m. These values
    are derived from the neutral chassis configuration and act as regression
    guards for mechanics calculations.
    """

    assert math.isclose(reference_suspension_linkage.lever_length, 0.3, rel_tol=1e-9)
    assert math.isclose(
        reference_suspension_linkage.rod_attach_distance, 0.25, rel_tol=1e-9
    )
    assert math.isclose(
        reference_suspension_linkage.rod_joint_fraction, 5.0 / 6.0, rel_tol=1e-9
    )
    assert reference_suspension_linkage.rod_joint_is_on_lever()


def test_reference_cylinder_envelope(
    reference_suspension_linkage: SuspensionLinkage,
) -> None:
    """Ensure cylinder lengths and amplitudes match analytical expectations.

    The nominal cylinder length must equal sqrt(0.34) m, the minimum rod length
    should stay positive, and the free-end amplitude should respect the
    0.30/0.2896 m stroke envelope determined during calibration.
    """

    expected_nominal = math.sqrt(0.34)
    assert math.isclose(
        reference_suspension_linkage.nominal_cylinder_length,
        expected_nominal,
        rel_tol=1e-9,
    )

    expected_minimum = max(
        0.0, expected_nominal - reference_suspension_linkage.cylinder_body_length
    )
    assert math.isclose(
        reference_suspension_linkage.minimum_rod_length,
        expected_minimum,
        rel_tol=1e-9,
    )

    negative, positive = reference_suspension_linkage.free_end_amplitude_limits()
    assert math.isclose(negative, -0.3, rel_tol=1e-9)
    assert math.isclose(positive, 0.28964316266516904, rel_tol=1e-9)
