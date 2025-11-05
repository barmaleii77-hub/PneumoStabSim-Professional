"""Physics evaluation helpers shared between tests and CLI tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping

import numpy as np

from src.physics import forces


def _as_tuple(values: Iterable[float]) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


def evaluate_physics_case(case: Any) -> dict[str, Any]:
    """Compute derived quantities for a physics test case."""

    scene = case.scene
    attachment_points = {
        name: tuple(_as_tuple(coords))[:2] for name, coords in scene.attachment_points.items()
    }
    state_name = next(iter(scene.state_vectors))
    state = np.asarray(scene.state_vectors[state_name], dtype=float)
    axis = scene.axis_directions

    kinematics: Dict[str, dict[str, Any]] = {}
    for wheel in attachment_points:
        kinematics[wheel] = forces.compute_suspension_point_kinematics(
            wheel, state, attachment_points, axis
        )

    pneumatic = scene.pneumatic

    cylinder_forces = {
        wheel: forces.compute_cylinder_force(
            payload["head"],
            payload["rod"],
            forces.DEFAULT_SUSPENSION_PARAMS["A_head"],
            forces.DEFAULT_SUSPENSION_PARAMS["A_rod"],
        )
        for wheel, payload in pneumatic["pressures"].items()
    }

    spring_forces = {
        wheel: forces.compute_spring_force(
            payload["current"],
            payload["rest"],
            forces.DEFAULT_SUSPENSION_PARAMS["k_spring"],
        )
        for wheel, payload in pneumatic["springs"].items()
    }

    damper_forces = {
        wheel: forces.compute_damper_force(
            kinematics[wheel]["axial_velocity"],
            forces.DEFAULT_SUSPENSION_PARAMS["c_damper"],
            forces.DEFAULT_SUSPENSION_PARAMS["F_damper_min"],
        )
        for wheel in pneumatic["dampers"].keys()
    }

    suspension_states = {
        wheel: forces.create_test_suspension_state(
            wheel,
            F_cyl=cylinder_forces[wheel],
            F_spring=spring_forces[wheel],
            F_damper=damper_forces[wheel],
        )
        for wheel in attachment_points
    }

    vertical_array, tau_x, tau_z = forces.project_forces_to_vertical_and_moments(
        suspension_states, attachment_points
    )

    vertical_forces = {
        wheel: float(value)
        for wheel, value in zip(attachment_points, vertical_array, strict=False)
    }

    return {
        "kinematics": kinematics,
        "cylinder_forces": cylinder_forces,
        "spring_forces": spring_forces,
        "damper_forces": damper_forces,
        "vertical_forces": vertical_forces,
        "moments": {"tau_x": float(tau_x), "tau_z": float(tau_z)},
        "raw_vertical_array": vertical_array,
    }


@dataclass(frozen=True)
class AssertionResult:
    """Result of evaluating a single assertion."""

    kind: str
    target: str
    expected: Any
    actual: Any
    tolerance: float
    passed: bool


def summarise_assertions(case: Any, evaluation: Mapping[str, Any]) -> list[AssertionResult]:
    """Evaluate assertions defined in *case* against computed values."""

    results: list[AssertionResult] = []
    vertical_array = evaluation["raw_vertical_array"]
    tau_x = evaluation["moments"]["tau_x"]
    tau_z = evaluation["moments"]["tau_z"]

    for assertion in case.assertions:
        expected = assertion.expected
        tolerance = float(assertion.tolerance)
        if assertion.kind == "axis-velocity":
            actual = float(evaluation["kinematics"][assertion.target]["axial_velocity"])
        elif assertion.kind == "cylinder-force":
            actual = float(evaluation["cylinder_forces"][assertion.target])
        elif assertion.kind == "spring-force":
            actual = float(evaluation["spring_forces"][assertion.target])
        elif assertion.kind == "damper-force":
            actual = float(evaluation["damper_forces"][assertion.target])
        elif assertion.kind == "vertical-force":
            actual = evaluation["vertical_forces"]
        elif assertion.kind == "moment":
            actual = {"tau_x": tau_x, "tau_z": tau_z}
        else:
            actual = None

        if assertion.kind in {"axis-velocity", "cylinder-force", "spring-force", "damper-force"}:
            passed = abs(actual - float(expected)) <= tolerance
        elif assertion.kind == "vertical-force":
            passed = all(
                abs(actual[k] - float(v)) <= tolerance for k, v in expected.items()
            )
        elif assertion.kind == "moment":
            passed = (
                abs(actual["tau_x"] - float(expected["tau_x"])) <= tolerance
                and abs(actual["tau_z"] - float(expected["tau_z"])) <= tolerance
            )
        else:
            passed = False

        results.append(
            AssertionResult(
                kind=assertion.kind,
                target=assertion.target,
                expected=expected,
                actual=actual,
                tolerance=tolerance,
                passed=passed,
            )
        )

    return results
