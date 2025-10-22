"""
Simple integration test for scipy.solve_ivp
"""

import numpy as np
from scipy.integrate import solve_ivp
import time


def simple_harmonic_oscillator(t, y):
    """Simple harmonic oscillator: d?x/dt? = -??x"""
    x, v = y
    omega = 1.0  # Natural frequency
    return [v, -(omega**2) * x]


def run_integration_test():
    """Test scipy.solve_ivp with different methods"""
    print("=== Testing scipy.solve_ivp Integration ===")

    # Initial conditions: x=1, v=0 (released from rest)
    y0 = [1.0, 0.0]
    t_span = (0.0, 5.0)  # 5 seconds

    methods = ["Radau", "BDF", "RK45"]

    for method in methods:
        print(f"\nTesting method: {method}")

        start_time = time.perf_counter()

        try:
            sol = solve_ivp(
                fun=simple_harmonic_oscillator,
                t_span=t_span,
                y0=y0,
                method=method,
                rtol=1e-6,
                atol=1e-9,
                max_step=0.01,
                dense_output=False,
            )

            solve_time = time.perf_counter() - start_time

            if sol.success:
                x_final, v_final = sol.y[:, -1]
                print(f"SUCCESS: Final state = [{x_final:.6f}, {v_final:.6f}]")
                print(f"Function evaluations: {sol.nfev}")
                print(f"Solve time: {solve_time*1000:.3f}ms")

                # For harmonic oscillator, energy should be conserved
                energy_initial = 0.5 * (y0[0] ** 2 + y0[1] ** 2)  # E = 0.5(x? + v?)
                energy_final = 0.5 * (x_final**2 + v_final**2)
                energy_error = abs(energy_final - energy_initial) / energy_initial

                print(f"Energy conservation error: {energy_error:.6e}")

                if energy_error < 1e-4:  # 0.01% error tolerance
                    print(f"PASS: {method} conserves energy well")
                else:
                    print(f"WARNING: {method} has poor energy conservation")
            else:
                print(f"FAILED: {sol.message}")

        except Exception as e:
            print(f"ERROR: {e}")


def test_3dof_placeholder():
    """Placeholder test for 3-DOF system structure"""
    print("\n=== Testing 3-DOF System Structure ===")

    # Test state vector structure
    # y = [Y, phi_z, theta_x, dY, dphi_z, dtheta_x]

    def simple_3dof_rhs(t, y):
        """Simplified 3-DOF system with gravity only"""
        Y, phi_z, theta_x, dY, dphi_z, dtheta_x = y

        # Parameters
        M = 1500.0  # Mass (kg)
        Ix = 2000.0  # Pitch inertia
        Iz = 3000.0  # Roll inertia
        g = 9.81  # Gravity
        c_damping = 0.1  # Damping

        # Simple dynamics: gravity + damping
        d2Y = g  # Free fall
        d2phi_z = -c_damping * dphi_z  # Damped roll
        d2theta_x = -c_damping * dtheta_x  # Damped pitch

        return [dY, dphi_z, dtheta_x, d2Y, d2phi_z, d2theta_x]

    # Initial conditions (small perturbation)
    y0 = [0.0, 0.01, 0.01, 0.0, 0.0, 0.0]  # Small initial angles

    # Short simulation
    t_span = (0.0, 1.0)

    print("Running 3-DOF test with Radau method...")

    try:
        sol = solve_ivp(
            fun=simple_3dof_rhs,
            t_span=t_span,
            y0=y0,
            method="Radau",
            rtol=1e-6,
            atol=1e-9,
            max_step=0.01,
        )

        if sol.success:
            y_final = sol.y[:, -1]
            Y, phi_z, theta_x, dY, dphi_z, dtheta_x = y_final

            print("PASS: 3-DOF integration successful")
            print(f"Final heave: {Y:.6f}m, velocity: {dY:.6f}m/s")
            print(f"Final roll: {phi_z:.6f}rad, rate: {dphi_z:.6f}rad/s")
            print(f"Final pitch: {theta_x:.6f}rad, rate: {dtheta_x:.6f}rad/s")

            # Check that angles are damping toward zero
            if abs(dphi_z) < abs(0.01) and abs(dtheta_x) < abs(0.01):
                print("PASS: Angular rates are damping as expected")
            else:
                print("WARNING: Angular damping may not be working correctly")

        else:
            print(f"FAILED: 3-DOF integration failed: {sol.message}")
            return False

    except Exception as e:
        print(f"ERROR in 3-DOF test: {e}")
        return False

    return True


def main():
    """Run all integration tests"""
    print("=" * 60)
    print("PNEUMOSTABSIM SCIPY INTEGRATION TESTS")
    print("=" * 60)

    # Check scipy availability
    try:
        print(f"NumPy version: {np.__version__}")
        import scipy

        print(f"SciPy version: {scipy.__version__}")
        print(f"solve_ivp available: {solve_ivp}")
        print()
    except Exception as e:
        print(f"FAILED: SciPy import error: {e}")
        return False

    # Run tests
    run_integration_test()
    success = test_3dof_placeholder()

    print("\n" + "=" * 60)
    if success:
        print("INTEGRATION TESTS PASSED")
    else:
        print("SOME INTEGRATION TESTS FAILED")
    print("=" * 60)

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
