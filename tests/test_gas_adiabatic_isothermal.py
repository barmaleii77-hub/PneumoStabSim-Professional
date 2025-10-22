"""
Tests for adiabatic and isothermal gas processes
"""

import unittest
from src.pneumo.gas_state import (
    LineGasState,
    TankGasState,
    iso_update,
    adiabatic_update,
    apply_instant_volume_change,
    p_from_mTV,
)
from src.pneumo.enums import Line, ReceiverVolumeMode
from src.common.units import PA_ATM, T_AMBIENT, R_AIR, GAMMA_AIR


class TestIsothermalProcess(unittest.TestCase):
    """Test isothermal gas processes"""

    def setUp(self):
        """Setup test gas state with consistent initial conditions"""
        V_initial = 1e-3  # 1 cm?
        p_initial = PA_ATM
        T_initial = T_AMBIENT

        # Calculate mass from ideal gas law for consistency
        m_initial = (p_initial * V_initial) / (R_AIR * T_initial)

        self.line_state = LineGasState(
            name=Line.A1,
            m=m_initial,
            T=T_initial,
            p=p_initial,
            V_prev=V_initial,
            V_curr=V_initial,
        )

    def test_isothermal_compression(self):
        """Test isothermal compression (volume decreases)"""
        initial_p = self.line_state.p
        initial_V = self.line_state.V_curr
        initial_m = self.line_state.m

        # Compress to half volume
        new_V = initial_V * 0.5
        iso_update(self.line_state, new_V, T_AMBIENT)

        # Check Boyle's law: p1*V1 = p2*V2 (at constant T)
        expected_p = initial_p * (initial_V / new_V)
        self.assertAlmostEqual(
            self.line_state.p, expected_p, delta=1000
        )  # 1000 Pa tolerance

        # Temperature should remain constant
        self.assertAlmostEqual(self.line_state.T, T_AMBIENT, places=1)

        # Mass should remain constant
        self.assertAlmostEqual(self.line_state.m, initial_m, places=10)

    def test_isothermal_expansion(self):
        """Test isothermal expansion (volume increases)"""
        initial_p = self.line_state.p
        initial_V = self.line_state.V_curr
        initial_m = self.line_state.m

        # Expand to double volume
        new_V = initial_V * 2.0
        iso_update(self.line_state, new_V, T_AMBIENT)

        # Check Boyle's law: pressure should halve
        expected_p = initial_p * 0.5
        self.assertAlmostEqual(self.line_state.p, expected_p, places=0)

        # Temperature should remain constant
        self.assertAlmostEqual(self.line_state.T, T_AMBIENT, places=1)

        # Mass should remain constant
        self.assertAlmostEqual(self.line_state.m, initial_m, places=10)

    def test_isothermal_invariants(self):
        """Test that isothermal process maintains p*V = constant"""
        initial_pV = self.line_state.p * self.line_state.V_curr

        # Test multiple volume changes
        for volume_ratio in [0.5, 0.8, 1.2, 2.0]:
            new_V = self.line_state.V_prev * volume_ratio
            iso_update(self.line_state, new_V, T_AMBIENT)

            new_pV = self.line_state.p * self.line_state.V_curr

            # p*V should remain constant (within numerical precision)
            self.assertAlmostEqual(new_pV / initial_pV, 1.0, places=6)


