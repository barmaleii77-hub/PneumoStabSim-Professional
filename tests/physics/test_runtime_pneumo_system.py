"""Unit tests for the runtime pneumatic aggregation helper."""

from __future__ import annotations

import importlib.util
import math
import sys
import types
from pathlib import Path

import numpy as np
import pytest

from src.common.units import PA_ATM, T_AMBIENT
from src.pneumo.cylinder import CylinderSpec
from src.pneumo.enums import (
    CheckValveKind,
    Line,
    ReceiverVolumeMode,
    ThermoMode,
    Wheel,
)
from src.pneumo.geometry import CylinderGeom, LeverGeom
from src.pneumo.gas_state import create_line_gas_state, create_tank_gas_state
from src.pneumo.network import GasNetwork
from src.pneumo.receiver import ReceiverSpec, ReceiverState
from src.pneumo.system import create_standard_diagonal_system
from src.pneumo.valves import CheckValve


def _install_forces_stub() -> None:
    module_name = "src.physics.forces"
    if module_name in sys.modules:
        return

    stub = types.ModuleType(module_name)

    def compute_cylinder_force(
        p_head: float, p_rod: float, area_head: float, area_rod: float
    ) -> float:
        return (p_head - PA_ATM) * area_head - (p_rod - PA_ATM) * area_rod

    stub.compute_cylinder_force = compute_cylinder_force  # type: ignore[attr-defined]
    sys.modules[module_name] = stub


def _load_pneumatic_system_class():
    _install_forces_stub()
    module_path = (
        Path(__file__).resolve().parents[2] / "src" / "physics" / "pneumo_system.py"
    )
    spec = importlib.util.spec_from_file_location("runtime_pneumo_system", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load pneumatic system module for tests")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.PneumaticSystem


PneumaticSystem = _load_pneumatic_system_class()


def _build_runtime_system() -> tuple[PneumaticSystem, object]:
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
        Wheel.LP: CylinderSpec(cylinder_geom, True, lever_geom),
        Wheel.PP: CylinderSpec(cylinder_geom, True, lever_geom),
        Wheel.LZ: CylinderSpec(cylinder_geom, False, lever_geom),
        Wheel.PZ: CylinderSpec(cylinder_geom, False, lever_geom),
    }

    def _check_valve(kind: CheckValveKind) -> CheckValve:
        return CheckValve(kind=kind, delta_open=5000.0, d_eq=0.006)

    line_configs = {
        line: {
            "cv_atmo": _check_valve(CheckValveKind.ATMO_TO_LINE),
            "cv_tank": _check_valve(CheckValveKind.LINE_TO_TANK),
            "p_line": PA_ATM,
        }
        for line in (Line.A1, Line.B1, Line.A2, Line.B2)
    }

    receiver_spec = ReceiverSpec(V_min=0.04, V_max=0.08)
    receiver_state = ReceiverState(
        spec=receiver_spec,
        V=0.05,
        p=PA_ATM,
        T=T_AMBIENT,
        mode=ReceiverVolumeMode.NO_RECALC,
    )

    structure = create_standard_diagonal_system(
        cylinder_specs=cylinder_specs,
        line_configs=line_configs,
        receiver=receiver_state,
        master_isolation_open=False,
    )

    line_states = {}
    for line_name, volume_info in structure.get_line_volumes().items():
        line_states[line_name] = create_line_gas_state(
            line_name,
            PA_ATM,
            T_AMBIENT,
            volume_info["total_volume"],
        )

    tank_state = create_tank_gas_state(
        V_initial=receiver_state.V,
        p_initial=PA_ATM,
        T_initial=T_AMBIENT,
        mode=ReceiverVolumeMode.NO_RECALC,
    )

    gas_network = GasNetwork(
        lines=line_states,
        tank=tank_state,
        system_ref=structure,
        master_isolation_open=False,
        ambient_temperature=T_AMBIENT,
        relief_min_threshold=2.5 * PA_ATM,
        relief_stiff_threshold=3.5 * PA_ATM,
        relief_safety_threshold=4.0 * PA_ATM,
        relief_min_orifice_diameter=0.008,
        relief_stiff_orifice_diameter=0.006,
    )

    runtime = PneumaticSystem(structure, gas_network)
    return runtime, type(
        "defaults", (), {"system": structure, "gas_network": gas_network}
    )


