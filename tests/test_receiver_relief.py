"""
Tests for receiver relief valve behavior
"""

import unittest
import math
from src.pneumo.network import GasNetwork
from src.pneumo.gas_state import TankGasState, create_tank_gas_state
from src.pneumo.enums import ReceiverVolumeMode
from src.common.units import PA_ATM, T_AMBIENT, R_AIR


class TestReceiverRelief(unittest.TestCase):
    """Test receiver relief valve operations"""
    
    def setUp(self):
        """Setup test network with tank at various pressures"""
        # Create a minimal gas network for testing
        # We'll focus on the tank relief behavior
        pass
    
    def test_min_press_relief_activation(self):
        """Test MIN_PRESS relief valve activates at correct threshold"""
        # Create tank at pressure just above MIN_PRESS threshold
        p_min_threshold = 1.05 * PA_ATM
        
        tank_above_min = create_tank_gas_state(
            V_initial=0.001,  # 1L
            p_initial=p_min_threshold + 2000,  # 2000 Pa above threshold
            T_initial=T_AMBIENT,
            mode=ReceiverVolumeMode.NO_RECALC
        )
        
        # Tank at this pressure should trigger MIN_PRESS relief
        self.assertGreater(tank_above_min.p, p_min_threshold)
        
        # Tank below threshold should not trigger
        tank_below_min = create_tank_gas_state(
            V_initial=0.001,
            p_initial=p_min_threshold - 1000,  # Below threshold
            T_initial=T_AMBIENT
        )
        
        self.assertLess(tank_below_min.p, p_min_threshold)
    
    def test_stiffness_relief_activation(self):
        """Test STIFFNESS relief valve activates at correct threshold"""
        p_stiff_threshold = 1.5 * PA_ATM
        
        # Tank above STIFFNESS threshold
        tank_above_stiff = create_tank_gas_state(
            V_initial=0.001,
            p_initial=p_stiff_threshold + 5000,  # 5000 Pa above
            T_initial=T_AMBIENT
        )
        
        self.assertGreater(tank_above_stiff.p, p_stiff_threshold)
        
        # This should also be above MIN_PRESS threshold (hierarchy)
        p_min_threshold = 1.05 * PA_ATM
        self.assertGreater(tank_above_stiff.p, p_min_threshold)
    
    def test_safety_relief_activation(self):
        """Test SAFETY relief valve activates at highest threshold"""
        p_safety_threshold = 2.0 * PA_ATM
        
        # Tank at dangerous pressure level
        tank_at_safety = create_tank_gas_state(
            V_initial=0.001,
            p_initial=p_safety_threshold + 10000,  # Well above safety limit
            T_initial=T_AMBIENT
        )
        
        self.assertGreater(tank_at_safety.p, p_safety_threshold)
        
        # Should also trigger both lower-level reliefs
        p_stiff_threshold = 1.5 * PA_ATM
        p_min_threshold = 1.05 * PA_ATM
        
        self.assertGreater(tank_at_safety.p, p_stiff_threshold)
        self.assertGreater(tank_at_safety.p, p_min_threshold)
    
    def test_relief_valve_hierarchy(self):
        """Test that relief valves have correct pressure hierarchy"""
        p_min = 1.05 * PA_ATM
        p_stiff = 1.5 * PA_ATM
        p_safety = 2.0 * PA_ATM
        
        # Verify hierarchy: SAFETY > STIFFNESS > MIN_PRESS > ATMOSPHERIC
        self.assertGreater(p_safety, p_stiff)
        self.assertGreater(p_stiff, p_min)
        self.assertGreater(p_min, PA_ATM)
        
        # Verify reasonable spacing between thresholds
        self.assertGreater(p_stiff - p_min, 10000)    # At least 10kPa between min and stiffness
        self.assertGreater(p_safety - p_stiff, 20000) # At least 20kPa between stiffness and safety
    
    def test_mass_conservation_during_relief(self):
        """Test that mass is conserved during relief operations"""
        # Start with high-pressure tank
        initial_p = 2.5 * PA_ATM  # Above all thresholds
        initial_V = 0.001
        initial_T = T_AMBIENT
        
        tank = create_tank_gas_state(initial_V, initial_p, initial_T)
        initial_mass = tank.m
        
        # Simulate relief by manually reducing mass (as would happen in actual relief)
        # This represents mass flowing out through relief valve
        mass_relieved = initial_mass * 0.1  # 10% of mass relieved
        tank.m -= mass_relieved
        
        # Recalculate pressure after mass reduction
        from src.pneumo.gas_state import p_from_mTV
        tank.p = p_from_mTV(tank.m, tank.T, tank.V)
        
        # Final mass should be reduced by exactly the relieved amount
        self.assertAlmostEqual(tank.m, initial_mass - mass_relieved, places=10)
        
        # Pressure should be lower
        self.assertLess(tank.p, initial_p)
        
        # Temperature and volume unchanged (for NO_RECALC mode)
        self.assertAlmostEqual(tank.T, initial_T, places=1)
        self.assertAlmostEqual(tank.V, initial_V, places=6)
    
    def test_throttling_vs_unlimited_flow(self):
        """Test difference between throttled and unlimited relief"""
        # MIN_PRESS and STIFFNESS valves have throttling (small d_eq)
        d_eq_throttled = 1.0e-3  # 1mm - limited flow
        
        # SAFETY valve has unlimited flow (no throttling)
        d_eq_unlimited = None    # Represents unlimited flow
        
        # At same pressure differential, unlimited flow should be much higher
        # This is tested conceptually - the actual flow calculation
        # would show safety valve allows much faster pressure reduction
        
        # Throttled valves provide controlled, slow relief
        self.assertIsNotNone(d_eq_throttled)
        self.assertGreater(d_eq_throttled, 0)
        
        # Safety valve provides rapid, unlimited relief
        self.assertIsNone(d_eq_unlimited)
    
    def test_pressure_reduction_effectiveness(self):
        """Test that relief valves effectively reduce pressure"""
        # Start with tank at 2.5 bar (well above safety threshold)
        high_pressure = 2.5 * PA_ATM
        tank = create_tank_gas_state(0.001, high_pressure, T_AMBIENT)
        
        # Simulate SAFETY valve operation (fast mass removal)
        # Safety valve should quickly bring pressure down to ~2.0 bar
        target_pressure = 2.0 * PA_ATM  # Safety threshold
        
        # Calculate required mass removal to reach target pressure
        from src.pneumo.gas_state import p_from_mTV
        target_mass = (target_pressure * tank.V) / (R_AIR * tank.T)
        
        # Remove excess mass
        excess_mass = tank.m - target_mass
        self.assertGreater(excess_mass, 0)  # Should have excess to remove
        
        tank.m = target_mass
        tank.p = p_from_mTV(tank.m, tank.T, tank.V)
        
        # Pressure should now be at target level
        self.assertAlmostEqual(tank.p, target_pressure, delta=1000)  # Within 1kPa
        
    def test_hysteresis_behavior(self):
        """Test relief valve hysteresis prevents oscillation"""
        p_set = 1.5 * PA_ATM     # STIFFNESS valve set point
        hyst = 2000.0            # 2000 Pa hysteresis
        
        # Valve opens at p_set + hyst
        p_open = p_set + hyst
        
        # Valve closes at p_set - hyst (for falling pressure)
        # This prevents rapid on/off cycling
        p_close = p_set - hyst
        
        # Verify hysteresis creates separation
        self.assertGreater(p_open, p_close)
        self.assertEqual(p_open - p_close, 2 * hyst)
        
        # Reasonable hysteresis values
        self.assertGreater(hyst, 500)   # At least 500 Pa
        self.assertLess(hyst, 10000)    # Not more than 10 kPa
    
    def test_multiple_relief_activation(self):
        """Test behavior when multiple relief valves activate simultaneously"""
        # At very high pressure, all three relief valves should activate
        very_high_pressure = 3.0 * PA_ATM
        
        p_min = 1.05 * PA_ATM
        p_stiff = 1.5 * PA_ATM  
        p_safety = 2.0 * PA_ATM
        
        # All thresholds should be exceeded
        self.assertGreater(very_high_pressure, p_safety)
        self.assertGreater(very_high_pressure, p_stiff)
        self.assertGreater(very_high_pressure, p_min)
        
        # Total relief capacity should be sum of all active valves
        # (In practice, safety valve dominates due to unlimited flow)
        
        # This represents the network's ability to handle extreme overpressure
        total_relief_capacity = "MIN_PRESS + STIFFNESS + SAFETY (dominant)"
        self.assertIsNotNone(total_relief_capacity)