class TestAdiabaticProcess(unittest.TestCase):
    """Test adiabatic gas processes"""

    def setUp(self):
        """Setup test gas state"""
        self.line_state = LineGasState(
            name=Line.A1,
            m=1e-4,  # 0.1g initial mass
            T=T_AMBIENT,  # 293.15K
            p=PA_ATM,  # 101325 Pa
            V_prev=1e-3,  # 1 cm?
            V_curr=1e-3,  # 1 cm?
        )

    def test_adiabatic_compression(self):
        """Test adiabatic compression (volume decreases, temperature rises)"""
        initial_T = self.line_state.T
        initial_p = self.line_state.p
        initial_V = self.line_state.V_curr
        initial_m = self.line_state.m

        # Compress to half volume
        new_V = initial_V * 0.5
        adiabatic_update(self.line_state, new_V, GAMMA_AIR)

        # Check adiabatic relations
        volume_ratio = initial_V / new_V  # = 2.0

        # T_new = T_old * (V_old/V_new)^(gamma-1)
        expected_T = initial_T * (volume_ratio ** (GAMMA_AIR - 1.0))
        self.assertAlmostEqual(self.line_state.T, expected_T, places=1)

        # p_new = p_old * (V_old/V_new)^gamma
        expected_p = initial_p * (volume_ratio**GAMMA_AIR)
        self.assertAlmostEqual(self.line_state.p, expected_p, places=0)

        # Mass should remain constant
        self.assertAlmostEqual(self.line_state.m, initial_m, places=10)

        # Temperature should increase during compression
        self.assertGreater(self.line_state.T, initial_T)

    def test_adiabatic_expansion(self):
        """Test adiabatic expansion (volume increases, temperature drops)"""
        initial_T = self.line_state.T
        initial_p = self.line_state.p
        initial_V = self.line_state.V_curr

        # Expand to double volume
        new_V = initial_V * 2.0
        adiabatic_update(self.line_state, new_V, GAMMA_AIR)

        # Check adiabatic relations
        volume_ratio = initial_V / new_V  # = 0.5

        # Temperature should decrease during expansion
        self.assertLess(self.line_state.T, initial_T)

        # Check adiabatic formula
        expected_T = initial_T * (volume_ratio ** (GAMMA_AIR - 1.0))
        self.assertAlmostEqual(self.line_state.T, expected_T, places=1)

    def test_adiabatic_invariants(self):
        """Test adiabatic invariants: p*V^gamma = constant, T*V^(gamma-1) = constant"""
        initial_pV_gamma = self.line_state.p * (self.line_state.V_curr**GAMMA_AIR)
        initial_TV_gamma_minus_1 = self.line_state.T * (
            self.line_state.V_curr ** (GAMMA_AIR - 1.0)
        )

        # Test multiple volume changes
        for volume_ratio in [0.5, 0.7, 1.3, 2.0]:
            new_V = self.line_state.V_prev * volume_ratio
            adiabatic_update(self.line_state, new_V, GAMMA_AIR)

            # Check p*V^gamma = constant
            new_pV_gamma = self.line_state.p * (self.line_state.V_curr**GAMMA_AIR)
            self.assertAlmostEqual(new_pV_gamma / initial_pV_gamma, 1.0, places=5)

            # Check T*V^(gamma-1) = constant
            new_TV_gamma_minus_1 = self.line_state.T * (
                self.line_state.V_curr ** (GAMMA_AIR - 1.0)
            )
            self.assertAlmostEqual(
                new_TV_gamma_minus_1 / initial_TV_gamma_minus_1, 1.0, places=5
            )

    def test_ideal_gas_consistency(self):
        """Test that adiabatic updates maintain ideal gas law p = mRT/V"""
        # Test after compression
        new_V = self.line_state.V_curr * 0.6
        adiabatic_update(self.line_state, new_V, GAMMA_AIR)

        # Calculate pressure from ideal gas law
        expected_p = p_from_mTV(
            self.line_state.m, self.line_state.T, self.line_state.V_curr
        )

        # Should match the stored pressure
        self.assertAlmostEqual(self.line_state.p, expected_p, places=0)