@pytest.fixture()
def runtime_system() -> tuple[PneumaticSystem, object]:
    return _build_runtime_system()


def _expected_force_for_wheel(defaults, wheel: Wheel) -> float:
    structure = defaults.system
    gas = defaults.gas_network
    cylinder = structure.cylinders[wheel]
    geom = cylinder.spec.geometry

    if wheel is Wheel.LP:
        head_line, rod_line = Line.B1, Line.A1
    elif wheel is Wheel.PP:
        head_line, rod_line = Line.B2, Line.A2
    elif wheel is Wheel.LZ:
        head_line, rod_line = Line.A2, Line.B2
    else:
        head_line, rod_line = Line.A1, Line.B1

    head_pressure = gas.lines[head_line].p
    rod_pressure = gas.lines[rod_line].p
    area_head = geom.area_head(cylinder.spec.is_front)
    area_rod = geom.area_rod(cylinder.spec.is_front)
    head_gauge = head_pressure - PA_ATM
    rod_gauge = rod_pressure - PA_ATM
    return head_gauge * area_head - rod_gauge * area_rod


def test_update_returns_expected_forces(runtime_system) -> None:
    runtime, defaults = runtime_system
    gas = defaults.gas_network

    gas.lines[Line.A1].p = 1.8 * PA_ATM
    gas.lines[Line.B1].p = 2.6 * PA_ATM
    gas.lines[Line.A2].p = 1.5 * PA_ATM
    gas.lines[Line.B2].p = 2.2 * PA_ATM

    lever_angles = {wheel: 0.0 for wheel in Wheel}
    update = runtime.update(
        lever_angles, master_isolation_open=False, thermo_mode=ThermoMode.ISOTHERMAL
    )

    for wheel in Wheel:
        expected_force = _expected_force_for_wheel(defaults, wheel)
        assert update.wheel_forces[wheel] == pytest.approx(expected_force, rel=1e-6)
        assert math.isclose(
            update.piston_positions[wheel],
            defaults.system.cylinders[wheel].x,
            rel_tol=0.0,
            abs_tol=1e-12,
        )

    left_sum = update.wheel_forces[Wheel.LP] + update.wheel_forces[Wheel.LZ]
    right_sum = update.wheel_forces[Wheel.PP] + update.wheel_forces[Wheel.PZ]
    assert update.left_force == pytest.approx(left_sum, rel=1e-6)
    assert update.right_force == pytest.approx(right_sum, rel=1e-6)

    for axis in update.axis_directions.values():
        assert pytest.approx(np.linalg.norm(np.asarray(axis))) == 1.0


def test_dead_zone_enforcement(runtime_system) -> None:
    _runtime, defaults = runtime_system
    strict_runtime = PneumaticSystem(
        defaults.system,
        defaults.gas_network,
        dead_zone_head_fraction=1.0,
        dead_zone_rod_fraction=0.5,
    )

    lever_angles = {wheel: 0.0 for wheel in Wheel}
    update = strict_runtime.update(
        lever_angles, master_isolation_open=False, thermo_mode=ThermoMode.ISOTHERMAL
    )

    for wheel, cylinder in defaults.system.cylinders.items():
        geom = cylinder.spec.geometry
        half_travel = geom.L_travel_max / 2.0
        max_head = cylinder.vol_head(-half_travel)
        max_rod = cylinder.vol_rod(half_travel)
        head_volume, rod_volume = update.chamber_volumes[wheel]
        assert head_volume == pytest.approx(max_head, rel=1e-6)
        assert rod_volume >= 0.5 * max_rod - 1e-9


def test_master_isolation_equalises_pressures(runtime_system) -> None:
    runtime, defaults = runtime_system
    gas = defaults.gas_network

    # Introduce notable pressure imbalance
    gas.lines[Line.A1].p = 3.1 * PA_ATM
    gas.lines[Line.B1].p = 1.4 * PA_ATM
    gas.lines[Line.A2].p = 2.2 * PA_ATM
    gas.lines[Line.B2].p = 2.8 * PA_ATM
    for line_state in gas.lines.values():
        line_state.m = max(line_state.m, 0.25)

    lever_angles = {wheel: 0.0 for wheel in Wheel}
    runtime.update(
        lever_angles, master_isolation_open=True, thermo_mode=ThermoMode.ISOTHERMAL
    )

    pressures = {line.p for line in gas.lines.values()}
    assert max(pressures) - min(pressures) < 1e-3
