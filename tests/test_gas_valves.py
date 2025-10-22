"""
Tests for gas valve behavior
"""

import unittest
from src.pneumo.valves import CheckValve, ReliefValve
from src.pneumo.enums import CheckValveKind, ReliefValveKind
from src.pneumo.flow import mass_flow_orifice, is_choked_flow
from src.common.units import PA_ATM, T_AMBIENT


class TestCheckValveBehavior(unittest.TestCase):
    """Test check valve opening/closing logic"""

    def setUp(self):
        """Setup test valves"""
        self.atmo_valve = CheckValve(
            kind=CheckValveKind.ATMO_TO_LINE,
            delta_open_min=5000.0,  # 5000 Pa
            d_eq=2.0e-3,  # 2mm
            hyst=200.0,
        )

        self.tank_valve = CheckValve(
            kind=CheckValveKind.LINE_TO_TANK,
            delta_open_min=10000.0,  # 10000 Pa
            d_eq=2.0e-3,  # 2mm
            hyst=200.0,
        )

    def test_atmo_to_line_opening(self):
        """Test ATMO_TO_LINE valve opens when line pressure drops"""
        p_atm = PA_ATM

        # Valve should open when p_line < p_atm - delta_open_min
        p_line_low = PA_ATM - 6000.0  # 6000 Pa below atmospheric
        self.assertTrue(self.atmo_valve.is_open(p_atm, p_line_low))

        # Valve should close when pressure difference is insufficient
        p_line_high = PA_ATM - 3000.0  # Only 3000 Pa below atmospheric
        self.assertFalse(self.atmo_valve.is_open(p_atm, p_line_high))

        # Valve should close when line pressure exceeds atmospheric
        p_line_above = PA_ATM + 1000.0
        self.assertFalse(self.atmo_valve.is_open(p_atm, p_line_above))

    def test_line_to_tank_opening(self):
        """Test LINE_TO_TANK valve opens when line pressure exceeds tank"""
        p_tank = PA_ATM

        # Valve should open when p_line > p_tank + delta_open_min
        p_line_high = PA_ATM + 12000.0  # 12000 Pa above tank
        self.assertTrue(self.tank_valve.is_open(p_line_high, p_tank))

        # Valve should close when pressure difference is insufficient
        p_line_low = PA_ATM + 5000.0  # Only 5000 Pa above tank
        self.assertFalse(self.tank_valve.is_open(p_line_low, p_tank))

        # Valve should close when line pressure is below tank
        p_line_below = PA_ATM - 1000.0
        self.assertFalse(self.tank_valve.is_open(p_line_below, p_tank))

    def test_valve_flow_rates(self):
        """Test mass flow rates through valves when open"""
        p_up = PA_ATM + 10000.0  # 10000 Pa above atmospheric
        p_down = PA_ATM
        T_up = T_AMBIENT
        T_down = T_AMBIENT
        d_eq = 2.0e-3

        # Calculate flow rate
        m_dot = mass_flow_orifice(p_up, T_up, p_down, T_down, d_eq)

        # Flow should be positive
        self.assertGreater(m_dot, 0)

        # Flow should be zero for no pressure difference
        m_dot_zero = mass_flow_orifice(PA_ATM, T_up, PA_ATM, T_down, d_eq)
        self.assertEqual(m_dot_zero, 0.0)

        # Flow should be zero for reverse pressure
        m_dot_reverse = mass_flow_orifice(PA_ATM, T_up, p_up, T_down, d_eq)
        self.assertEqual(m_dot_reverse, 0.0)


