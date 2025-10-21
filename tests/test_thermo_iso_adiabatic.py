"""
Unit tests for isothermal and adiabatic thermodynamic processes.

Tests:
- Isothermal compression and expansion
- Adiabatic compression and expansion
- Ideal gas law consistency
- Mode switching consistency

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

from src.pneumo.gas_state import GasState
from src.pneumo.thermo import ThermoMode


class TestIsothermalProcess(unittest.TestCase):
    """Test isothermal thermodynamic process (T=const)"""
    
    def setUp(self):
        """Setup gas state for isothermal tests"""
        self.R = 287.05  # J/(kg·K) for air
        
        # Initial state
        self.T_const = 293.15  # K (20°C)
        self.p0 = 200000.0  # 2 bar
        self.V0 = 0.001  # 1 liter
        
        # Calculate initial mass
        self.m0 = (self.p0 * self.V0) / (self.R * self.T_const)
        
        self.gas = GasState(
            pressure=self.p0,
            temperature=self.T_const,
            volume=self.V0
        )
        
    def test_isothermal_compression(self):
        """Test isothermal compression: V? ? p?, T=const"""
        # Compress to half volume
        V_new = self.V0 / 2.0
        
        # Expected pressure (Boyle's law: p1*V1 = p2*V2)
        p_expected = self.p0 * (self.V0 / V_new)
        
        # Update gas state (isothermal)
        self.gas.update_volume(V_new, mode=ThermoMode.ISOTHERMAL)
        
        # Check temperature unchanged
        assert_allclose(
            self.gas.temperature,
            self.T_const,
            rtol=1e-10,
            err_msg="Temperature should remain constant in isothermal process"
        )
        
        # Check pressure matches expected
        assert_allclose(
            self.gas.pressure,
            p_expected,
            rtol=1e-10,
            err_msg="Pressure mismatch in isothermal compression"
        )
        
        # Check mass conserved
        assert_allclose(
            self.gas.mass,
            self.m0,
            rtol=1e-10,
            err_msg="Mass should be conserved in closed system"
        )

    def test_isothermal_expansion(self):
        """Test isothermal expansion: V? ? p?, T=const"""
        # Expand to double volume
        V_new = self.V0 * 2.0
        
        # Expected pressure
        p_expected = self.p0 * (self.V0 / V_new)
        
        # Update gas state
        self.gas.update_volume(V_new, mode=ThermoMode.ISOTHERMAL)
        
        # Check temperature unchanged
        assert_allclose(
            self.gas.temperature,
            self.T_const,
            rtol=1e-10,
            err_msg="Temperature should remain constant"
        )
        
        # Check pressure halved
        assert_allclose(
            self.gas.pressure,
            p_expected,
            rtol=1e-10,
            err_msg="Pressure mismatch in isothermal expansion"
        )
        
    def test_isothermal_mass_constant(self):
        """Test mass remains constant during isothermal volume change"""
        m_initial = self.gas.mass
        
        # Change volume
        self.gas.update_volume(self.V0 * 1.5, mode=ThermoMode.ISOTHERMAL)
        
        # Mass should not change (no flow)
        assert_allclose(
            self.gas.mass,
            m_initial,
            rtol=1e-10,
            err_msg="Mass should be conserved in closed system"
        )
        
    def test_isothermal_ideal_gas_law(self):
        """Test ideal gas law p = mRT/V holds after volume change"""
        # Change volume
        V_new = self.V0 * 1.3
        self.gas.update_volume(V_new, mode=ThermoMode.ISOTHERMAL)
        
        # Calculate pressure from ideal gas law
        p_calculated = (self.gas.mass * self.R * self.gas.temperature) / self.gas.volume
        
        assert_allclose(
            self.gas.pressure,
            p_calculated,
            rtol=1e-10,
            err_msg="Ideal gas law violated"
        )


class TestAdiabaticProcess(unittest.TestCase):
    """Test adiabatic thermodynamic process (temperature changes)"""
    
    def setUp(self):
        """Setup gas state for adiabatic tests"""
        self.R = 287.05  # J/(kg·K)
        self.gamma = 1.4  # Heat capacity ratio for air
        
        # Initial state
        self.T0 = 293.15  # K
        self.p0 = 200000.0  # Pa
        self.V0 = 0.001  # m?
        
        self.m0 = (self.p0 * self.V0) / (self.R * self.T0)
        
        self.gas = GasState(
            pressure=self.p0,
            temperature=self.T0,
            volume=self.V0
        )
        
    def test_adiabatic_compression_heats(self):
        """Test adiabatic compression increases temperature"""
        # Compress to half volume
        V_new = self.V0 / 2.0
        
        # Expected temperature (T2/T1 = (V1/V2)^(gamma-1))
        T_expected = self.T0 * (self.V0 / V_new) ** (self.gamma - 1)
        
        # Update gas state (adiabatic)
        self.gas.update_volume(V_new, mode=ThermoMode.ADIABATIC)
        
        # Temperature should increase
        self.assertGreater(
            self.gas.temperature,
            self.T0,
            "Temperature should increase during adiabatic compression"
        )
        
        # Check against analytical solution
        assert_allclose(
            self.gas.temperature,
            T_expected,
            rtol=0.01,  # 1% tolerance
            err_msg=f"Temperature mismatch: {self.gas.temperature:.2f}K vs {T_expected:.2f}K"
        )
        
    def test_adiabatic_expansion_cools(self):
        """Test adiabatic expansion decreases temperature"""
        # Expand to double volume
        V_new = self.V0 * 2.0
        
        # Expected temperature
        T_expected = self.T0 * (self.V0 / V_new) ** (self.gamma - 1)
        
        # Update gas state
        self.gas.update_volume(V_new, mode=ThermoMode.ADIABATIC)
        
        # Temperature should decrease
        self.assertLess(
            self.gas.temperature,
            self.T0,
            "Temperature should decrease during adiabatic expansion"
        )
        
        # Check against analytical solution
        assert_allclose(
            self.gas.temperature,
            T_expected,
            rtol=0.01,
            err_msg=f"Temperature mismatch: {self.gas.temperature:.2f}K vs {T_expected:.2f}K"
        )
        
    def test_mass_mixing_temperature(self):
        """Test temperature mixing when adding mass
        
        When mass flows in, resulting temperature is mass-weighted average
        """
        # Initial state
        m1 = self.gas.mass
        T1 = self.gas.temperature
        
        # Incoming flow
        m_in = 0.0001  # kg
        T_in = 350.0  # K (hot)
        
        # Expected mixed temperature
        T_mixed = (m1 * T1 + m_in * T_in) / (m1 + m_in)
        
        # Add mass
        self.gas.add_mass(m_in, T_in)
        
        # Check mixed temperature
        assert_allclose(
            self.gas.temperature,
            T_mixed,
            rtol=1e-6,
            err_msg=f"Mixed temperature incorrect: {self.gas.temperature:.2f}K vs {T_mixed:.2f}K"
        )
        
    def test_adiabatic_pvgamma_invariant(self):
        """Test adiabatic invariant pV^gamma = const
        
        For adiabatic process without mass exchange
        """
        # Initial pV^gamma
        pv_gamma_initial = self.p0 * (self.V0 ** self.gamma)
        
        # Compress
        V_new = self.V0 / 2.0
        self.gas.update_volume(V_new, mode=ThermoMode.ADIABATIC)
        
        # Final pV^gamma
        pv_gamma_final = self.gas.pressure * (self.gas.volume ** self.gamma)
        
        # Should be conserved (within numerical tolerance)
        assert_allclose(
            pv_gamma_final,
            pv_gamma_initial,
            rtol=0.01,  # 1% tolerance
            err_msg=f"Adiabatic invariant not conserved: {pv_gamma_final:.0f} vs {pv_gamma_initial:.0f}"
        )


class TestModeConsistency(unittest.TestCase):
    """Test consistency between isothermal and adiabatic modes"""
    
    def test_mode_switching(self):
        """Test switching between isothermal and adiabatic modes"""
        gas = GasState(pressure=200000.0, temperature=293.15, volume=0.001)
        
        # Isothermal compression
        V_compressed = 0.0005
        gas.update_volume(V_compressed, mode=ThermoMode.ISOTHERMAL)
        T_iso = gas.temperature
        p_iso = gas.pressure
        
        # Reset
        gas = GasState(pressure=200000.0, temperature=293.15, volume=0.001)
        
        # Adiabatic compression (same volume change)
        gas.update_volume(V_compressed, mode=ThermoMode.ADIABATIC)
        T_adiab = gas.temperature
        p_adiab = gas.pressure
        
        # Adiabatic should have higher temperature and pressure
        self.assertGreater(T_adiab, T_iso, "Adiabatic T > Isothermal T")
        self.assertGreater(p_adiab, p_iso, "Adiabatic p > Isothermal p")
        
    def test_energy_conservation(self):
        """Test energy conservation in adiabatic process
        
        dU = -p*dV (work done by/on gas)
        """
        gas = GasState(pressure=200000.0, temperature=293.15, volume=0.001)
        
        cv = 717.5  # J/(kg·K) for air
        
        # Initial internal energy
        U0 = gas.mass * cv * gas.temperature
        
        # Compress adiabatically
        V_new = 0.0005
        p_initial = gas.pressure
        V_initial = gas.volume

        # Update state
        gas.update_volume(V_new, mode=ThermoMode.ADIABATIC)

        # Work done on the gas using the adiabatic work integral
        gamma = gas.gamma
        p_final = gas.pressure
        V_final = gas.volume
        W = (p_final * V_final - p_initial * V_initial) / (gamma -1.0)

        # Final internal energy
        U1 = gas.mass * cv * gas.temperature
        
        # Change in internal energy
        dU = U1 - U0
        
        # Should equal work done (first law for adiabatic process)
        assert_allclose(
            dU,
            W,
            rtol=5e-4,
            err_msg=f"Energy balance: dU={dU:.2f}J, W={W:.2f}J"
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
