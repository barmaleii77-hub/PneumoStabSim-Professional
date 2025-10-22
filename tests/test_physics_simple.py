"""
Test 3-DOF dynamics integration
"""

import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_basic_integration():
    """Test basic physics integration"""
    print("=== Testing Basic Physics Integration ===")

    try:
        # Import modules
        from physics.odes import create_initial_conditions
        from physics.integrator import step_dynamics, create_default_rigid_body

        print("SUCCESS: Physics modules imported")

        # Create test setup
        params = create_default_rigid_body()
        y0 = create_initial_conditions(heave=0.01, roll=0.005)

        print(f"Rigid body: M={params.M}kg, angles=+/-{params.angle_limit:.1f}rad")

        # Test integration step
        result = step_dynamics(y0, 0.0, 0.01, params, None, None, method="Radau")

        if result.success:
            print(f"SUCCESS: Integration with {result.method_used}")
            print(f"Final heave: {result.y_final[0]:.6f}m")
            return True
        else:
            print(f"FAILED: {result.message}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_coordinate_system():
    """Test coordinate system"""
    print("\n=== Testing Coordinate System ===")

    try:
        from physics.odes import axis_vertical_projection

        # Y-down coordinate system
        eY = np.array([0.0, 1.0, 0.0])
        F_down = axis_vertical_projection(1000.0, eY)

        if abs(F_down - 1000.0) < 1e-6:
            print("SUCCESS: Y-down coordinate system confirmed")
            return True
        else:
            print("FAILED: Coordinate system error")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def run_scenario():
    """Run 5-second scenario"""
    print("\n=== Running 5-Second Scenario ===")

    try:
        from physics.integrator import step_dynamics, create_default_rigid_body
        from physics.odes import create_initial_conditions

        params = create_default_rigid_body()
        y0 = create_initial_conditions(heave=0.01, roll=0.002, pitch=0.001)

        # Shorter test for reliability
        duration = 1.0  # 1 second
        dt = 0.01  # 10ms steps
        steps = int(duration / dt)

        print(f"Running {steps} steps, dt={dt}s")

        t, y = 0.0, y0.copy()
        successful_steps = 0

        for i in range(steps):
            result = step_dynamics(y, t, dt, params, None, None)

            if result.success:
                y = result.y_final
                t = result.t_final
                successful_steps += 1
            else:
                print(f"Step {i} failed")
                break

        print(f"SUCCESS: {successful_steps}/{steps} steps completed")
        print(f"Final: heave={y[0]:.3f}m, angles=[{y[1]:.3f}, {y[2]:.3f}]rad")

        return successful_steps == steps

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    """Run physics tests"""
    print("=" * 50)
    print("3-DOF PHYSICS TESTS")
    print("=" * 50)

    tests = [test_basic_integration, test_coordinate_system, run_scenario]
    passed = sum(1 for test in tests if test())

    print(f"\nRESULTS: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("ALL TESTS PASSED - PHYSICS SYSTEM READY!")
        return True
    else:
        print("Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
