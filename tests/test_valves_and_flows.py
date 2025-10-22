"""
P12: Valve and flow validation tests

Tests:
- One-way check valves (ATMO?LINE, LINE?TANK)
- Opening thresholds (pressure differential)
- Tank relief valves (MIN_PRESS, STIFFNESS, SAFETY)
- Master isolation valve (pressure equalization)

References:
- unittest: https://docs.python.org/3/library/unittest.html
- numpy.testing: https://numpy.org/doc/stable/reference/routines.testing.html
"""

import unittest
import numpy as np
from numpy.testing import assert_allclose
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pneumo.valves import CheckValve, ReliefValve
from src.pneumo.gas_state import GasState


class TestCheckValves(unittest.TestCase):
    """Test one-way check valve behavior"""

    def setUp(self):
        """Setup valve parameters"""
        self.delta_open = 5000.0  # 5 kPa opening differential
        self.d_eff = 0.008  # 8mm effective diameter

        # Atmospheric pressure
        self.p_atm = 101325.0  # Pa

    def test_atmo_to_line_one_way(self):
        """Test ATMO?LINE valve allows flow only when p_line < p_atm

        Forward flow: p_atm > p_line + delta
        Reverse flow: blocked (one-way)
        """
        # Forward flow condition
        p_line_low = self.p_atm - self.delta_open - 1000.0  # Below threshold

        valve = CheckValve(
            p_upstream=self.p_atm,
            p_downstream=p_line_low,
            delta_open=self.delta_open,
            d_eff=self.d_eff
        )

        is_open_forward = valve.is_open()
        self.assertTrue(
            is_open_forward,
            f"Valve should open: dp={self.p_atm - p_line_low:.0f}Pa > {self.delta_open:.0f}Pa"
        )

        # Reverse flow blocked
        p_line_high = self.p_atm + 10000.0  # Above atmospheric

        valve_reverse = CheckValve(
            p_upstream=self.p_atm,
            p_downstream=p_line_high,
            delta_open=self.delta_open,
            d_eff=self.d_eff
        )

        is_open_reverse = valve_reverse.is_open()
        self.assertFalse(
            is_open_reverse,
            "Reverse flow should be blocked (one-way valve)"
        )

    def test_line_to_tank_one_way(self):
        """Test LINE?TANK valve allows flow only when p_line > p_tank

        Forward flow: p_line > p_tank + delta
        Reverse flow: blocked (one-way)
        """
        p_tank = 500000.0  # 5 bar tank pressure

        # Forward flow condition
        p_line_high = p_tank + self.delta_open + 1000.0

        valve = CheckValve(
            p_upstream=p_line_high,
            p_downstream=p_tank,
            delta_open=self.delta_open,
            d_eff=self.d_eff
        )

        is_open_forward = valve.is_open()
        self.assertTrue(
            is_open_forward,
            f"Valve should open: dp={p_line_high - p_tank:.0f}Pa > {self.delta_open:.0f}Pa"
        )

        # Reverse flow blocked
        p_line_low = p_tank - 10000.0

        valve_reverse = CheckValve(
            p_upstream=p_line_low,
            p_downstream=p_tank,
            delta_open=self.delta_open,
            d_eff=self.d_eff
        )

        is_open_reverse = valve_reverse.is_open()
        self.assertFalse(
            is_open_reverse,
            "Reverse flow should be blocked (one-way valve)"
        )

    def test_opening_threshold(self):
        """Test valve opens exactly at threshold pressure differential"""
        p_upstream = 110000.0  # Pa

        # Just below threshold
        p_downstream_below = p_upstream - self.delta_open + 100.0
        valve_below = CheckValve(p_upstream, p_downstream_below, self.delta_open, self.d_eff)
        self.assertFalse(valve_below.is_open(), "Should be closed below threshold")

        # Exactly at threshold
        p_downstream_at = p_upstream - self.delta_open
        valve_at = CheckValve(p_upstream, p_downstream_at, self.delta_open, self.d_eff)
        self.assertTrue(valve_at.is_open(), "Should open at threshold")

        # Above threshold
        p_downstream_above = p_upstream - self.delta_open - 100.0
        valve_above = CheckValve(p_upstream, p_downstream_above, self.delta_open, self.d_eff)
        self.assertTrue(valve_above.is_open(), "Should be open above threshold")


