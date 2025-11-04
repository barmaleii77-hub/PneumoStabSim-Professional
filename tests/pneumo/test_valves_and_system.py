"""Tests covering pneumatic valves and system invariants."""

from __future__ import annotations

import math

import pytest

from src.common.units import PA_ATM, T_AMBIENT
from src.pneumo.cylinder import CylinderSpec
from src.pneumo.enums import (
    CheckValveKind,
    Line,
    ReceiverVolumeMode,
    ReliefValveKind,
    Wheel,
)
from src.pneumo.geometry import CylinderGeom, LeverGeom
from src.pneumo.receiver import ReceiverSpec, ReceiverState
from src.pneumo.system import create_standard_diagonal_system
from src.pneumo.valves import CheckValve, ReliefValve


def _default_cylinder_geom() -> CylinderGeom:
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


def _build_line_config(delta: float = 5_000.0, diameter: float = 0.008) -> dict[Line, dict]:
    def _valve(kind: CheckValveKind) -> CheckValve:
        return CheckValve(kind=kind, delta_open=delta, d_eq=diameter)

    return {
        Line.A1: {"cv_atmo": _valve(CheckValveKind.ATMO_TO_LINE), "cv_tank": _valve(CheckValveKind.LINE_TO_TANK), "p_line": PA_ATM},
        Line.B1: {"cv_atmo": _valve(CheckValveKind.ATMO_TO_LINE), "cv_tank": _valve(CheckValveKind.LINE_TO_TANK), "p_line": PA_ATM},
        Line.A2: {"cv_atmo": _valve(CheckValveKind.ATMO_TO_LINE), "cv_tank": _valve(CheckValveKind.LINE_TO_TANK), "p_line": PA_ATM},
        Line.B2: {"cv_atmo": _valve(CheckValveKind.ATMO_TO_LINE), "cv_tank": _valve(CheckValveKind.LINE_TO_TANK), "p_line": PA_ATM},
    }


def test_check_valve_hysteresis_cycle():
    """Ensure check valves respect hysteresis thresholds and validation rules."""

    valve = CheckValve(delta_open=6_000.0, d_eq=0.01, hyst=500.0)
    valve.set_pressures(120_000.0, 100_000.0)
    assert valve.is_open() is True

    valve.set_pressures(104_900.0, 100_000.0)
    assert valve.is_open() is True  # still above close threshold

    valve.set_pressures(104_000.0, 100_000.0)
    assert valve.is_open() is False  # drops below close threshold

    report = valve.validate_invariants()
    assert report["is_valid"]
    assert not report["errors"]


@pytest.mark.parametrize(
    "kwargs, opening_pressure, closing_pressure, expectation",
    [
        (
            {"kind": ReliefValveKind.SAFETY, "p_set": 1_200_000.0, "hyst": 50_000.0},
            1_280_000.0,
            1_150_000.0,
            ("ge", 0.0),
        ),
        (
            {
                "kind": ReliefValveKind.STIFFNESS,
                "p_set": 1_200_000.0,
                "hyst": 50_000.0,
                "d_eq": 5.0,
            },
            1_280_000.0,
            1_150_000.0,
            ("ge", 0.0),
        ),
        (
            {
                "kind": ReliefValveKind.MIN_PRESS,
                "p_set": 100_000.0,
                "hyst": 5_000.0,
                "d_eq": 1.0,
            },
            92_000.0,
            110_000.0,
            ("approx", 8_000.0),
        ),
    ],
)
def test_relief_valve_modes(kwargs, opening_pressure, closing_pressure, expectation):
    """Verify relief valve behaviour across supported operating modes."""

    valve = ReliefValve(**kwargs)

    valve.update_pressure(opening_pressure)
    assert valve.is_open() is True

    flow = valve.calculate_flow()
    mode, target = expectation
    if mode == "approx":
        assert flow == pytest.approx(target, rel=1e-3)
    elif mode == "ge":
        assert flow >= target
    else:  # pragma: no cover - ensure future expectations are handled explicitly
        raise AssertionError(f"Unexpected expectation mode: {mode}")

    valve.update_pressure(closing_pressure)
    if kwargs["kind"] == ReliefValveKind.MIN_PRESS:
        assert valve.is_open() is False
    else:
        assert valve.is_open() is False

    report = valve.validate_invariants()
    assert report["is_valid"]


def test_pneumatic_system_invariants():
    """Construct the diagonal system and ensure invariants hold."""

    lever = LeverGeom(L_lever=0.75, rod_joint_frac=0.45, d_frame_to_lever_hinge=0.42)
    cylinder_geom = _default_cylinder_geom()
    cylinder_specs = {
        Wheel.LP: CylinderSpec(cylinder_geom, True, lever),
        Wheel.PP: CylinderSpec(cylinder_geom, True, lever),
        Wheel.LZ: CylinderSpec(cylinder_geom, False, lever),
        Wheel.PZ: CylinderSpec(cylinder_geom, False, lever),
    }

    receiver_spec = ReceiverSpec(V_min=0.0025, V_max=0.01)
    receiver = ReceiverState(
        spec=receiver_spec,
        V=0.005,
        p=PA_ATM,
        T=T_AMBIENT,
        mode=ReceiverVolumeMode.ADIABATIC_RECALC,
    )

    system = create_standard_diagonal_system(
        cylinder_specs=cylinder_specs,
        line_configs=_build_line_config(),
        receiver=receiver,
        master_isolation_open=True,
    )

    result = system.validate_invariants()
    assert result["is_valid"], result["errors"]

    receiver_result = receiver_spec.validate_invariants()
    assert receiver_result["is_valid"]

    line_volumes = system.get_line_volumes()
    for info in line_volumes.values():
        assert info["total_volume"] > 0
        for contribution in info["endpoints"]:
            assert contribution["volume"] > 0

    # Check that diagonal connections enforce expected pairing semantics
    diag = system.lines[Line.A1]
    assert diag.is_diagonal_connection() is True
    description = diag.get_connection_description()
    assert "LP" in description and "PZ" in description

    # Validate lever updates propagate to cylinders
    system.update_system_from_lever_angles(
        {
            Wheel.LP: math.radians(1.2),
            Wheel.PP: math.radians(1.0),
            Wheel.LZ: math.radians(-0.8),
            Wheel.PZ: math.radians(-1.1),
        }
    )
    assert system.cylinders[Wheel.LP].x != system.cylinders[Wheel.PP].x

