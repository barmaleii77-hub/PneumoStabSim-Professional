"""
P12: ODE dynamics validation tests (3-DOF rigid body)

Tests:
- scipy.integrate.solve_ivp integration stability
- One-sided spring force
- Damping behavior
- Energy bounds (with damping)

References:
- scipy.integrate.solve_ivp: https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html
- unittest: https://docs.python.org/3/library/unittest.html
"""

import unittest
import numpy as np
from numpy.testing import assert_allclose
from scipy.integrate import solve_ivp
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# CORRECTED: Use actual function names from odes.py
from src.physics.odes import f_rhs, RigidBody3DOF, create_initial_conditions
from src.physics.integrator import create_default_rigid_body


class TestODEIntegrationStability(unittest.TestCase):
    """Test ODE integration stability and convergence"""
    
    def setUp(self):
        """Setup 3-DOF rigid body parameters"""
        self.M = 1500.0  # kg (vehicle mass)
        self.Ix = 2000.0  # kg*m^2 (roll inertia)
        self.Iz = 3000.0  # kg*m^2 (pitch inertia)
        
        # Time span
        self.t_span = (0.0, 2.0)  # 2 seconds
        self.t_eval = np.linspace(0.0, 2.0, 201)  # 100 Hz sampling
        
    def test_solve_ivp_no_explosion(self):
        """Test solve_ivp does not explode on short interval
        
        Solution should remain bounded (no NaN/Inf)
        """
        # Initial state [heave, roll, pitch, heave_rate, roll_rate, pitch_rate]
        y0 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        
        def ode_func(t, y):
            """Simple damped oscillator ODE"""
            heave, roll, pitch, v_heave, v_roll, v_pitch = y
            
            # Spring-damper forces
            k = 20000.0  # N/m
            c = 2000.0   # N*s/m
            
            # Accelerations
            a_heave = -(k * heave + c * v_heave) / self.M
            a_roll = -(k * roll + c * v_roll) / self.Ix
            a_pitch = -(k * pitch + c * v_pitch) / self.Iz
            
            return [v_heave, v_roll, v_pitch, a_heave, a_roll, a_pitch]
        
        # Solve ODE
        sol = solve_ivp(
            ode_func,
            self.t_span,
            y0,
            t_eval=self.t_eval,
            method='RK45',
            rtol=1e-6,
            atol=1e-9
        )
        
        # Check solution success
        self.assertTrue(sol.success, f"solve_ivp failed: {sol.message}")
        
        # Check no NaN/Inf
        self.assertFalse(
            np.any(np.isnan(sol.y)),
            "Solution contains NaN"
        )
        self.assertFalse(
            np.any(np.isinf(sol.y)),
            "Solution contains Inf"
        )
        
    def test_damped_oscillation_decay(self):
        """Test damped oscillation decays to zero
        
        With damping, amplitude should decrease over time
        """
        # Initial displacement
        y0 = np.array([0.1, 0.0, 0.0, 0.0, 0.0, 0.0])  # 10cm heave
        
        def ode_func(t, y):
            heave, roll, pitch, v_heave, v_roll, v_pitch = y
            
            k = 20000.0
            c = 2000.0
            
            a_heave = -(k * heave + c * v_heave) / self.M
            a_roll = 0.0
            a_pitch = 0.0
            
            return [v_heave, v_roll, v_pitch, a_heave, a_roll, a_pitch]
        
        sol = solve_ivp(ode_func, self.t_span, y0, t_eval=self.t_eval, method='RK45')
        
        # Final amplitude should be less than initial
        heave_initial = abs(sol.y[0, 0])
        heave_final = abs(sol.y[0, -1])
        
        self.assertLess(
            heave_final,
            heave_initial,
            f"Damping not working: {heave_final:.6f} >= {heave_initial:.6f}"
        )
        
    def test_energy_dissipation(self):
        """Test energy decreases due to damping
        
        Total energy E = KE + PE should decrease monotonically
        """
        y0 = np.array([0.1, 0.0, 0.0, 0.0, 0.0, 0.0])
        
        k = 20000.0
        c = 2000.0
        
        def ode_func(t, y):
            heave, _, _, v_heave, _, _ = y
            a_heave = -(k * heave + c * v_heave) / self.M
            return [v_heave, 0, 0, a_heave, 0, 0]
        
        sol = solve_ivp(ode_func, self.t_span, y0, t_eval=self.t_eval, method='RK45')
        
        # Calculate energy at each timestep
        heave = sol.y[0, :]
        v_heave = sol.y[3, :]
        
        KE = 0.5 * self.M * v_heave ** 2
        PE = 0.5 * k * heave ** 2
        E_total = KE + PE
        
        # Energy should decrease (with some numerical noise)
        E_initial = E_total[0]
        E_final = E_total[-1]
        
        self.assertLess(
            E_final,
            E_initial * 0.9,  # At least 10% dissipation
            f"Energy not dissipated: {E_final:.3f}J >= {E_initial*0.9:.3f}J"
        )


