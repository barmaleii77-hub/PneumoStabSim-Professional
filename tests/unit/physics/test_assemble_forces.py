import json
import math
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pytest

from src.physics.odes import (
    assemble_forces,
    RigidBody3DOF,
    reset_suspension_settings_cache,
)
from src.physics.forces import compute_cylinder_force
from src.pneumo.cylinder import CylinderSpec
from src.pneumo.enums import CheckValveKind, Line, Port, ReceiverVolumeMode, Wheel
from src.pneumo.gas_state import create_line_gas_state, create_tank_gas_state
from src.pneumo.geometry import CylinderGeom, LeverGeom
from src.pneumo.network import GasNetwork
from src.pneumo.receiver import ReceiverSpec, ReceiverState
from src.pneumo.system import create_standard_diagonal_system
from src.pneumo.valves import CheckValve
from src.common.units import PA_ATM, T_AMBIENT


@pytest.fixture()
def pneumatic_system_with_gas() -> tuple[object, GasNetwork, dict[Line, float]]:
    """Construct a minimal pneumatic system and gas network for force tests."""

    lever_geom = LeverGeom(
        L_lever=0.75,
        rod_joint_frac=0.45,
        d_frame_to_lever_hinge=0.42,
    )
    cylinder_geom = CylinderGeom(
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

    cylinder_specs = {
        wheel: CylinderSpec(cylinder_geom, wheel in (Wheel.LP, Wheel.PP), lever_geom)
        for wheel in Wheel
    }

    def _check_valve(kind: CheckValveKind) -> CheckValve:
        return CheckValve(kind=kind, delta_open=500.0, d_eq=0.01)

    line_configs = {
        line: {
            "cv_atmo": _check_valve(CheckValveKind.ATMO_TO_LINE),
            "cv_tank": _check_valve(CheckValveKind.LINE_TO_TANK),
            "p_line": PA_ATM,
        }
        for line in Line
    }

    receiver_spec = ReceiverSpec(V_min=0.002, V_max=0.005)
    receiver_state = ReceiverState(
        spec=receiver_spec,
        V=0.003,
        p=PA_ATM,
        T=T_AMBIENT,
        mode=ReceiverVolumeMode.NO_RECALC,
    )

    system = create_standard_diagonal_system(
        cylinder_specs=cylinder_specs,
        line_configs=line_configs,
        receiver=receiver_state,
        master_isolation_open=False,
    )

    line_pressures: dict[Line, float] = {
        Line.A1: 150_000.0,
        Line.B1: 210_000.0,
        Line.A2: 170_000.0,
        Line.B2: 190_000.0,
    }

    line_volumes = system.get_line_volumes()
    gas_lines = {
        line: create_line_gas_state(
            line,
            p_initial=pressure,
            T_initial=T_AMBIENT,
            V_initial=float(line_volumes[line]["total_volume"]),
        )
        for line, pressure in line_pressures.items()
    }

    tank_state = create_tank_gas_state(
        V_initial=0.004,
        p_initial=PA_ATM,
        T_initial=T_AMBIENT,
        mode=ReceiverVolumeMode.NO_RECALC,
    )

    gas_network = GasNetwork(
        lines=gas_lines,
        tank=tank_state,
        system_ref=system,
        master_isolation_open=False,
    )

    return system, gas_network, line_pressures


def test_assemble_forces_uses_pneumatic_pressures(
    pneumatic_system_with_gas: tuple[object, GasNetwork, dict[Line, float]],
) -> None:
    system, gas_network, _ = pneumatic_system_with_gas

    params = RigidBody3DOF(M=1800.0, Ix=2200.0, Iz=2400.0)
    state = np.zeros(6)

    vertical_forces, tau_x, tau_z = assemble_forces(system, gas_network, state, params)

    wheel_order = ["LP", "PP", "LZ", "PZ"]
    line_lookup = {
        Wheel.LP: {Port.HEAD: Line.B1, Port.ROD: Line.A1},
        Wheel.PP: {Port.HEAD: Line.B2, Port.ROD: Line.A2},
        Wheel.LZ: {Port.HEAD: Line.A2, Port.ROD: Line.B2},
        Wheel.PZ: {Port.HEAD: Line.A1, Port.ROD: Line.B1},
    }

    expected_forces = []
    expected_tau_x = 0.0
    expected_tau_z = 0.0

    for index, name in enumerate(wheel_order):
        wheel_enum = Wheel[name]
        cylinder = system.cylinders[wheel_enum]
        geom = cylinder.spec.geometry
        area_head = geom.area_head(cylinder.spec.is_front)
        area_rod = geom.area_rod(cylinder.spec.is_front)
        head_line = line_lookup[wheel_enum][Port.HEAD]
        rod_line = line_lookup[wheel_enum][Port.ROD]
        head_pressure = gas_network.lines[head_line].p
        rod_pressure = gas_network.lines[rod_line].p

        expected_force = compute_cylinder_force(
            head_pressure, rod_pressure, area_head, area_rod
        )
        expected_forces.append(expected_force)

        x_i, z_i = params.attachment_points[name]
        expected_tau_x += expected_force * z_i
        expected_tau_z += expected_force * x_i

    expected_array = np.array(expected_forces, dtype=float)

    assert np.allclose(vertical_forces, expected_array, rtol=1e-9, atol=1e-6)
    assert math.isclose(tau_x, expected_tau_x, abs_tol=1e-9)
    assert math.isclose(tau_z, expected_tau_z, abs_tol=1e-9)


def test_assemble_forces_without_system() -> None:
    params = RigidBody3DOF(M=1800.0, Ix=2200.0, Iz=2400.0)
    # Provide non-zero state to ensure spring/damper contributions remain defined.
    state = np.array([0.01, 0.005, -0.004, 0.0, 0.0, 0.0])

    vertical_forces, tau_x, tau_z = assemble_forces(None, None, state, params)

    assert vertical_forces.shape == (4,)
    assert np.all(np.isfinite(vertical_forces))
    assert math.isfinite(tau_x)
    assert math.isfinite(tau_z)


def test_assemble_forces_uses_settings_for_suspension(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    original_settings = json.loads(
        Path("config/app_settings.json").read_text(encoding="utf-8")
    )

    # Configure distinctive suspension parameters to verify they are applied.
    override = json.loads(json.dumps(original_settings))
    override["current"]["physics"]["suspension"]["spring_constant"] = 1234.0
    override["current"]["physics"]["suspension"]["damper_coefficient"] = 56.0

    custom_settings = tmp_path / "settings.json"
    custom_settings.write_text(
        json.dumps(override, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    monkeypatch.setenv("PSS_SETTINGS_FILE", str(custom_settings))
    reset_suspension_settings_cache()

    params = RigidBody3DOF(M=1800.0, Ix=2200.0, Iz=2400.0)
    state = np.array([0.02, 0.0, 0.0, 0.1, 0.0, 0.0])

    vertical_forces, _, _ = assemble_forces(None, None, state, params)

    static_load = params.static_load_for("LP")
    expected = static_load - 1234.0 * state[0] - 56.0 * state[3]

    assert math.isclose(vertical_forces[0], expected, rel_tol=1e-9, abs_tol=1e-9)
    reset_suspension_settings_cache()
