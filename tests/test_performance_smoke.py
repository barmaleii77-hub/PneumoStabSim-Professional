"""
P12: Performance smoke tests

Light performance validation:
- Physics step timing
- UI update lag
- Memory stability

References:
- unittest: https://docs.python.org/3/library/unittest.html
"""

import unittest
import time
import sys
from pathlib import Path
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.physics.integrator import create_default_rigid_body
from scipy.integrate import solve_ivp


class TestPhysicsStepTiming(unittest.TestCase):
    """Test physics step execution time"""
    
    def test_single_ode_step_fast(self):
        """Test single ODE step completes quickly
        
        Single integration step should be < 10ms
        """
        def ode_func(t, y):
            """Simple damped oscillator"""
            heave, roll, pitch, v_h, v_r, v_p = y
            
            M = 1500.0
            Ix = 2000.0
            Iz = 3000.0
            k = 20000.0
            c = 2000.0
            
            a_h = -(k * heave + c * v_h) / M
            a_r = -(k * roll + c * v_r) / Ix
            a_p = -(k * pitch + c * v_p) / Iz
            
            return [v_h, v_r, v_p, a_h, a_r, a_p]
        
        y0 = np.array([0.1, 0.01, 0.01, 0.0, 0.0, 0.0])
        t_span = (0.0, 0.01)  # 10ms step
        
        # Time single step
        start = time.perf_counter()
        sol = solve_ivp(ode_func, t_span, y0, method='RK45')
        elapsed = time.perf_counter() - start
        
        # Should complete in < 10ms
        self.assertLess(
            elapsed,
            0.010,
            f"Single ODE step took {elapsed*1000:.2f}ms (should be < 10ms)"
        )
        
    def test_multiple_steps_reasonable(self):
        """Test 100 ODE steps complete in reasonable time
        
        100 steps @ 10ms each = 1 second physics time
        Should complete in < 1 second real time
        """
        def ode_func(t, y):
            heave, roll, pitch, v_h, v_r, v_p = y
            M, Ix, Iz = 1500.0, 2000.0, 3000.0
            k, c = 20000.0, 2000.0
            
            a_h = -(k * heave + c * v_h) / M
            a_r = -(k * roll + c * v_r) / Ix
            a_p = -(k * pitch + c * v_p) / Iz
            
            return [v_h, v_r, v_p, a_h, a_r, a_p]
        
        y0 = np.array([0.1, 0.01, 0.01, 0.0, 0.0, 0.0])
        t_span = (0.0, 1.0)  # 1 second
        t_eval = np.linspace(0.0, 1.0, 101)  # 100 steps
        
        start = time.perf_counter()
        sol = solve_ivp(ode_func, t_span, y0, t_eval=t_eval, method='RK45')
        elapsed = time.perf_counter() - start
        
        # Should complete in < 1 second
        self.assertLess(
            elapsed,
            1.0,
            f"100 ODE steps took {elapsed:.3f}s (should be < 1s)"
        )
        
        # Check solution valid
        self.assertTrue(sol.success)
        self.assertEqual(len(sol.t), 101)


class TestMemoryStability(unittest.TestCase):
    """Test memory usage remains stable"""
    
    def test_repeated_ode_no_memory_leak(self):
        """Test repeated ODE calls don't accumulate memory
        
        This is a simple smoke test - real leak detection needs profiling tools
        """
        def ode_func(t, y):
            return [-y[i] - 0.1*y[i+3] for i in range(3)] + \
                   [-(100*y[i] + 10*y[i+3]) for i in range(3)]
        
        y0 = np.array([0.1, 0.01, 0.01, 0.0, 0.0, 0.0])
        t_span = (0.0, 0.1)
        
        # Run multiple times
        for _ in range(10):
            sol = solve_ivp(ode_func, t_span, y0, method='RK45')
            self.assertTrue(sol.success)
        
        # If we got here without crash, consider it passed
        # (Real leak detection requires memory profiling)


