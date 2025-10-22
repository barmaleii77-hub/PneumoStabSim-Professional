"""
Tests for adiabatic and isothermal gas processes (simplified)
"""

import unittest
from src.pneumo.gas_state import (
    LineGasState,
    iso_update,
    adiabatic_update,
    apply_instant_volume_change,
    create_line_gas_state,
    create_tank_gas_state,
)
from src.pneumo.enums import Line, ReceiverVolumeMode
from src.common.units import PA_ATM, T_AMBIENT, GAMMA_AIR


class TestGasProcesses(unittest.TestCase):
    """Test basic gas processes"""

    def test_isothermal_process_basic(self):
        """Test basic isothermal process"""
        # Create line with known state
        line = create_line_gas_state(Line.A1, PA_ATM, T_AMBIENT, 1e-3)
        initial_p = line.p
        initial_V = line.V_curr

        # Compress isothermally
        new_V = initial_V * 0.5
        iso_update(line, new_V, T_AMBIENT)

        # Pressure should roughly double for half volume
        pressure_ratio = line.p / initial_p
        self.assertGreater(pressure_ratio, 1.5)  # Should be close to 2.0
        self.assertLess(pressure_ratio, 2.5)

        # Temperature should remain constant
        self.assertAlmostEqual(line.T, T_AMBIENT, places=1)

    def test_adiabatic_process_basic(self):
        """Test basic adiabatic process"""
        # Create line with known state
        line = create_line_gas_state(Line.A1, PA_ATM, T_AMBIENT, 1e-3)
        initial_T = line.T

        # Compress adiabatically
        new_V = line.V_curr * 0.5
        adiabatic_update(line, new_V, GAMMA_AIR)

        # Temperature should increase during compression
        self.assertGreater(line.T, initial_T)

        # Pressure should increase more than isothermal case
        self.assertGreater(line.p, PA_ATM * 2.0)

    def test_tank_volume_modes(self):
        """Test tank volume change modes"""
        # NO_RECALC mode
        tank_no_recalc = create_tank_gas_state(
            0.001, PA_ATM, T_AMBIENT, ReceiverVolumeMode.NO_RECALC
        )
        initial_p = tank_no_recalc.p
        initial_T = tank_no_recalc.T

        apply_instant_volume_change(tank_no_recalc, 0.0005)  # Half volume

        # Pressure and temperature should remain unchanged
        self.assertAlmostEqual(tank_no_recalc.p, initial_p, delta=100)
        self.assertAlmostEqual(tank_no_recalc.T, initial_T, places=1)

        # ADIABATIC_RECALC mode
        tank_adiabatic = create_tank_gas_state(
            0.001, PA_ATM, T_AMBIENT, ReceiverVolumeMode.ADIABATIC_RECALC
        )
        initial_p = tank_adiabatic.p
        initial_T = tank_adiabatic.T

        apply_instant_volume_change(tank_adiabatic, 0.0005, GAMMA_AIR)  # Half volume

        # Pressure should increase, temperature should increase
        self.assertGreater(tank_adiabatic.p, initial_p)
        self.assertGreater(tank_adiabatic.T, initial_T)

    def test_gas_state_validation(self):
        """Test gas state parameter validation"""
        # Valid state should not raise
        try:
            line = create_line_gas_state(Line.A1, PA_ATM, T_AMBIENT, 1e-3)
            self.assertIsNotNone(line)
        except Exception:
            self.fail("Valid gas state creation should not raise exception")

        # Invalid parameters should raise
        with self.assertRaises(ValueError):
            LineGasState(Line.A1, m=-0.1, T=300, p=100000, V_prev=1e-3, V_curr=1e-3)

        with self.assertRaises(ValueError):
            LineGasState(Line.A1, m=1e-4, T=0, p=100000, V_prev=1e-3, V_curr=1e-3)


if __name__ == "__main__":
    unittest.main()
