"""Runtime pneumatic aggregation utilities.

This module bridges the structural :mod:`src.pneumo.system` definition and the
thermodynamic network so that the real-time simulation can expose coherent
forces, piston positions, and chamber volumes for every wheel.  The
implementation mirrors the high-level algorithms described in the technical
specification (§3.2–3.3): first the mechanical configuration is updated from
lever angles, then the gas network is synchronised (including optional master
valve equalisation), and finally pneumatic forces are projected back to the
rigid body model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Tuple

from src.physics.forces import compute_cylinder_force
from src.pneumo.enums import Line, Port, ThermoMode, Wheel
from src.pneumo.network import GasNetwork
from src.pneumo.system import PneumaticSystem as StructuralPneumaticSystem


@dataclass(frozen=True)
class PneumaticUpdate:
    """Aggregated pneumatic state computed for the current step."""

    left_force: float
    right_force: float
    wheel_forces: Dict[Wheel, float]
    piston_positions: Dict[Wheel, float]
    chamber_volumes: Dict[Wheel, Tuple[float, float]]
    axis_directions: Dict[Wheel, Tuple[float, float, float]]
    pressures: Dict[Wheel, Tuple[float, float]]


class PneumaticSystem:
    """Runtime helper that couples the structural model with the gas network."""

    def __init__(
        self,
        structure: StructuralPneumaticSystem,
        gas_network: GasNetwork,
        *,
        dead_zone_head_fraction: float = 0.0,
        dead_zone_rod_fraction: float = 0.0,
    ) -> None:
        self._structure = structure
        self._gas_network = gas_network
        self._dead_zone_head_fraction = max(0.0, float(dead_zone_head_fraction))
        self._dead_zone_rod_fraction = max(0.0, float(dead_zone_rod_fraction))

        # Cache reference volumes used for dead-zone enforcement so that they do
        # not need to be recomputed every frame.
        self._max_head_volume: Dict[Wheel, float] = {}
        self._max_rod_volume: Dict[Wheel, float] = {}
        for wheel, cylinder in self._structure.cylinders.items():
            geom = cylinder.spec.geometry
            half_travel = geom.L_travel_max / 2.0
            self._max_head_volume[wheel] = cylinder.vol_head(-half_travel)
            self._max_rod_volume[wheel] = cylinder.vol_rod(half_travel)

        self._last_update: PneumaticUpdate | None = None

    # ------------------------------------------------------------------
    # Compatibility helpers (delegate to structural system)
    # ------------------------------------------------------------------
    @property
    def cylinders(self):
        return self._structure.cylinders

    @property
    def lines(self):
        return self._structure.lines

    @property
    def receiver(self):
        return self._structure.receiver

    def get_line_volumes(self):
        return self._structure.get_line_volumes()

    def update_system_from_lever_angles(self, angles: Mapping[Wheel, float]):
        return self._structure.update_system_from_lever_angles(angles)

    def validate_invariants(self):
        return self._structure.validate_invariants()

    # ------------------------------------------------------------------
    # Runtime aggregation
    # ------------------------------------------------------------------
    def _line_for_endpoint(self, wheel: Wheel, port: Port) -> Line | None:
        for line_name, line in self.lines.items():
            for endpoint_wheel, endpoint_port in line.endpoints:
                if endpoint_wheel == wheel and endpoint_port == port:
                    return line_name
        return None

    @staticmethod
    def _normalise(vector: Tuple[float, float, float]) -> Tuple[float, float, float]:
        vx, vy, vz = vector
        magnitude_sq = vx * vx + vy * vy + vz * vz
        if magnitude_sq <= 0.0:
            return (0.0, 1.0, 0.0)
        inv_mag = (magnitude_sq) ** -0.5
        return (vx * inv_mag, vy * inv_mag, vz * inv_mag)

    def _enforce_dead_zones(
        self, wheel: Wheel, head_volume: float, rod_volume: float
    ) -> Tuple[float, float]:
        head_limit = (
            self._max_head_volume.get(wheel, 0.0) * self._dead_zone_head_fraction
        )
        rod_limit = self._max_rod_volume.get(wheel, 0.0) * self._dead_zone_rod_fraction

        if head_limit > 0.0:
            head_volume = max(head_volume, head_limit)
        if rod_limit > 0.0:
            rod_volume = max(rod_volume, rod_limit)

        return head_volume, rod_volume

    def update(
        self,
        lever_angles: Mapping[Wheel, float],
        master_isolation_open: bool,
        thermo_mode: ThermoMode,
    ) -> PneumaticUpdate:
        """Synchronise structural model with lever angles and compute forces."""

        # ``thermo_mode`` is kept for API compatibility with the legacy
        # implementation; gas thermodynamics are resolved within
        # :func:`src.runtime.steps.update_gas_state`.
        _ = thermo_mode

        if lever_angles:
            self._structure.update_system_from_lever_angles(lever_angles)

        # Master isolation valve state is stored on the gas network.  Equalise
        # pressures instantly when the valve opens to match the behaviour in the
        # reference algorithms.
        self._gas_network.master_isolation_open = bool(master_isolation_open)
        if master_isolation_open:
            self._gas_network.enforce_master_isolation(dt=0.0)

        chamber_volumes: Dict[Wheel, Tuple[float, float]] = {}
        piston_positions: Dict[Wheel, float] = {}
        wheel_forces: Dict[Wheel, float] = {}
        axis_directions: Dict[Wheel, Tuple[float, float, float]] = {}
        pressures: Dict[Wheel, Tuple[float, float]] = {}

        left_force = 0.0
        right_force = 0.0

        for wheel, cylinder in self.cylinders.items():
            head_volume = cylinder.vol_head()
            rod_volume = cylinder.vol_rod()
            head_volume, rod_volume = self._enforce_dead_zones(
                wheel, head_volume, rod_volume
            )

            chamber_volumes[wheel] = (head_volume, rod_volume)
            piston_positions[wheel] = float(cylinder.x)

            line_head = self._line_for_endpoint(wheel, Port.HEAD)
            line_rod = self._line_for_endpoint(wheel, Port.ROD)

            head_pressure = (
                self._gas_network.lines[line_head].p
                if line_head in self._gas_network.lines
                else self._gas_network.tank.p
            )
            rod_pressure = (
                self._gas_network.lines[line_rod].p
                if line_rod in self._gas_network.lines
                else self._gas_network.tank.p
            )

            pressures[wheel] = (float(head_pressure), float(rod_pressure))

            geom = cylinder.spec.geometry
            area_head = geom.area_head(cylinder.spec.is_front)
            area_rod = geom.area_rod(cylinder.spec.is_front)
            pneumatic_force = compute_cylinder_force(
                head_pressure, rod_pressure, area_head, area_rod
            )
            wheel_forces[wheel] = pneumatic_force

            axis_tail = (0.0, geom.Y_tail, geom.Z_axle)
            rod_x, rod_y = cylinder.spec.lever_geom.rod_joint_pos(
                lever_angles.get(wheel, 0.0)
            )
            axis_tip = (0.0, rod_x, geom.Z_axle + rod_y)
            axis_vector = (
                axis_tip[0] - axis_tail[0],
                axis_tip[1] - axis_tail[1],
                axis_tip[2] - axis_tail[2],
            )
            axis_directions[wheel] = self._normalise(axis_vector)

            if wheel in (Wheel.LP, Wheel.LZ):
                left_force += pneumatic_force
            else:
                right_force += pneumatic_force

        update = PneumaticUpdate(
            left_force=float(left_force),
            right_force=float(right_force),
            wheel_forces=wheel_forces,
            piston_positions=piston_positions,
            chamber_volumes=chamber_volumes,
            axis_directions=axis_directions,
            pressures=pressures,
        )

        self._last_update = update
        return update


__all__ = ["PneumaticSystem", "PneumaticUpdate"]
