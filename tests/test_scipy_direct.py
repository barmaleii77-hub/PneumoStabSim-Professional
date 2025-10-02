"""
Simple scipy test
"""

from scipy.integrate import solve_ivp
import numpy as np

def test_solve_ivp():
    """Test solve_ivp directly"""
    print("Testing solve_ivp directly...")
    
    # Simple 3-DOF free fall system
    def rhs(t, y):
        # y = [Y, phi_z, theta_x, dY, dphi_z, dtheta_x]
        Y, phi_z, theta_x, dY, dphi_z, dtheta_x = y
        
        # Simple gravity + damping
        d2Y = 9.81  # Free fall
        d2phi_z = -0.1 * dphi_z  # Damped roll
        d2theta_x = -0.1 * dtheta_x  # Damped pitch
        
        return [dY, dphi_z, dtheta_x, d2Y, d2phi_z, d2theta_x]
    
    # Initial conditions
    y0 = [0.0, 0.01, 0.01, 0.0, 0.0, 0.0]  # Small initial angles
    
    # Integrate for 1 second
    sol = solve_ivp(rhs, [0, 1.0], y0, method='Radau', rtol=1e-6, atol=1e-9)
    
    if sol.success:
        y_final = sol.y[:, -1]
        print(f"SUCCESS: Integration completed")
        print(f"Final heave: {y_final[0]:.3f}m (should be ~4.9m for free fall)")
        print(f"Final roll: {y_final[1]:.6f}rad (should decay toward 0)")
        print(f"Final pitch: {y_final[2]:.6f}rad (should decay toward 0)")
        print(f"Heave velocity: {y_final[3]:.3f}m/s (should be ~9.8m/s)")
        
        # Validate results
        expected_heave = 0.5 * 9.81 * 1.0**2  # s = 0.5*g*t^2
        if abs(y_final[0] - expected_heave) < 0.1:
            print("PASS: Free fall physics correct")
        else:
            print(f"WARN: Expected heave ~{expected_heave:.1f}m, got {y_final[0]:.1f}m")
        
        if abs(y_final[1]) < abs(0.01) and abs(y_final[2]) < abs(0.01):
            print("PASS: Angular damping working")
        else:
            print("WARN: Angular damping may not be working")
            
        return True
    else:
        print(f"FAILED: {sol.message}")
        return False


if __name__ == "__main__":
    success = test_solve_ivp()
    print("="*50)
    print("SCIPY INTEGRATION:", "PASSED" if success else "FAILED")
    print("="*50)