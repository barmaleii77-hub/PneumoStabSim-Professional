"""Physics evaluation helpers shared between tests and CLI tools.

Предоставляет вспомогательные функции для расчёта кинематики и сил
подвески, а также утилиту проверки ожидаемых значений (assertions).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from collections.abc import Iterable
from math import isclose

import numpy as np

from src.physics import forces

# ---------------------------------------------------------------------------
# Low level helpers
# ---------------------------------------------------------------------------


def _as_tuple(values: Iterable[float]) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


def _within_tolerance(actual: float, expected: float, tolerance: float) -> bool:
    """Возвращает True если |actual - expected| <= tolerance."""
    return isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance)


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------


def evaluate_physics_case(case: Any) -> dict[str, Any]:
    """Вычисляет производные величины для тестового physics case.

    Ожидается что *case.scene* содержит:
      - attachment_points: mapping[name -> (x, y)]
      - state_vectors: mapping[state_name -> sequence]
      - axis_directions: mapping[name -> (dx, dy, dz)]
      - pneumatic: dict с pressures / springs / dampers.
    """
    scene = case.scene

    attachment_points: dict[str, tuple[float, float]] = {}
    for name, coords in scene.attachment_points.items():
        values = _as_tuple(coords)
        attachment_points[str(name)] = (values[0], values[1])

    state_name = next(iter(scene.state_vectors))
    state = np.asarray(scene.state_vectors[state_name], dtype=float)

    axis: dict[str, tuple[float, ...]] = {
        str(name): _as_tuple(direction)
        for name, direction in scene.axis_directions.items()
    }

    kinematics: dict[str, dict[str, Any]] = {}
    for wheel in attachment_points:
        kinematics[wheel] = forces.compute_suspension_point_kinematics(
            wheel, state, attachment_points, axis
        )

    pneumatic = scene.pneumatic
    defaults = forces.get_default_suspension_params()

    cylinder_forces = {
        wheel: forces.compute_cylinder_force(
            payload["head"],
            payload["rod"],
            defaults["A_head"],
            defaults["A_rod"],
        )
        for wheel, payload in pneumatic["pressures"].items()
    }

    spring_forces = {
        wheel: forces.compute_spring_force(
            payload["current"],
            payload["rest"],
            defaults["k_spring"],
        )
        for wheel, payload in pneumatic["springs"].items()
    }

    damper_forces = {
        wheel: forces.compute_damper_force(
            kinematics[wheel]["axial_velocity"],
            defaults["c_damper"],
            defaults["F_damper_min"],
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
        for wheel, value in zip(attachment_points, vertical_array, strict=True)
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


# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AssertionResult:
    """Результат одной проверки значения."""

    kind: str
    target: str
    expected: Any
    actual: Any
    tolerance: float
    passed: bool


def summarise_assertions(
    case: Any, evaluation: Mapping[str, Any]
) -> list[AssertionResult]:
    """Выполняет assertions и возвращает список результатов."""
    results: list[AssertionResult] = []
    tau_x = evaluation["moments"]["tau_x"]
    tau_z = evaluation["moments"]["tau_z"]

    for assertion in case.assertions:
        expected = assertion.expected
        tolerance = float(assertion.tolerance)
        actual: Any
        passed: bool

        if assertion.kind == "axis-velocity":
            actual_value = float(
                evaluation["kinematics"][assertion.target]["axial_velocity"]
            )
            actual = actual_value
            passed = _within_tolerance(actual_value, float(expected), tolerance)
        elif assertion.kind == "cylinder-force":
            actual_value = float(evaluation["cylinder_forces"][assertion.target])
            actual = actual_value
            passed = _within_tolerance(actual_value, float(expected), tolerance)
        elif assertion.kind == "spring-force":
            actual_value = float(evaluation["spring_forces"][assertion.target])
            actual = actual_value
            passed = _within_tolerance(actual_value, float(expected), tolerance)
        elif assertion.kind == "damper-force":
            actual_value = float(evaluation["damper_forces"][assertion.target])
            actual = actual_value
            passed = _within_tolerance(actual_value, float(expected), tolerance)
        elif assertion.kind == "vertical-force":
            expected_map = {k: float(v) for k, v in expected.items()}
            actual_map = {
                wheel: float(force)
                for wheel, force in evaluation["vertical_forces"].items()
            }
            actual = actual_map
            passed = all(
                abs(actual_map[k] - expected_map[k]) <= tolerance for k in expected_map
            )
        elif assertion.kind == "moment":
            expected_map = {k: float(v) for k, v in expected.items()}
            actual_map = {"tau_x": float(tau_x), "tau_z": float(tau_z)}
            actual = actual_map
            passed = all(
                _within_tolerance(actual_map[key], expected_map[key], tolerance)
                for key in expected_map
            )
        else:
            raise ValueError(f"Unsupported assertion kind: {assertion.kind}")

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
