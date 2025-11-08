"""Utility helpers for deterministic integration simulations."""

from __future__ import annotations

import json
import logging
import math
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterator, Mapping

from src.core.settings_manager import (
    create_default_gas_network,
    create_default_system_configuration,
)
from src.common.units import DEG2RAD
from src.pneumo.enums import ThermoMode, Wheel
from src.pneumo.network import GasNetwork
from src.pneumo.sim_time import advance_gas
from src.pneumo.system import PneumaticSystem, create_standard_diagonal_system
from src.road.engine import RoadInput, create_road_input_from_preset
from src.road.scenarios import get_preset_by_name
from src.road.types import CorrelationSpec


def _clone_correlation(base: CorrelationSpec, seed: int | None) -> CorrelationSpec:
    """Return a correlation spec with the provided seed."""

    return CorrelationSpec(
        rho_LR=float(base.rho_LR),
        method=str(base.method),
        seed=seed if seed is not None else base.seed,
    )


@dataclass
class SimulationContext:
    """Bundle of simulation primitives reused across integration tests."""

    system: PneumaticSystem
    network: object
    road_input: RoadInput

    def snapshot_pressures(self) -> dict[str, float]:
        """Return current line pressures keyed by line name."""

        lines = self.network.lines
        return {line.name: float(state.p) for line, state in lines.items()}

    def snapshot_volumes(self) -> dict[str, float]:
        """Return current line volumes keyed by line name."""

        volumes = self.network.compute_line_volumes()
        return {line.name: float(volume) for line, volume in volumes.items()}


def _create_gas_network(system: PneumaticSystem) -> GasNetwork:
    """Return a gas network initialised from the settings manager."""

    network = create_default_gas_network(system)
    network.master_isolation_open = False
    return network


def create_simulation_context(
    *,
    road_preset: str = "test_sine",
    seed: int | None = 1234,
    duration: float = 5.0,
) -> SimulationContext:
    """Create a deterministic simulation context for integration tests."""

    config = create_default_system_configuration()
    system = create_standard_diagonal_system(
        cylinder_specs=config["cylinder_specs"],
        line_configs=config["line_configs"],
        receiver=config["receiver"],
        master_isolation_open=config["master_isolation_open"],
    )
    network = _create_gas_network(system)

    preset = get_preset_by_name(road_preset)
    if preset is None:
        raise ValueError(f"Unknown road preset '{road_preset}'")
    correlation = _clone_correlation(preset.correlation, seed)
    road_input = create_road_input_from_preset(
        road_preset,
        correlation=correlation,
        duration=duration,
    )
    road_input.configure(road_input.config, system=system)
    road_input.prime(duration=duration)

    return SimulationContext(system=system, network=network, road_input=road_input)


def _aggregate_mass(network) -> float:
    """Return total gas mass across tank and lines."""

    total = float(network.tank.m)
    for line_state in network.lines.values():
        total += float(line_state.m)
    return total


def apply_body_roll(
    context: SimulationContext,
    *,
    angle_deg: float = 3.0,
    thermo_mode: ThermoMode = ThermoMode.ISOTHERMAL,
    logger: logging.Logger | None = None,
) -> dict[str, Mapping[str, float]]:
    """Apply a static body roll and return pressure/volume deltas."""

    network = context.network
    initial_pressures = context.snapshot_pressures()
    initial_volumes = context.snapshot_volumes()

    angle_rad = float(angle_deg) * DEG2RAD
    roll_angles = {
        Wheel.LP: angle_rad,
        Wheel.LZ: angle_rad,
        Wheel.PP: -angle_rad,
        Wheel.PZ: -angle_rad,
    }
    context.system.update_system_from_lever_angles(roll_angles)

    if logger:
        logger.info(
            "Applying body roll of %.1f° -> thermo_mode=%s",
            angle_deg,
            thermo_mode.value,
        )

    network.update_pressures_due_to_volume(thermo_mode)

    final_pressures = context.snapshot_pressures()
    final_volumes = context.snapshot_volumes()

    def _delta(
        after: Mapping[str, float], before: Mapping[str, float]
    ) -> dict[str, float]:
        return {key: float(after[key]) - float(before[key]) for key in before.keys()}

    return {
        "initial_pressure": initial_pressures,
        "final_pressure": final_pressures,
        "pressure_delta": _delta(final_pressures, initial_pressures),
        "initial_volume": initial_volumes,
        "final_volume": final_volumes,
        "volume_delta": _delta(final_volumes, initial_volumes),
    }


