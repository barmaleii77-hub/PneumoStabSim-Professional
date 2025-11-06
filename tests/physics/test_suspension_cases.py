"""Regression tests for physics suspension scenarios."""

from __future__ import annotations

import pytest

from src.physics import forces
from src.tools.reporting import evaluate_physics_case, summarise_assertions


@pytest.mark.parametrize(
    "case_identifier",
    (
        "standard-suspension-balance",
        "limit-pressure-envelope",
        "full-droop-asymmetric",
    ),
)
def test_suspension_cases(physics_case_loader, case_identifier):
    """Validate forces and invariants for representative suspension cases."""

    case = physics_case_loader(case_identifier)
    evaluation = evaluate_physics_case(case)
    results = summarise_assertions(case, evaluation)

    for outcome in results:
        if isinstance(outcome.actual, dict):
            for key, value in outcome.expected.items():
                assert outcome.actual[key] == pytest.approx(
                    float(value), abs=outcome.tolerance
                )
        else:
            assert outcome.actual == pytest.approx(
                float(outcome.expected), abs=outcome.tolerance
            )
        assert outcome.passed

    vertical_forces = evaluation["raw_vertical_array"]
    tau_x = evaluation["moments"]["tau_x"]
    tau_z = evaluation["moments"]["tau_z"]

    is_valid, reason = forces.validate_force_calculation(
        vertical_forces, (tau_x, tau_z)
    )
    assert is_valid, reason