class TestReceiverVolumeChange(unittest.TestCase):
    """Test receiver tank volume changes"""

    def setUp(self):
        """Setup test tank state"""
        self.tank_no_recalc = TankGasState(
            V=0.001,  # 1L
            p=PA_ATM,  # 101325 Pa
            T=T_AMBIENT,  # 293.15K
            m=1e-3,  # 1g
            mode=ReceiverVolumeMode.NO_RECALC,
        )

        self.tank_adiabatic = TankGasState(
            V=0.001,  # 1L
            p=PA_ATM,  # 101325 Pa
            T=T_AMBIENT,  # 293.15K
            m=1e-3,  # 1g
            mode=ReceiverVolumeMode.ADIABATIC_RECALC,
        )

    def test_no_recalc_mode(self):
        """Test NO_RECALC mode keeps p,T constant"""
        initial_p = self.tank_no_recalc.p
        initial_T = self.tank_no_recalc.T
        initial_m = self.tank_no_recalc.m

        # Change volume
        new_V = self.tank_no_recalc.V * 1.5
        apply_instant_volume_change(self.tank_no_recalc, new_V)

        # Pressure and temperature should remain unchanged
        self.assertAlmostEqual(self.tank_no_recalc.p, initial_p, places=0)
        self.assertAlmostEqual(self.tank_no_recalc.T, initial_T, places=1)
        self.assertAlmostEqual(self.tank_no_recalc.m, initial_m, places=10)

        # Volume should be updated
        self.assertAlmostEqual(self.tank_no_recalc.V, new_V, places=6)

    def test_adiabatic_recalc_mode(self):
        """Test ADIABATIC_RECALC mode updates p,T adiabatically"""
        initial_p = self.tank_adiabatic.p
        initial_T = self.tank_adiabatic.T
        initial_V = self.tank_adiabatic.V
        initial_m = self.tank_adiabatic.m

        # Compress tank to half volume
        new_V = initial_V * 0.5
        apply_instant_volume_change(self.tank_adiabatic, new_V, GAMMA_AIR)

        # Check adiabatic relations
        volume_ratio = initial_V / new_V  # = 2.0

        expected_p = initial_p * (volume_ratio**GAMMA_AIR)
        expected_T = initial_T * (volume_ratio ** (GAMMA_AIR - 1.0))

        self.assertAlmostEqual(self.tank_adiabatic.p, expected_p, places=0)
        self.assertAlmostEqual(self.tank_adiabatic.T, expected_T, places=1)

        # Mass should be approximately preserved (within numerical precision)
        self.assertAlmostEqual(self.tank_adiabatic.m, initial_m, places=8)

    def test_mass_consistency(self):
        """Test that mass remains consistent through volume changes"""
        # Calculate initial mass from ideal gas law
        initial_mass_calculated = (self.tank_adiabatic.p * self.tank_adiabatic.V) / (
            R_AIR * self.tank_adiabatic.T
        )
        self.assertAlmostEqual(self.tank_adiabatic.m, initial_mass_calculated, places=8)

        # After adiabatic volume change
        new_V = self.tank_adiabatic.V * 1.3
        apply_instant_volume_change(self.tank_adiabatic, new_V, GAMMA_AIR)

        # Recalculate mass and verify consistency
        final_mass_calculated = (self.tank_adiabatic.p * self.tank_adiabatic.V) / (
            R_AIR * self.tank_adiabatic.T
        )
        self.assertAlmostEqual(self.tank_adiabatic.m, final_mass_calculated, places=8)


class TestGasStateValidation(unittest.TestCase):
    """Test gas state validation and error handling"""

    def test_invalid_parameters(self):
        """Test that invalid parameters raise appropriate errors"""
        # Negative mass
        with self.assertRaises(ValueError):
            LineGasState(Line.A1, m=-0.1, T=300, p=100000, V_prev=1e-3, V_curr=1e-3)

        # Zero temperature
        with self.assertRaises(ValueError):
            LineGasState(Line.A1, m=1e-4, T=0, p=100000, V_prev=1e-3, V_curr=1e-3)

        # Negative pressure
        with self.assertRaises(ValueError):
            LineGasState(Line.A1, m=1e-4, T=300, p=-1000, V_prev=1e-3, V_curr=1e-3)

        # Zero volume
        with self.assertRaises(ValueError):
            LineGasState(Line.A1, m=1e-4, T=300, p=100000, V_prev=0, V_curr=1e-3)

    def test_edge_cases(self):
        """Test edge cases in gas calculations"""
        line_state = LineGasState(
            Line.A1, m=1e-10, T=300, p=1000, V_prev=1e-6, V_curr=1e-6
        )

        # Very small volume change
        new_V = line_state.V_curr * 1.001  # 0.1% change
        adiabatic_update(line_state, new_V, GAMMA_AIR)

        # Should not crash and should produce reasonable results
        self.assertGreater(line_state.T, 0)
        self.assertGreater(line_state.p, 0)
        self.assertGreater(line_state.m, 0)


if __name__ == "__main__":
    unittest.main()