class TestReliefValveBehavior(unittest.TestCase):
    """Test relief valve behavior"""

    def setUp(self):
        """Setup test relief valves"""
        self.min_press_valve = ReliefValve(
            kind=ReliefValveKind.MIN_PRESS,
            p_set=1.05 * PA_ATM,  # 5% above atmospheric
            hyst=1000.0,  # 1000 Pa hysteresis
            d_eq=1.0e-3,  # 1mm throttle
        )

        self.stiffness_valve = ReliefValve(
            kind=ReliefValveKind.STIFFNESS,
            p_set=1.5 * PA_ATM,  # 50% above atmospheric
            hyst=2000.0,  # 2000 Pa hysteresis
            d_eq=1.0e-3,  # 1mm throttle
        )

        self.safety_valve = ReliefValve(
            kind=ReliefValveKind.SAFETY,
            p_set=2.0 * PA_ATM,  # 100% above atmospheric
            hyst=5000.0,  # 5000 Pa hysteresis
            d_eq=None,  # No throttling
        )

    def test_min_press_valve(self):
        """Test MIN_PRESS valve behavior"""
        # Should open when pressure falls below set point - hysteresis
        p_low = self.min_press_valve.p_set - 1500.0  # Below (p_set - hyst)
        self.assertTrue(self.min_press_valve.is_open(p_low))

        # Should close when pressure is above set point - hysteresis
        p_high = self.min_press_valve.p_set - 500.0  # Above (p_set - hyst)
        self.assertFalse(self.min_press_valve.is_open(p_high))

    def test_stiffness_valve(self):
        """Test STIFFNESS valve behavior"""
        # Should open when pressure exceeds set point + hysteresis
        p_high = self.stiffness_valve.p_set + 3000.0  # Above (p_set + hyst)
        self.assertTrue(self.stiffness_valve.is_open(p_high))

        # Should close when pressure is below set point + hysteresis
        p_low = self.stiffness_valve.p_set + 1000.0  # Below (p_set + hyst)
        self.assertFalse(self.stiffness_valve.is_open(p_low))

    def test_safety_valve(self):
        """Test SAFETY valve behavior"""
        # Should open when pressure exceeds set point + hysteresis
        p_high = self.safety_valve.p_set + 6000.0  # Above (p_set + hyst)
        self.assertTrue(self.safety_valve.is_open(p_high))

        # Should close when pressure is below set point + hysteresis
        p_low = self.safety_valve.p_set + 3000.0  # Below (p_set + hyst)
        self.assertFalse(self.safety_valve.is_open(p_low))

    def test_relief_valve_priorities(self):
        """Test that relief valves have correct pressure thresholds"""
        # Safety threshold should be highest
        self.assertGreater(self.safety_valve.p_set, self.stiffness_valve.p_set)

        # Stiffness threshold should be higher than min_press
        self.assertGreater(self.stiffness_valve.p_set, self.min_press_valve.p_set)

        # All should be above atmospheric
        self.assertGreater(self.min_press_valve.p_set, PA_ATM)


class TestCompressibleFlow(unittest.TestCase):
    """Test compressible flow calculations"""

    def test_choked_flow_detection(self):
        """Test detection of choked (sonic) flow conditions"""
        p_up = 200000.0  # 2 bar

        # Choked flow: p_down/p_up <= critical ratio (~0.528 for air)
        p_down_choked = p_up * 0.5  # Below critical ratio
        self.assertTrue(is_choked_flow(p_up, p_down_choked))

        # Subsonic flow: p_down/p_up > critical ratio
        p_down_subsonic = p_up * 0.8  # Above critical ratio
        self.assertFalse(is_choked_flow(p_up, p_down_subsonic))

    def test_flow_rate_scaling(self):
        """Test that flow rates scale correctly with pressure and diameter"""
        p_up_low = PA_ATM + 5000.0
        p_up_high = PA_ATM + 20000.0
        p_down = PA_ATM
        T = T_AMBIENT
        d_eq = 2.0e-3

        # Higher upstream pressure should give higher flow
        m_dot_low = mass_flow_orifice(p_up_low, T, p_down, T, d_eq)
        m_dot_high = mass_flow_orifice(p_up_high, T, p_down, T, d_eq)
        self.assertGreater(m_dot_high, m_dot_low)

        # Larger diameter should give higher flow
        d_eq_large = 4.0e-3  # Double diameter
        m_dot_large = mass_flow_orifice(p_up_low, T, p_down, T, d_eq_large)
        self.assertGreater(m_dot_large, m_dot_low)

    def test_zero_flow_conditions(self):
        """Test conditions that should produce zero flow"""
        p = PA_ATM
        T = T_AMBIENT
        d_eq = 2.0e-3

        # Same pressures
        self.assertEqual(mass_flow_orifice(p, T, p, T, d_eq), 0.0)

        # Reverse pressure (higher downstream)
        self.assertEqual(mass_flow_orifice(p, T, p + 1000, T, d_eq), 0.0)

        # Zero diameter
        self.assertEqual(mass_flow_orifice(p + 1000, T, p, T, 0.0), 0.0)

        # Negative pressures
        self.assertEqual(mass_flow_orifice(-1000, T, p, T, d_eq), 0.0)


if __name__ == "__main__":
    unittest.main()
