import logging
from dataclasses import replace

import math
from dataclasses import dataclass

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
from src.runtime.steps.kinematics import integrate_lever_state
from src.runtime.steps.context import LeverDynamicsConfig
from src.runtime.sync import PerformanceMetrics


@dataclass
class _StubCylinderGeom:
    L_travel_max: float = 100.0
    Z_axle: float = 0.0

    def area_head(self, is_front: bool) -> float:  # pragma: no cover - simple stub
        return 0.01

    def area_rod(self, is_front: bool) -> float:  # pragma: no cover - simple stub
        return 0.01


@dataclass
class _StubLeverGeom:
    L_lever: float

    def angle_to_displacement(self, angle: float) -> float:
        return self.L_lever * angle

    def mechanical_advantage(self, angle: float) -> float:
        return self.L_lever


@dataclass
class _StubCylinderSpec:
    geometry: _StubCylinderGeom
    is_front: bool
    lever_geom: _StubLeverGeom


@dataclass
class _StubCylinder:
    spec: _StubCylinderSpec
    penetration_head: float = 0.0
    penetration_rod: float = 0.0


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


def _build_check_valves() -> dict[Line, dict[str, CheckValve]]:
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
    lever_kwargs = dict(
        L_lever=0.75,
        rod_joint_frac=0.45,
        d_frame_to_lever_hinge=0.42,
    )

    lever_geometries = {
        wheel: LeverGeom(**lever_kwargs)
        for wheel in (Wheel.LP, Wheel.PP, Wheel.LZ, Wheel.PZ)
    }

    lever_sample = next(iter(lever_geometries.values()))

    cylinder_specs = {
        Wheel.LP: CylinderSpec(cylinder_geom, True, lever_geometries[Wheel.LP]),
        Wheel.PP: CylinderSpec(cylinder_geom, True, lever_geometries[Wheel.PP]),
        Wheel.LZ: CylinderSpec(cylinder_geom, False, lever_geometries[Wheel.LZ]),
        Wheel.PZ: CylinderSpec(cylinder_geom, False, lever_geometries[Wheel.PZ]),
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
        prev_road_inputs={key: 0.0 for key in ("LF", "RF", "LR", "RR")},
        latest_frame_accel=np.zeros(3),
        prev_frame_velocities=np.zeros(3),
        performance=PerformanceMetrics(),
        logger=logging.getLogger("physics-step-test"),
        get_line_pressure=_make_line_pressure_getter(system, gas_network),
        lever_config=LeverDynamicsConfig(
            include_springs=True,
            include_dampers=True,
            include_pneumatics=True,
            spring_constant=50_000.0,
            damper_coefficient=2_000.0,
            damper_threshold=50.0,
            spring_rest_position=0.0,
            lever_inertia=50.0 * lever_sample.L_lever * lever_sample.L_lever,
            integrator_method="rk4",
        ),
    )

    return state


def test_compute_kinematics_updates_wheel_state(step_state: PhysicsStepState) -> None:
    road_inputs = {"LF": 0.01, "RF": -0.005, "LR": 0.0, "RR": 0.002}

    step_state.prev_road_inputs = dict(step_state.last_road_inputs)
    compute_kinematics(step_state, road_inputs)

    assert step_state.last_road_inputs["LF"] == pytest.approx(0.01)
    front_left = step_state.pneumatic_system.cylinders[Wheel.LP]
    assert not np.isclose(front_left.x, 0.0)
    wheel_state = step_state.wheel_states[Wheel.LP]
    assert wheel_state.lever_angle != 0.0
    assert wheel_state.lever_angular_velocity != 0.0
    assert step_state.prev_piston_positions[Wheel.LP] == pytest.approx(
        wheel_state.piston_position
    )


def test_integrate_lever_state_without_forces(
    step_state: PhysicsStepState,
) -> None:
    wheel = Wheel.LP
    cylinder = step_state.pneumatic_system.cylinders[wheel]
    lever_geom = cylinder.spec.lever_geom

    step_state.lever_config = replace(
        step_state.lever_config,
        include_springs=False,
        include_dampers=False,
        include_pneumatics=False,
        spring_constant=0.0,
        damper_coefficient=0.0,
        integrator_method="rk4",
    )

    theta0 = 0.18
    omega0 = -0.35

    result = integrate_lever_state(
        wheel=wheel,
        theta0=theta0,
        omega0=omega0,
        dt=step_state.dt,
        lever_config=step_state.lever_config,
        lever_geom=lever_geom,
        cylinder=cylinder,
        road_displacement=0.0,
        road_velocity=0.0,
        get_line_pressure=step_state.get_line_pressure,
    )

    assert result.angle == pytest.approx(theta0)
    assert result.angular_velocity == pytest.approx(omega0)
    assert result.spring_force == pytest.approx(0.0)
    assert result.damper_force == pytest.approx(0.0)
    assert result.pneumatic_force == pytest.approx(0.0)
    assert result.clamped is False


