import logging
from typing import Dict

import numpy as np
import pytest

from src.common.units import PA_ATM, T_AMBIENT
from src.physics.integrator import create_default_rigid_body
from src.physics.odes import create_initial_conditions
from src.pneumo.cylinder import CylinderSpec
from src.pneumo.enums import (
    CheckValveKind,
    Line,
    Port,
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
from src.runtime.state import LineState, TankState, WheelState
from src.runtime.steps import (
    PhysicsStepState,
    compute_kinematics,
    integrate_body,
    update_gas_state,
)
from src.runtime.sync import PerformanceMetrics


def _build_cylinder_geom() -> CylinderGeom:
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


def _build_check_valves() -> Dict[Line, Dict[str, CheckValve]]:
    base_delta = 5_000.0
    diameter = 0.008

    def _valve(kind: CheckValveKind) -> CheckValve:
        return CheckValve(kind=kind, delta_open=base_delta, d_eq=diameter)

    return {
        line: {
            "cv_atmo": _valve(CheckValveKind.ATMO_TO_LINE),
            "cv_tank": _valve(CheckValveKind.LINE_TO_TANK),
            "p_line": PA_ATM,
        }
        for line in [Line.A1, Line.B1, Line.A2, Line.B2]
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


def _make_line_pressure_getter(system, gas_network):
    def _getter(wheel: Wheel, port: Port) -> float:
        for line_name, line in system.lines.items():
            for endpoint_wheel, endpoint_port in line.endpoints:
                if endpoint_wheel == wheel and endpoint_port == port:
                    return float(gas_network.lines[line_name].p)
        return float(gas_network.tank.p)

    return _getter


@pytest.fixture()
def step_state() -> PhysicsStepState:
    cylinder_geom = _build_cylinder_geom()
    lever = LeverGeom(L_lever=0.75, rod_joint_frac=0.45, d_frame_to_lever_hinge=0.42)

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
        master_isolation_open=True,
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
        master_isolation_open=True,
    )

    state = PhysicsStepState(
        dt=0.005,
        pneumatic_system=system,
        gas_network=gas_network,
        rigid_body=create_default_rigid_body(),
        physics_state=create_initial_conditions(heave=0.02, roll=0.01, pitch=-0.015),
        simulation_time=0.0,
        master_isolation_open=True,
        thermo_mode=ThermoMode.ISOTHERMAL,
        receiver_volume=gas_network.tank.V,
        receiver_mode=ReceiverVolumeMode.ADIABATIC_RECALC,
        prev_piston_positions={wheel: 0.0 for wheel in Wheel},
        wheel_states={wheel: WheelState(wheel) for wheel in Wheel},
        line_states={line: LineState(line) for line in Line},
        tank_state=TankState(),
        last_road_inputs={key: 0.0 for key in ("LF", "RF", "LR", "RR")},
        latest_frame_accel=np.zeros(3),
        prev_frame_velocities=np.zeros(3),
        performance=PerformanceMetrics(),
        logger=logging.getLogger("physics-step-test"),
        get_line_pressure=_make_line_pressure_getter(system, gas_network),
    )

    return state


def test_compute_kinematics_updates_wheel_state(step_state: PhysicsStepState) -> None:
    road_inputs = {"LF": 0.01, "RF": -0.005, "LR": 0.0, "RR": 0.002}

    compute_kinematics(step_state, road_inputs)

    assert step_state.last_road_inputs["LF"] == pytest.approx(0.01)
    front_left = step_state.pneumatic_system.cylinders[Wheel.LP]
    assert not np.isclose(front_left.x, 0.0)
    wheel_state = step_state.wheel_states[Wheel.LP]
    assert wheel_state.lever_angle != 0.0
    assert step_state.prev_piston_positions[Wheel.LP] == pytest.approx(
        wheel_state.piston_position
    )


def test_update_gas_state_syncs_line_states(step_state: PhysicsStepState) -> None:
    road_inputs = {"LF": 0.01, "RF": -0.005, "LR": 0.0, "RR": 0.002}
    compute_kinematics(step_state, road_inputs)

    update_gas_state(step_state)

    assert step_state.gas_network.master_isolation_open is True
    for line_name in [Line.A1, Line.B1, Line.A2, Line.B2]:
        expected_volume = step_state.pneumatic_system.get_line_volumes()[line_name][
            "total_volume"
        ]
        assert step_state.line_states[line_name].volume == pytest.approx(
            float(expected_volume)
        )

    assert step_state.tank_state.pressure == pytest.approx(
        step_state.gas_network.tank.p
    )


def test_integrate_body_advances_state(step_state: PhysicsStepState) -> None:
    road_inputs = {"LF": 0.01, "RF": -0.005, "LR": 0.0, "RR": 0.002}
    compute_kinematics(step_state, road_inputs)
    update_gas_state(step_state)

    initial_state = step_state.physics_state.copy()
    integrate_body(step_state)

    assert step_state.performance.integration_failures == 0
    assert not np.allclose(step_state.physics_state, initial_state)
    assert step_state.latest_frame_accel.shape == (3,)
