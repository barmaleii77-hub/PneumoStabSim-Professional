"""High-level pneumatic system wrapper used by the physics worker.

The historical simulation pipeline exposed the low-level
``src.pneumo.system.PneumaticSystem`` object directly to the physics worker
and individual step helpers.  This module introduces a thin orchestration
layer that keeps the validated pneumatic model but augments it with
headless-friendly update utilities, dead-zone handling and force
aggregation.  The wrapper deliberately mirrors the original API so that
existing callers that expect ``cylinders`` or ``lines`` dictionaries keep
working while newer code can rely on the richer :meth:`update` result.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Tuple

from src.common.units import PA_ATM, to_gauge_pressure
from src.pneumo.enums import Line, Port, ReceiverVolumeMode, ThermoMode, Wheel
from src.pneumo.gas_state import apply_instant_volume_change
from src.pneumo.network import GasNetwork
from src.pneumo.system import PneumaticSystem as CorePneumaticSystem


@dataclass
class PneumaticUpdate:
    """Result of a pneumatic update step."""

    wheel_forces: Dict[Wheel, float]
    piston_positions: Dict[Wheel, float]
    line_states: Dict[Line, Dict[str, float]]
    tank_state: Dict[str, float]
    flows: Dict[Line, Dict[str, float]]
    relief_flows: Dict[str, float]


class PneumaticSystem:
    """Facade around the core pneumatic system and gas network."""

    def __init__(
        self,
        system: CorePneumaticSystem,
        gas_network: GasNetwork,
        *,
        dead_zone_head: float = 0.0,
        dead_zone_rod: float = 0.0,
    ) -> None:
        self._core = system
        self.gas_network = gas_network
        self.dead_zone_head = max(0.0, float(dead_zone_head))
        self.dead_zone_rod = max(0.0, float(dead_zone_rod))

        self._endpoint_lookup: Dict[Tuple[Wheel, Port], Line] = {}
        self._volume_limits: Dict[Tuple[Wheel, Port], Dict[str, float]] = {}
        self._piston_areas: Dict[Tuple[Wheel, Port], float] = {}

        self._rebuild_endpoint_lookup()
        self._compute_volume_limits()

    # ------------------------------------------------------------------
    # Compatibility shim
    # ------------------------------------------------------------------
    def __getattr__(self, name: str):  # pragma: no cover - thin delegation
        return getattr(self._core, name)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _rebuild_endpoint_lookup(self) -> None:
        for line_name, line in self._core.lines.items():
            for wheel, port in line.endpoints:
                self._endpoint_lookup[(wheel, port)] = line_name

    def _compute_volume_limits(self) -> None:
        for wheel, cylinder in self._core.cylinders.items():
            geom = cylinder.spec.geometry
            half_travel = geom.L_travel_max / 2.0

            head_volumes = [
                float(cylinder.vol_head(x=-half_travel)),
                float(cylinder.vol_head(x=half_travel)),
            ]
            rod_volumes = [
                float(cylinder.vol_rod(x=-half_travel)),
                float(cylinder.vol_rod(x=half_travel)),
            ]

            max_head = max(head_volumes)
            max_rod = max(rod_volumes)

            default_min_head = geom.min_volume_head(cylinder.spec.is_front)
            default_min_rod = geom.min_volume_rod(cylinder.spec.is_front)

            ratio_head = (self.dead_zone_head / max_head) if max_head > 0 else 0.0
            ratio_rod = (self.dead_zone_rod / max_rod) if max_rod > 0 else 0.0

            head_limit = max(
                default_min_head,
                min(self.dead_zone_head, max_head) if self.dead_zone_head > 0 else 0.0,
                max_head * max(0.0, min(1.0, ratio_head)),
            )
            rod_limit = max(
                default_min_rod,
                min(self.dead_zone_rod, max_rod) if self.dead_zone_rod > 0 else 0.0,
                max_rod * max(0.0, min(1.0, ratio_rod)),
            )

            self._volume_limits[(wheel, Port.HEAD)] = {
                "min": min(head_limit, max_head),
                "max": max_head,
            }
            self._volume_limits[(wheel, Port.ROD)] = {
                "min": min(rod_limit, max_rod),
                "max": max_rod,
            }

            self._piston_areas[(wheel, Port.HEAD)] = geom.area_head(
                cylinder.spec.is_front
            )
            self._piston_areas[(wheel, Port.ROD)] = geom.area_rod(
                cylinder.spec.is_front
            )

    def _normalise_contribution(
        self, wheel: Wheel, port: Port, raw_volume: float
    ) -> float:
        limits = self._volume_limits.get((wheel, port))
        if not limits:
            return float(raw_volume)
        min_volume = limits.get("min", 0.0)
        return max(float(raw_volume), min_volume)

    def _compute_penetration_volume(self, line_name: Line) -> float:
        penetration_volume = 0.0
        line = self._core.lines[line_name]
        for wheel, port in line.endpoints:
            cylinder = self._core.cylinders[wheel]
            geom = cylinder.spec.geometry
            if port == Port.HEAD and cylinder.penetration_head > 0.0:
                penetration_volume += (
                    geom.area_head(cylinder.spec.is_front) * cylinder.penetration_head
                )
            elif port == Port.ROD and cylinder.penetration_rod > 0.0:
                penetration_volume += (
                    geom.area_rod(cylinder.spec.is_front) * cylinder.penetration_rod
                )
        return penetration_volume

    def _resolve_endpoint(self, payload: Mapping[str, object]) -> Tuple[Wheel, Port]:
        wheel_value = payload.get("wheel")
        port_value = payload.get("port")

        wheel = (
            wheel_value if isinstance(wheel_value, Wheel) else Wheel(str(wheel_value))
        )
        port = port_value if isinstance(port_value, Port) else Port(str(port_value))
        return wheel, port

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def update(
        self,
        *,
        lever_angles: Optional[Mapping[Wheel, float]] = None,
        master_isolation_open: bool,
        thermo_mode: ThermoMode,
        receiver_volume: float,
        receiver_mode: ReceiverVolumeMode,
        dt: float,
        logger: Optional[logging.Logger] = None,
    ) -> PneumaticUpdate:
        """Update the gas network and return derived forces."""

        if lever_angles:
            self._core.update_system_from_lever_angles(dict(lever_angles))

        self._core.master_isolation_open = bool(master_isolation_open)
        self.gas_network.master_isolation_open = bool(master_isolation_open)

        raw_volumes = self._core.get_line_volumes()
        corrected_volumes: Dict[Line, float] = {}
        endpoint_cache: Dict[Line, Iterable[Mapping[str, object]]] = {}

        for line_name, volume_info in raw_volumes.items():
            endpoints = volume_info.get("endpoints", [])
            endpoint_cache[line_name] = endpoints

            adjusted_sum = 0.0
            for endpoint in endpoints:
                wheel, port = self._resolve_endpoint(endpoint)
                adjusted_sum += self._normalise_contribution(
                    wheel, port, float(endpoint.get("volume", 0.0))
                )

            penetration = self._compute_penetration_volume(line_name)
            corrected_volumes[line_name] = max(adjusted_sum - penetration, 1e-9)

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

        flow_data = self.gas_network.apply_valves_and_flows(dt, logger)
        self.gas_network.enforce_master_isolation(logger, dt=dt)

        wheel_forces: Dict[Wheel, float] = {}
        piston_positions: Dict[Wheel, float] = {}
        line_states: Dict[Line, Dict[str, float]] = {}
        flows: Dict[Line, Dict[str, float]] = {}

        for wheel, cylinder in self._core.cylinders.items():
            piston_positions[wheel] = float(cylinder.x)

            head_line = self._endpoint_lookup.get((wheel, Port.HEAD))
            rod_line = self._endpoint_lookup.get((wheel, Port.ROD))

            head_pressure = (
                self.gas_network.lines[head_line].p
                if head_line
                else self.gas_network.tank.p
            )
            rod_pressure = (
                self.gas_network.lines[rod_line].p
                if rod_line
                else self.gas_network.tank.p
            )

            area_head = self._piston_areas[(wheel, Port.HEAD)]
            area_rod = self._piston_areas[(wheel, Port.ROD)]

            head_gauge = to_gauge_pressure(head_pressure)
            rod_gauge = to_gauge_pressure(rod_pressure)

            wheel_forces[wheel] = head_gauge * area_head - rod_gauge * area_rod

        for line_name, gas_state in self.gas_network.lines.items():
            pneumo_line = self._core.lines[line_name]
            line_flow = flow_data.get("lines", {}).get(
                line_name, {"flow_atmo": 0.0, "flow_tank": 0.0, "flow_leak": 0.0}
            )

            line_states[line_name] = {
                "pressure": gas_state.p,
                "temperature": gas_state.T,
                "mass": gas_state.m,
                "volume": gas_state.V_curr,
                "cv_atmo_open": pneumo_line.cv_atmo.is_open(PA_ATM, gas_state.p),
                "cv_tank_open": pneumo_line.cv_tank.is_open(
                    gas_state.p, self.gas_network.tank.p
                ),
            }

            flows[line_name] = {
                "flow_atmo": float(line_flow.get("flow_atmo", 0.0)),
                "flow_tank": float(line_flow.get("flow_tank", 0.0)),
                "flow_leak": float(line_flow.get("flow_leak", 0.0)),
            }

        relief_flows = flow_data.get(
            "relief", {"flow_min": 0.0, "flow_stiff": 0.0, "flow_safety": 0.0}
        )
        tank = self.gas_network.tank
        tank_state = {
            "pressure": tank.p,
            "temperature": tank.T,
            "mass": tank.m,
            "volume": tank.V,
            "relief_min_open": bool(relief_flows.get("flow_min", 0.0) > 0.0),
            "relief_stiff_open": bool(relief_flows.get("flow_stiff", 0.0) > 0.0),
            "relief_safety_open": bool(relief_flows.get("flow_safety", 0.0) > 0.0),
            "flow_min": float(relief_flows.get("flow_min", 0.0)),
            "flow_stiff": float(relief_flows.get("flow_stiff", 0.0)),
            "flow_safety": float(relief_flows.get("flow_safety", 0.0)),
        }

        return PneumaticUpdate(
            wheel_forces=wheel_forces,
            piston_positions=piston_positions,
            line_states=line_states,
            tank_state=tank_state,
            flows=flows,
            relief_flows={k: float(v) for k, v in relief_flows.items()},
        )