def test_free_oscillation_rk4_conserves_amplitude() -> None:
    lever_length = 0.75
    inertia = 25.0
    spring_constant = 10_000.0

    lever_geom = _StubLeverGeom(lever_length)
    cylinder = _StubCylinder(
        spec=_StubCylinderSpec(
            geometry=_StubCylinderGeom(), is_front=True, lever_geom=lever_geom
        )
    )

    config = LeverDynamicsConfig(
        include_springs=True,
        include_dampers=False,
        include_pneumatics=False,
        spring_constant=spring_constant,
        damper_coefficient=0.0,
        damper_threshold=0.0,
        spring_rest_position=0.0,
        lever_inertia=inertia,
        integrator_method="rk4",
    )

    theta = 0.1
    omega = 0.0
    dt = 5e-4

    natural_freq = math.sqrt(spring_constant * lever_length**2 / inertia)
    period = 2.0 * math.pi / natural_freq
    steps = max(1, int(round(period / dt)))

    for _ in range(steps):
        result = integrate_lever_state(
            wheel=Wheel.LP,
            theta0=theta,
            omega0=omega,
            dt=dt,
            lever_config=config,
            lever_geom=lever_geom,
            cylinder=cylinder,
            road_displacement=0.0,
            road_velocity=0.0,
            get_line_pressure=lambda *_args: 0.0,
            method="rk4",
        )
        theta, omega = result.angle, result.angular_velocity

    assert theta == pytest.approx(0.1, abs=5e-3)
    assert omega == pytest.approx(0.0, abs=5e-3)


def test_lever_damping_reduces_amplitude() -> None:
    lever_length = 0.75
    inertia = 25.0
    spring_constant = 10_000.0
    damper = 1_000.0

    lever_geom = _StubLeverGeom(lever_length)
    cylinder = _StubCylinder(
        spec=_StubCylinderSpec(
            geometry=_StubCylinderGeom(), is_front=True, lever_geom=lever_geom
        )
    )

    config = LeverDynamicsConfig(
        include_springs=True,
        include_dampers=True,
        include_pneumatics=False,
        spring_constant=spring_constant,
        damper_coefficient=damper,
        damper_threshold=0.0,
        spring_rest_position=0.0,
        lever_inertia=inertia,
        integrator_method="rk4",
    )

    theta = 0.15
    omega = 0.0
    dt = 1e-3
    steps = 4000

    initial_peak = 0.0
    late_peak = 0.0

    for idx in range(steps):
        result = integrate_lever_state(
            wheel=Wheel.LP,
            theta0=theta,
            omega0=omega,
            dt=dt,
            lever_config=config,
            lever_geom=lever_geom,
            cylinder=cylinder,
            road_displacement=0.0,
            road_velocity=0.0,
            get_line_pressure=lambda *_args: 0.0,
            method="rk4",
        )
        theta, omega = result.angle, result.angular_velocity
        amplitude = abs(theta)
        if idx < steps // 4:
            initial_peak = max(initial_peak, amplitude)
        else:
            late_peak = max(late_peak, amplitude)

    assert late_peak < initial_peak


def test_update_gas_state_syncs_line_states(step_state: PhysicsStepState) -> None:
    road_inputs = {"LF": 0.01, "RF": -0.005, "LR": 0.0, "RR": 0.002}
    step_state.prev_road_inputs = dict(step_state.last_road_inputs)
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
    step_state.prev_road_inputs = dict(step_state.last_road_inputs)
    compute_kinematics(step_state, road_inputs)
    update_gas_state(step_state)

    initial_state = step_state.physics_state.copy()
    integrate_body(step_state)

    assert step_state.performance.integration_failures == 0
    assert not np.allclose(step_state.physics_state, initial_state)
    assert step_state.latest_frame_accel.shape == (3,)


def test_free_oscillation_without_damping(step_state: PhysicsStepState) -> None:
    step_state.lever_config = replace(
        step_state.lever_config,
        include_dampers=False,
        include_pneumatics=False,
        damper_coefficient=0.0,
    )

    wheel_state = step_state.wheel_states[Wheel.LP]
    wheel_state.lever_angle = 0.12
    wheel_state.lever_angular_velocity = 0.0

    zero_inputs = {key: 0.0 for key in ("LF", "RF", "LR", "RR")}
    angles: list[float] = []
    for _ in range(120):
        step_state.prev_road_inputs = dict(step_state.last_road_inputs)
        compute_kinematics(step_state, zero_inputs)
        angles.append(step_state.wheel_states[Wheel.LP].lever_angle)

    assert any(angle < 0.0 for angle in angles[10:])
    max_amp = max(abs(angle) for angle in angles)
    min_amp = min(abs(angle) for angle in angles if abs(angle) > 1e-6)
    assert max_amp < 0.2
    assert min_amp > 0.04


def test_free_oscillation_with_damping(step_state: PhysicsStepState) -> None:
    step_state.lever_config = replace(
        step_state.lever_config,
        include_pneumatics=False,
        include_dampers=True,
        damper_coefficient=6_000.0,
    )

    wheel_state = step_state.wheel_states[Wheel.LP]
    wheel_state.lever_angle = 0.12
    wheel_state.lever_angular_velocity = 0.0

    zero_inputs = {key: 0.0 for key in ("LF", "RF", "LR", "RR")}
    last_angles: list[float] = []
    for _ in range(160):
        step_state.prev_road_inputs = dict(step_state.last_road_inputs)
        compute_kinematics(step_state, zero_inputs)
        last_angles.append(step_state.wheel_states[Wheel.LP].lever_angle)

    assert abs(last_angles[-1]) < 0.12
    assert abs(last_angles[-1]) < 0.12 * 0.6