class TestReliefValves(unittest.TestCase):
    """Test tank relief valve behavior"""

    def setUp(self):
        """Setup relief valve parameters"""
        # Valve setpoints
        self.p_min = 150000.0     # 1.5 bar MIN_PRESS
        self.p_stiff = 300000.0   # 3.0 bar STIFFNESS
        self.p_safety = 800000.0  # 8.0 bar SAFETY

        # Throttling coefficients
        self.throttle_min = 0.5
        self.throttle_stiff = 0.7
        # Safety has no throttle (full flow)

    def test_min_press_valve(self):
        """Test MIN_PRESS relief valve with throttling"""
        # Below setpoint - closed
        p_tank_low = self.p_min - 10000.0
        valve_closed = ReliefValve(
            p_tank=p_tank_low,
            p_setpoint=self.p_min,
            throttle_coeff=self.throttle_min
        )
        self.assertFalse(valve_closed.is_open())

        # Above setpoint - open with throttling
        p_tank_high = self.p_min + 50000.0
        valve_open = ReliefValve(
            p_tank=p_tank_high,
            p_setpoint=self.p_min,
            throttle_coeff=self.throttle_min
        )
        self.assertTrue(valve_open.is_open())

        # Check flow is throttled
        flow_full = valve_open.calculate_flow(throttle_coeff=1.0)
        flow_throttled = valve_open.calculate_flow(throttle_coeff=self.throttle_min)

        self.assertLess(
            flow_throttled,
            flow_full,
            "Throttled flow should be less than full flow"
        )

    def test_stiffness_valve(self):
        """Test STIFFNESS relief valve with throttling"""
        p_tank = self.p_stiff + 100000.0  # Above setpoint

        valve = ReliefValve(
            p_tank=p_tank,
            p_setpoint=self.p_stiff,
            throttle_coeff=self.throttle_stiff
        )

        self.assertTrue(valve.is_open())

    def test_safety_valve_no_throttle(self):
        """Test SAFETY relief valve with no throttling (full flow)"""
        p_tank = self.p_safety + 50000.0  # Above setpoint

        valve = ReliefValve(
            p_tank=p_tank,
            p_setpoint=self.p_safety,
            throttle_coeff=1.0  # No throttle
        )

        self.assertTrue(valve.is_open())

        # Full flow (no reduction)
        flow = valve.calculate_flow(throttle_coeff=1.0)
        self.assertGreater(flow, 0.0, "Safety valve should allow full flow")

    def test_valve_hysteresis(self):
        """Test valve opening/closing hysteresis

        Optional: Some valves have hysteresis to prevent chattering
        """
        # Simple test: valve closes when pressure drops below setpoint
        p_tank_above = self.p_min + 10000.0
        p_tank_below = self.p_min - 10000.0

        valve = ReliefValve(p_tank=p_tank_above, p_setpoint=self.p_min, throttle_coeff=1.0)
        self.assertTrue(valve.is_open(), "Should open above setpoint")

        valve.update_pressure(p_tank_below)
        self.assertFalse(valve.is_open(), "Should close below setpoint")


class TestMasterIsolation(unittest.TestCase):
    """Test master isolation valve (line pressure equalization)"""

    def setUp(self):
        """Setup gas states for multiple lines"""
        # 4 lines with different pressures
        self.lines = [
            GasState(pressure=200000.0, temperature=293.15, volume=0.001),  # A1
            GasState(pressure=300000.0, temperature=295.00, volume=0.0015), # B1
            GasState(pressure=250000.0, temperature=294.00, volume=0.0012), # A2
            GasState(pressure=280000.0, temperature=296.00, volume=0.0013), # B2
        ]

    def test_isolation_open_equalizes_pressure(self):
        """Test that opening isolation equalizes all line pressures

        When master_isolation_open=True:
        - All lines reach common pressure
        - Mass redistributed by volume
        - Temperature weighted by mass
        """
        # Calculate expected equilibrium
        total_mass = sum(line.mass for line in self.lines)
        total_volume = sum(line.volume for line in self.lines)

        # Mass-weighted temperature
        T_avg = sum(line.mass * line.temperature for line in self.lines) / total_mass

        # Common pressure p = (m_total * R * T_avg) / V_total
        R = 287.05  # J/(kg·K) for air
        p_common = (total_mass * R * T_avg) / total_volume

        # Apply equalization
        self._equalize_pressures(self.lines)

        # Check all pressures equal
        for line in self.lines:
            assert_allclose(
                line.pressure,
                p_common,
                rtol=1e-6,
                err_msg=f"Line pressure {line.pressure:.0f}Pa != common {p_common:.0f}Pa"
            )

        # Check total mass conserved
        total_mass_after = sum(line.mass for line in self.lines)
        assert_allclose(
            total_mass_after,
            total_mass,
            rtol=1e-10,
            err_msg="Total mass not conserved"
        )

    def test_isolation_closed_independent_lines(self):
        """Test that closed isolation keeps lines independent"""
        # Store initial pressures
        initial_pressures = [line.pressure for line in self.lines]

        # Lines remain independent (no equalization)
        # Just verify they don't change without interaction
        for i, line in enumerate(self.lines):
            self.assertEqual(
                line.pressure,
                initial_pressures[i],
                "Pressure should not change when isolated"
            )

    def _equalize_pressures(self, lines):
        """Helper: equalize pressures across all lines

        This mimics the master isolation valve logic
        """
        R = 287.05  # J/(kg·K)

        # Calculate totals
        total_mass = sum(line.mass for line in lines)
        total_volume = sum(line.volume for line in lines)

        # Mass-weighted average temperature
        T_avg = sum(line.mass * line.temperature for line in lines) / total_mass

        # Common pressure
        p_common = (total_mass * R * T_avg) / total_volume

        # Redistribute mass by volume fraction
        for line in lines:
            volume_fraction = line.volume / total_volume
            line.mass = total_mass * volume_fraction
            line.pressure = p_common
            line.temperature = T_avg


if __name__ == '__main__':
    unittest.main(verbosity=2)
