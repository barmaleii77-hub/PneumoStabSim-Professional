"""Valve boundary-condition tests covering hysteresis and flow delays."""

import math

from src.pneumo.valves import CheckValve, ReliefValve


def test_check_valve_hysteresis_delay(hysteretic_check_valve: CheckValve) -> None:
    """Simulate pressure sweeps to verify hysteresis keeps the valve open longer.

    The calibrated valve opens once Δp exceeds 1.5 kPa and should only close
    after the differential falls below 0.9 kPa. The sequence of pressure pairs
    therefore keeps the valve closed, then forces it open, holds it open above
    the closing threshold, and finally shuts it when Δp drops to 0.7 kPa.
    """

    valve = hysteretic_check_valve

    assert not valve.is_open(101_325.0, 101_000.0)
    assert valve.is_open(103_000.0, 101_000.0)
    assert valve.is_open(102_000.0, 101_000.0)
    assert not valve.is_open(101_700.0, 101_000.0)


def test_relief_valve_flow_and_hold(relief_valve_reference: ReliefValve) -> None:
    """Check relief valve open/close hysteresis and throttled flow estimation.

    The reference valve opens above 205 kPa and delivers throttled flow of
    0.02 × (p - 200 kPa) when active. It should remain open at 201 kPa due to the
    hysteresis band and finally reseal once tank pressure drops below 200 kPa.
    """

    valve = relief_valve_reference

    assert not valve.is_open(198_000.0)
    assert not valve.is_open(204_000.0)
    assert valve.is_open(206_000.0)

    flow = valve.calculate_flow()
    assert math.isclose(flow, 0.02 * (206_000.0 - 200_000.0))

    assert valve.is_open(201_000.0)
    assert not valve.is_open(199_000.0)