class TestNumericalStability(unittest.TestCase):
    """Test numerical stability of calculations"""
    
    def test_no_nan_in_solution(self):
        """Test solution never contains NaN"""
        def ode_func(t, y):
            heave, roll, pitch, v_h, v_r, v_p = y
            M, Ix, Iz = 1500.0, 2000.0, 3000.0
            k, c = 20000.0, 2000.0
            
            a_h = -(k * heave + c * v_h) / M
            a_r = -(k * roll + c * v_r) / Ix
            a_p = -(k * pitch + c * v_p) / Iz
            
            return [v_h, v_r, v_p, a_h, a_r, a_p]
        
        y0 = np.array([0.1, 0.01, 0.01, 0.0, 0.0, 0.0])
        t_span = (0.0, 2.0)
        t_eval = np.linspace(0.0, 2.0, 201)
        
        sol = solve_ivp(ode_func, t_span, y0, t_eval=t_eval, method='RK45')
        
        # Check no NaN/Inf
        self.assertFalse(
            np.any(np.isnan(sol.y)),
            "Solution contains NaN"
        )
        self.assertFalse(
            np.any(np.isinf(sol.y)),
            "Solution contains Inf"
        )
        
    def test_bounded_solution(self):
        """Test solution remains bounded with damping"""
        def ode_func(t, y):
            heave, roll, pitch, v_h, v_r, v_p = y
            M, Ix, Iz = 1500.0, 2000.0, 3000.0
            k, c = 20000.0, 2000.0
            
            a_h = -(k * heave + c * v_h) / M
            a_r = -(k * roll + c * v_r) / Ix
            a_p = -(k * pitch + c * v_p) / Iz
            
            return [v_h, v_r, v_p, a_h, a_r, a_p]
        
        y0 = np.array([0.1, 0.01, 0.01, 0.0, 0.0, 0.0])
        t_span = (0.0, 5.0)
        t_eval = np.linspace(0.0, 5.0, 501)
        
        sol = solve_ivp(ode_func, t_span, y0, t_eval=t_eval, method='RK45')
        
        # With damping, solution should decay
        # Max displacement should be less than 2x initial
        max_heave = np.max(np.abs(sol.y[0, :]))
        
        self.assertLess(
            max_heave,
            0.2,  # 2x initial 0.1m
            f"Heave grew unbounded: {max_heave:.3f}m"
        )


class TestIntegrationMethodPerformance(unittest.TestCase):
    """Compare integration method performance"""
    
    def test_rk45_vs_radau(self):
        """Compare RK45 (explicit) vs Radau (implicit) timing"""
        def ode_func(t, y):
            heave, roll, pitch, v_h, v_r, v_p = y
            M, Ix, Iz = 1500.0, 2000.0, 3000.0
            k, c = 20000.0, 2000.0
            
            a_h = -(k * heave + c * v_h) / M
            a_r = -(k * roll + c * v_r) / Ix
            a_p = -(k * pitch + c * v_p) / Iz
            
            return [v_h, v_r, v_p, a_h, a_r, a_p]
        
        y0 = np.array([0.1, 0.01, 0.01, 0.0, 0.0, 0.0])
        t_span = (0.0, 1.0)
        
        # RK45 (explicit)
        start = time.perf_counter()
        sol_rk45 = solve_ivp(ode_func, t_span, y0, method='RK45')
        time_rk45 = time.perf_counter() - start
        
        # Radau (implicit)
        start = time.perf_counter()
        sol_radau = solve_ivp(ode_func, t_span, y0, method='Radau')
        time_radau = time.perf_counter() - start
        
        # Both should complete
        self.assertTrue(sol_rk45.success, "RK45 should succeed")
        self.assertTrue(sol_radau.success, "Radau should succeed")
        
        # RK45 usually faster for non-stiff systems
        # (but not always, so just check both complete in reasonable time)
        self.assertLess(time_rk45, 1.0, "RK45 too slow")
        self.assertLess(time_radau, 2.0, "Radau too slow")


if __name__ == '__main__':
    unittest.main(verbosity=2)