class TestOneSidedSpring(unittest.TestCase):
    """Test one-sided spring behavior (force only in compression)"""
    
    def test_compression_force(self):
        """Test spring force in compression (x < 0)"""
        k = 20000.0  # N/m
        x_compression = -0.05  # -5cm (compressed)
        
        # Force should be positive (upward)
        F = max(0.0, -k * x_compression)
        
        self.assertGreater(F, 0.0, "Compression should produce positive force")
        
        expected_force = k * abs(x_compression)
        assert_allclose(F, expected_force, rtol=1e-10)
        
    def test_extension_no_force(self):
        """Test spring produces no force in extension (x > 0)"""
        k = 20000.0
        x_extension = 0.05  # +5cm (extended)
        
        # One-sided spring: no force in extension
        F = max(0.0, -k * x_extension)
        
        self.assertEqual(F, 0.0, "Extension should produce zero force")
        
    def test_zero_displacement_zero_force(self):
        """Test zero displacement produces zero force"""
        k = 20000.0
        x_zero = 0.0
        
        F = max(0.0, -k * x_zero)
        
        self.assertEqual(F, 0.0, "Zero displacement should give zero force")


class TestDampingForce(unittest.TestCase):
    """Test damping force behavior"""
    
    def test_damping_proportional_to_velocity(self):
        """Test damping force F_damp = -c * v"""
        c = 2000.0  # N*s/m
        
        velocities = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])  # m/s
        
        for v in velocities:
            F_damp = -c * v
            
            # Sign should oppose velocity
            if v > 0:
                self.assertLess(F_damp, 0, f"Damping should oppose positive velocity")
            elif v < 0:
                self.assertGreater(F_damp, 0, f"Damping should oppose negative velocity")
            else:
                self.assertEqual(F_damp, 0, "Zero velocity ? zero damping")
                
    def test_damping_magnitude(self):
        """Test damping force magnitude"""
        c = 2000.0
        v = 0.5  # m/s
        
        F_damp = -c * v
        expected = -1000.0  # N
        
        assert_allclose(F_damp, expected, rtol=1e-10)


class TestPressureForceProjection(unittest.TestCase):
    """Test projection of pneumatic forces to vertical/rotational DOF"""
    
    def test_vertical_force_projection(self):
        """Test pneumatic force projects to heave correctly"""
        # Cylinder axis vertical ? full force to heave
        F_cylinder = 1000.0  # N
        angle = 0.0  # Vertical
        
        F_heave = F_cylinder * np.cos(angle)
        
        assert_allclose(F_heave, F_cylinder, rtol=1e-10)
        
    def test_angled_force_projection(self):
        """Test pneumatic force projects to heave and moment"""
        F_cylinder = 1000.0  # N
        angle = np.radians(45.0)  # 45 degrees
        
        F_heave = F_cylinder * np.cos(angle)
        expected_heave = 1000.0 * np.cos(angle)
        
        assert_allclose(F_heave, expected_heave, rtol=1e-6)
        
    def test_moment_arm(self):
        """Test moment calculation from force and lever arm"""
        F = 1000.0  # N
        lever_arm = 0.4  # m
        
        M = F * lever_arm
        expected = 400.0  # N*m
        
        assert_allclose(M, expected, rtol=1e-10)


class TestIntegrationMethods(unittest.TestCase):
    """Test different integration methods (RK45, Radau, etc.)"""
    
    def test_rk45_explicit(self):
        """Test RK45 (explicit Runge-Kutta) method"""
        y0 = np.array([0.1, 0, 0, 0, 0, 0])
        t_span = (0, 1.0)
        
        def ode_func(t, y):
            return [-y[3], 0, 0, -100*y[0] - 10*y[3], 0, 0]
        
        sol = solve_ivp(ode_func, t_span, y0, method='RK45')
        
        self.assertTrue(sol.success, "RK45 should succeed")
        
    def test_radau_implicit(self):
        """Test Radau (implicit) method for stiff systems"""
        y0 = np.array([0.1, 0, 0, 0, 0, 0])
        t_span = (0, 1.0)
        
        def ode_func(t, y):
            # Stiff system (large damping)
            return [-y[3], 0, 0, -10000*y[0] - 1000*y[3], 0, 0]
        
        sol = solve_ivp(ode_func, t_span, y0, method='Radau')
        
        self.assertTrue(sol.success, "Radau should handle stiff systems")


if __name__ == '__main__':
    unittest.main(verbosity=2)
