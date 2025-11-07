"""Integration tests for the lightweight PhysicsLoop helper."""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np
import pytest

from src.common.units import PA_ATM, T_AMBIENT
from src.physics.integrator import (
    PhysicsLoop,
    PhysicsLoopConfig,
    create_default_rigid_body,
)
from src.physics.odes import create_initial_conditions
from src.pneumo.cylinder import CylinderSpec
from src.pneumo.enums import (
    CheckValveKind,
    Line,
    ReceiverVolumeMode,
    ThermoMode,
    Wheel,
)
from src.pneumo.gas_state import create_line_gas_state, create_tank_gas_state
from src.pneumo.geometry import CylinderGeom, LeverGeom
from src.pneumo.network import GasNetwork
from src.pneumo.receiver import ReceiverSpec, ReceiverState
from src.pneumo.system import create_standard_diagonal_system
from src.pneumo.valves import CheckValve


def _build_default_cylinder_geom() -> CylinderGeom:
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


def _build_check_valves() -> dict[Line, dict]:
    base_delta = 5_000.0
    diameter = 0.008

    def _valve(kind: CheckValveKind) -> CheckValve:
        return CheckValve(kind=kind, delta_open=base_delta, d_eq=diameter)

    return {
        Line.A1: {
            "cv_atmo": _valve(CheckValveKind.ATMO_TO_LINE),
            "cv_tank": _valve(CheckValveKind.LINE_TO_TANK),
            "p_line": PA_ATM,
        },
        Line.B1: {
            "cv_atmo": _valve(CheckValveKind.ATMO_TO_LINE),
            "cv_tank": _valve(CheckValveKind.LINE_TO_TANK),
            "p_line": PA_ATM,
        },
        Line.A2: {
            "cv_atmo": _valve(CheckValveKind.ATMO_TO_LINE),
            "cv_tank": _valve(CheckValveKind.LINE_TO_TANK),
            "p_line": PA_ATM,
        },
        Line.B2: {
            "cv_atmo": _valve(CheckValveKind.ATMO_TO_LINE),
            "cv_tank": _valve(CheckValveKind.LINE_TO_TANK),
            "p_line": PA_ATM,
        },
    }


def _create_receiver_state() -> ReceiverState:
    spec = ReceiverSpec(V_min=0.0025, V_max=0.01)
    return ReceiverState(
        spec=spec,
        V=0.005,
        p=PA_ATM,
        T=T_AMBIENT,
        mode=ReceiverVolumeMode.ADIABATIC_RECALC,
    )


@pytest.fixture()
def pneumatic_system_and_gas() -> tuple[object, GasNetwork]:
    lever = LeverGeom(L_lever=0.75, rod_joint_frac=0.45, d_frame_to_lever_hinge=0.42)
    cylinder_geom = _build_default_cylinder_geom()

    cylinder_specs = {
        Wheel.LP: CylinderSpec(cylinder_geom, True, lever),
        Wheel.PP: CylinderSpec(cylinder_geom, True, lever),
        Wheel.LZ: CylinderSpec(cylinder_geom, False, lever),
        Wheel.PZ: CylinderSpec(cylinder_geom, False, lever),
    }

    system = create_standard_diagonal_system(
        cylinder_specs=cylinder_specs,
        line_configs=_build_check_valves(),
        receiver=_create_receiver_state(),
        master_isolation_open=False,
    )

    line_states = {}
    for line_name, info in system.get_line_volumes().items():
        volume = float(info["total_volume"])
        line_states[line_name] = create_line_gas_state(
            line_name, PA_ATM, T_AMBIENT, volume
        )

    gas_network = GasNetwork(
        lines=line_states,
        tank=create_tank_gas_state(
            V_initial=0.004,
            p_initial=PA_ATM,
            T_initial=T_AMBIENT,
            mode=ReceiverVolumeMode.ADIABATIC_RECALC,
        ),
        system_ref=system,
        master_isolation_open=False,
    )

    return system, gas_network


def test_physics_loop_updates_pneumatics(
    pneumatic_system_and_gas: tuple[object, GasNetwork],
) -> None:
    system, gas = pneumatic_system_and_gas

    config = PhysicsLoopConfig(
        dt_physics=0.005,
        dt_render=0.02,
        max_steps_per_render=4,
        thermo_mode=ThermoMode.ISOTHERMAL,
        master_isolation_open=True,
    )

    loop = PhysicsLoop(config, create_default_rigid_body(), system, gas)
    initial_state = create_initial_conditions(heave=0.02, roll=0.03, pitch=-0.015)
    loop.reset(initial_state)

    summary = loop.step_physics_fixed(config.dt_physics)

    assert summary["steps_taken"] == 1
    assert len(summary["gas_flows"]) == 1
    assert gas.master_isolation_open is True

    # Lever angles should move cylinders asymmetrically under roll input
    left_front = system.cylinders[Wheel.LP].x
    right_front = system.cylinders[Wheel.PP].x
    assert not math.isclose(left_front, right_front)

    # Gas network volumes must mirror the mechanical configuration
    expected_volumes = system.get_line_volumes()
    for line_name, info in expected_volumes.items():
        total_volume = float(info["total_volume"])
        assert math.isclose(
            gas.lines[line_name].V_curr,
            total_volume,
            rel_tol=1e-9,
        )

    # Returned state should match the loop cache
    assert np.allclose(summary["y_current"], loop.y_current)
