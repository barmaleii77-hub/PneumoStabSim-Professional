"""High-level pneumatic system solver for simulation updates."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Mapping

from src.pneumo.enums import Line, Port, ReceiverVolumeMode, ThermoMode, Wheel
from src.pneumo.gas_state import apply_instant_volume_change
from src.pneumo.network import GasNetwork
from src.pneumo.system import PneumaticSystem as StructuralSystem


@dataclass
class PneumaticUpdateResult:
    """Result bundle produced after synchronising the pneumatic network."""

    corrected_volumes: Dict[Line, float]
    line_pressures: Dict[Line, float]
    wheel_forces: Dict[Wheel, float]
    piston_positions: Dict[Wheel, float]
    tank_pressure: float
    tank_volume: float
    left_force: float
    right_force: float


class PneumaticSystem:
    """Wrapper around the structural pneumatic system and gas network solver."""

    def __init__(
        self,
        structure: StructuralSystem,
        gas_network: GasNetwork,
        *,
        dead_zone_fraction: float = 0.01,
        dead_zone_head: float | None = None,
        dead_zone_rod: float | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._structure = structure
        self.gas_network = gas_network
        self.dead_zone_fraction = max(float(dead_zone_fraction), 0.0)
        self.logger = logger or logging.getLogger(__name__)

        self._dead_zone_head = (
            dead_zone_head if dead_zone_head and dead_zone_head > 0 else None
        )
        self._dead_zone_rod = (
            dead_zone_rod if dead_zone_rod and dead_zone_rod > 0 else None
        )

        # Expose attributes used by legacy code paths
        self.cylinders = self._structure.cylinders
        self.lines = self._structure.lines
        self.receiver = self._structure.receiver
        self.master_isolation_open = self._structure.master_isolation_open
        self.tank = self.gas_network.tank

        self._max_chamber_volume: Dict[Wheel, Dict[Port, float]] = {}
        self._precompute_max_volumes()

    def _precompute_max_volumes(self) -> None:
        volumes: Dict[Wheel, Dict[Port, float]] = {}
        for wheel, cylinder in self.cylinders.items():
            geom = cylinder.spec.geometry
            half_travel = geom.L_travel_max / 2.0
            head_volume = float(cylinder.vol_head(-half_travel))
            rod_volume = float(cylinder.vol_rod(half_travel))
            volumes[wheel] = {Port.HEAD: head_volume, Port.ROD: rod_volume}
        self._max_chamber_volume = volumes

    def get_line_volumes(self) -> Mapping[Line, Mapping[str, object]]:
        """Proxy to the structural system helper used in legacy code paths."""

        return self._structure.get_line_volumes()

    def update_system_from_lever_angles(self, angles: Mapping[Wheel, float]) -> None:
        """Delegate lever update to the underlying structural model."""

        self._structure.update_system_from_lever_angles(angles)

    # ------------------------------------------------------------------ solver
    def solve_gas_state(
        self,
        *,
        thermo_mode: ThermoMode,
        master_isolation_open: bool,
        receiver_volume: float,
        receiver_mode: ReceiverVolumeMode,
        dt: float,
        logger: logging.Logger | None = None,
    ) -> PneumaticUpdateResult:
        """Synchronise gas network with the current mechanical configuration."""

        active_logger = logger or self.logger
        corrected_volumes: Dict[Line, float] = {}

        for line_name, line in self.lines.items():
            total_volume = 0.0
            for wheel, port in line.endpoints:
                cylinder = self.cylinders[wheel]
                if port == Port.HEAD:
                    raw_volume = float(cylinder.vol_head())
                    penetration = float(cylinder.penetration_head)
                    max_volume = self._max_chamber_volume[wheel][Port.HEAD]
                    area = cylinder.spec.geometry.area_head(cylinder.spec.is_front)
                else:
                    raw_volume = float(cylinder.vol_rod())
                    penetration = float(cylinder.penetration_rod)
                    max_volume = self._max_chamber_volume[wheel][Port.ROD]
                    area = cylinder.spec.geometry.area_rod(cylinder.spec.is_front)

                if port == Port.HEAD:
                    absolute_min = self._dead_zone_head
                else:
                    absolute_min = self._dead_zone_rod
                min_allowed = max(
                    self.dead_zone_fraction * max_volume,
                    absolute_min if absolute_min is not None else 0.0,
                    1e-9,
                )
                chamber_volume = max(raw_volume, min_allowed)
                if penetration > 0.0:
                    chamber_volume = max(
                        chamber_volume - area * penetration, min_allowed
                    )
                total_volume += chamber_volume

            corrected_volumes[line_name] = max(total_volume, 1e-9)

        self.master_isolation_open = master_isolation_open
        self.gas_network.master_isolation_open = master_isolation_open

        self.gas_network.update_pressures_with_explicit_volumes(
            corrected_volumes, thermo_mode
        )

        self.gas_network.tank.mode = receiver_mode
        if abs(self.gas_network.tank.V - receiver_volume) > 1e-9:
            apply_instant_volume_change(
                self.gas_network.tank,
                receiver_volume,
                gamma=self.gas_network.tank.gamma,
            )

        self.gas_network.apply_valves_and_flows(dt, active_logger)
        self.gas_network.enforce_master_isolation(active_logger, dt=dt)

        line_pressures: Dict[Line, float] = {
            line_name: float(gas_state.p)
            for line_name, gas_state in self.gas_network.lines.items()
        }

        wheel_forces: Dict[Wheel, float] = {}
        piston_positions: Dict[Wheel, float] = {}
        for wheel, cylinder in self.cylinders.items():
            head_pressure = self._get_line_pressure(wheel, Port.HEAD)
            rod_pressure = self._get_line_pressure(wheel, Port.ROD)
            geom = cylinder.spec.geometry
            area_head = geom.area_head(cylinder.spec.is_front)
            area_rod = geom.area_rod(cylinder.spec.is_front)
            wheel_forces[wheel] = head_pressure * area_head - rod_pressure * area_rod
            piston_positions[wheel] = float(cylinder.x)

        left_force = wheel_forces.get(Wheel.LP, 0.0) + wheel_forces.get(Wheel.LZ, 0.0)
        right_force = wheel_forces.get(Wheel.PP, 0.0) + wheel_forces.get(Wheel.PZ, 0.0)

        return PneumaticUpdateResult(
            corrected_volumes=corrected_volumes,
            line_pressures=line_pressures,
            wheel_forces=wheel_forces,
            piston_positions=piston_positions,
            tank_pressure=float(self.gas_network.tank.p),
            tank_volume=float(self.gas_network.tank.V),
            left_force=left_force,
            right_force=right_force,
        )

    def _get_line_pressure(self, wheel: Wheel, port: Port) -> float:
        for line_name, line in self.lines.items():
            for endpoint_wheel, endpoint_port in line.endpoints:
                if endpoint_wheel == wheel and endpoint_port == port:
                    return float(self.gas_network.lines[line_name].p)
        return float(self.gas_network.tank.p)