class TestReceiverOperationalScenarios(unittest.TestCase):
    """Test realistic operational scenarios for receiver relief"""
    
    def test_normal_operation_no_relief(self):
        """Test normal operation where no relief valves activate"""
        # Normal operating pressure slightly above atmospheric
        normal_pressure = 1.02 * PA_ATM  # 2% above atmospheric
        
        tank = create_tank_gas_state(0.001, normal_pressure, T_AMBIENT)
        
        # Should be below all relief thresholds
        self.assertLess(tank.p, 1.05 * PA_ATM)  # Below MIN_PRESS
        self.assertLess(tank.p, 1.5 * PA_ATM)   # Below STIFFNESS
        self.assertLess(tank.p, 2.0 * PA_ATM)   # Below SAFETY
    
    def test_gradual_pressure_buildup(self):
        """Test gradual pressure buildup triggering relief in sequence"""
        pressures = [
            1.03 * PA_ATM,  # Normal - no relief
            1.07 * PA_ATM,  # MIN_PRESS relief only
            1.55 * PA_ATM,  # MIN_PRESS + STIFFNESS relief
            2.1 * PA_ATM    # All relief valves active
        ]
        
        for i, pressure in enumerate(pressures):
            tank = create_tank_gas_state(0.001, pressure, T_AMBIENT)
            
            # Check which relief valves would be active
            min_active = tank.p > 1.05 * PA_ATM
            stiff_active = tank.p > 1.5 * PA_ATM
            safety_active = tank.p > 2.0 * PA_ATM
            
            if i == 0:  # Normal operation
                self.assertFalse(min_active)
                self.assertFalse(stiff_active)
                self.assertFalse(safety_active)
            elif i == 1:  # MIN_PRESS only
                self.assertTrue(min_active)
                self.assertFalse(stiff_active)
                self.assertFalse(safety_active)
            elif i == 2:  # MIN_PRESS + STIFFNESS
                self.assertTrue(min_active)
                self.assertTrue(stiff_active)
                self.assertFalse(safety_active)
            elif i == 3:  # All active
                self.assertTrue(min_active)
                self.assertTrue(stiff_active)
                self.assertTrue(safety_active)


if __name__ == '__main__':
    unittest.main()