def run_oscillation_cycle(
    context: SimulationContext,
    *,
    amplitude_deg: float = 2.5,
    frequency_hz: float = 1.2,
    cycles: float = 2.0,
    dt: float = 0.01,
    thermo_mode: ThermoMode = ThermoMode.ISOTHERMAL,
    logger: logging.Logger | None = None,
) -> dict[str, object]:
    """Drive the stabiliser through oscillations and record metrics."""

    network = context.network
    total_time = cycles / max(frequency_hz, 1e-6)
    steps = max(1, int(total_time / dt))
    angle_rad = float(amplitude_deg) * DEG2RAD

    series: dict[str, list[float]] = defaultdict(list)
    masses: list[float] = []

    if logger:
        logger.info(
            "Running oscillation: amplitude=%.2f°, freq=%.2fHz, steps=%d, thermo=%s",
            amplitude_deg,
            frequency_hz,
            steps,
            thermo_mode.value,
        )

    time_cursor = 0.0
    for _ in range(steps):
        angle = angle_rad * math.sin(2.0 * math.pi * frequency_hz * time_cursor)
        roll_angles = {
            Wheel.LP: angle,
            Wheel.LZ: angle,
            Wheel.PP: -angle,
            Wheel.PZ: -angle,
        }
        context.system.update_system_from_lever_angles(roll_angles)
        advance_gas(dt, context.system, network, thermo_mode, logger)

        for line, state in network.lines.items():
            series[line.name].append(float(state.p))
        masses.append(_aggregate_mass(network))
        time_cursor += dt

    pressure_range = {
        line: max(values) - min(values) if values else 0.0
        for line, values in series.items()
    }

    return {
        "pressure_series": {line: list(values) for line, values in series.items()},
        "pressure_range": pressure_range,
        "max_pressure_range": max(pressure_range.values() or [0.0]),
        "mass_range": (max(masses) - min(masses)) if masses else 0.0,
    }


def compute_road_metrics(road_input: RoadInput) -> dict[str, object]:
    """Extract deterministic metrics from a primed road input."""

    info = road_input.get_info()
    stats = info.get("profile_stats", {})

    profile_stats = {
        wheel: {
            "min": float(payload["min"]),
            "max": float(payload["max"]),
            "rms": float(payload["rms"]),
            "std": float(payload["std"]),
        }
        for wheel, payload in stats.items()
    }

    return {
        "axle_delay": float(info.get("axle_delay", 0.0)),
        "duration": float(info.get("duration", 0.0)),
        "velocity": float(info.get("velocity", 0.0)),
        "profile_stats": profile_stats,
    }


def _serialise_metrics(payload: object) -> object:
    """Convert metrics payload to JSON friendly primitives."""

    if isinstance(payload, dict):
        return {str(key): _serialise_metrics(value) for key, value in payload.items()}
    if isinstance(payload, (list, tuple)):
        return [_serialise_metrics(value) for value in payload]
    if isinstance(payload, (int, float)):
        return float(payload)
    return payload


def store_metrics(metrics: Mapping[str, object], target: Path) -> None:
    """Persist metrics dictionary as JSON."""

    target.write_text(
        json.dumps(_serialise_metrics(metrics), indent=2, sort_keys=True),
        encoding="utf-8",
    )


@contextmanager
def simulation_logger(
    directory: Path, stem: str
) -> Iterator[tuple[logging.Logger, Path]]:
    """Context manager yielding a configured logger that writes to ``stem``."""

    directory.mkdir(parents=True, exist_ok=True)
    log_path = directory / f"{stem}.log"
    logger = logging.getLogger(f"tests.integration.{stem}")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    try:
        yield logger, log_path
    finally:
        logger.removeHandler(handler)
        handler.close()
