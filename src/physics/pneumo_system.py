"""High-level pneumatic system runtime helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Tuple

from src.pneumo.enums import Line, Port, ThermoMode, Wheel
from src.pneumo.system import PneumaticSystem as StructuralPneumaticSystem
from src.pneumo.network import GasNetwork


@dataclass
class PneumaticUpdate:
    """Aggregated pneumatic state computed for the current step."""

    left_force: float
    right_force: float
    piston_positions: Dict[Wheel, float]
    chamber_volumes: Dict[Wheel, Tuple[float, float]]


class PneumaticSystem:
    """Runtime pneumatic helpers bridging structural model and gas network."""

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
    def _max_head_volume(self, wheel: Wheel) -> float:
        cylinder = self.cylinders[wheel]
        geom = cylinder.spec.geometry
        half_travel = geom.L_travel_max / 2.0
        return cylinder.vol_head(-half_travel)

    def _max_rod_volume(self, wheel: Wheel) -> float:
        cylinder = self.cylinders[wheel]
        geom = cylinder.spec.geometry
        half_travel = geom.L_travel_max / 2.0
        return cylinder.vol_rod(half_travel)

    def _line_for_endpoint(self, wheel: Wheel, port: Port) -> Line | None:
        for line_name, line in self.lines.items():
            for endpoint_wheel, endpoint_port in line.endpoints:
                if endpoint_wheel == wheel and endpoint_port == port:
                    return line_name
        return None

    def update(
        self,
        lever_angles: Mapping[Wheel, float],
        master_isolation_open: bool,
        thermo_mode: ThermoMode,
    ) -> PneumaticUpdate:
        """Synchronise structural model with lever angles and compute forces."""

        if lever_angles:
            self._structure.update_system_from_lever_angles(lever_angles)

        self._gas_network.master_isolation_open = master_isolation_open

        chamber_volumes: Dict[Wheel, Tuple[float, float]] = {}
        piston_positions: Dict[Wheel, float] = {}

        for wheel, cylinder in self.cylinders.items():
            head_volume = cylinder.vol_head()
            rod_volume = cylinder.vol_rod()

            head_limit = self._dead_zone_head_fraction * self._max_head_volume(wheel)
            rod_limit = self._dead_zone_rod_fraction * self._max_rod_volume(wheel)

            if head_limit > 0.0:
                head_volume = max(head_volume, head_limit)
            if rod_limit > 0.0:
                rod_volume = max(rod_volume, rod_limit)

            chamber_volumes[wheel] = (head_volume, rod_volume)
            piston_positions[wheel] = float(cylinder.x)

        left_force = 0.0
        right_force = 0.0

        for wheel, (head_volume, rod_volume) in chamber_volumes.items():
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

            geom = self.cylinders[wheel].spec.geometry
            area_head = geom.area_head(self.cylinders[wheel].spec.is_front)
            area_rod = geom.area_rod(self.cylinders[wheel].spec.is_front)
            pneumatic_force = head_pressure * area_head - rod_pressure * area_rod

            if wheel in (Wheel.LP, Wheel.LZ):
                left_force += pneumatic_force
            else:
                right_force += pneumatic_force

        return PneumaticUpdate(
            left_force=float(left_force),
            right_force=float(right_force),
            piston_positions=piston_positions,
            chamber_volumes=chamber_volumes,
        )


__all__ = ["PneumaticSystem", "PneumaticUpdate"]
