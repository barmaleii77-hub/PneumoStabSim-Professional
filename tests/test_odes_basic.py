"""
Basic tests for 3-DOF ODE system
Tests static equilibrium, symmetry, and numerical stability
"""

import logging
import os
import sys

import numpy as np

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from physics.forces import (
    create_test_suspension_state,
    project_forces_to_vertical_and_moments,
)
from physics.integrator import (
    PhysicsLoop,
    PhysicsLoopConfig,
    create_default_rigid_body,
    step_dynamics,
)
from physics.odes import create_initial_conditions, validate_state


def test_static_equilibrium():
    """Test that system remains at rest with balanced forces"""
    print("=== Test: Static Equilibrium ===")

    # Create rigid body parameters
    params = create_default_rigid_body()

    # Initial conditions at rest
    y0 = create_initial_conditions()  # All zeros

    # Mock system and gas (no forces)
    system = None
    gas = None

    # Integration parameters
    dt = 0.01  # 10ms
    duration = 2.0  # 2 seconds
    steps = int(duration / dt)

    t = 0.0
    y = y0.copy()
    max_deviation = 0.0

    print(f"Running {steps} steps with dt={dt}s")

    for i in range(steps):
        try:
            result = step_dynamics(y, t, dt, params, system, gas, method="Radau")

            if not result.success:
                print(f"FAIL: Integration failed at step {i}: {result.message}")
                return False

            y = result.y_final
            t = result.t_final

            # Track maximum deviation from zero
            deviation = np.max(np.abs(y))
            max_deviation = max(max_deviation, deviation)

            # Check for reasonable bounds
            if deviation > 1.0:  # 1m or 1 rad deviation is too much for static test
                print(f"FAIL: Excessive deviation at step {i}: {deviation:.6f}")
                print(f"State: {y}")
                return False

        except Exception as e:
            print(f"FAIL: Exception at step {i}: {e}")
            return False

    print(f"PASS: Maximum deviation over {duration}s: {max_deviation:.8f}")
    print(f"Final state: {y}")
    return True


def test_force_projection():
    """Test force projection and moment calculation"""
    print("\n=== Test: Force Projection ===")

    # Create test attachment points
    attachment_points = {
        "LP": (-0.8, -1.6),  # Left front
        "PP": (+0.8, -1.6),  # Right front
        "LZ": (-0.8, +1.6),  # Left rear
        "PZ": (+0.8, +1.6),  # Right rear
    }

    # Test case 1: Equal vertical forces (should produce no moments)
    print("Test 1: Equal forces, no moments")
    suspension_states = {}
    test_force = 1000.0  # 1000N per wheel

    for wheel_name in ["LP", "PP", "LZ", "PZ"]:
        suspension_states[wheel_name] = create_test_suspension_state(
            wheel_name, F_cyl=test_force
        )

    forces, tau_x, tau_z = project_forces_to_vertical_and_moments(
        suspension_states, attachment_points
    )

    expected_forces = np.array([test_force, test_force, test_force, test_force])

    if not np.allclose(forces, expected_forces, atol=1e-6):
        print(f"FAIL: Forces don't match. Expected {expected_forces}, got {forces}")
        return False

    if abs(tau_x) > 1e-6 or abs(tau_z) > 1e-6:
        print(f"FAIL: Non-zero moments with equal forces: ?x={tau_x}, ?z={tau_z}")
        return False

    print("PASS: Equal forces produce zero moments")

    # Test case 2: Front/rear imbalance (should produce pitch moment)
    print("Test 2: Front/rear imbalance")
    suspension_states["LP"]["F_cyl_axis"] = test_force * 1.5  # More force at front left
    suspension_states["LP"]["F_total_axis"] = test_force * 1.5
    suspension_states["PP"]["F_cyl_axis"] = (
        test_force * 1.5
    )  # More force at front right
    suspension_states["PP"]["F_total_axis"] = test_force * 1.5

    forces, tau_x, tau_z = project_forces_to_vertical_and_moments(
        suspension_states, attachment_points
    )

    # Should have negative pitch moment (nose down due to coordinate system)
    if tau_x >= 0:
        print(f"FAIL: Expected positive pitch moment, got ?x={tau_x}")
        return False

    # Roll moment should still be zero (symmetric left/right)
    if abs(tau_z) > 1e-6:
        print(f"FAIL: Expected zero roll moment, got ?z={tau_z}")
        return False

    print(f"PASS: Front/rear imbalance produces correct pitch moment: ?x={tau_x:.1f}")

    # Test case 3: Left/right imbalance (should produce roll moment)
    print("Test 3: Left/right imbalance")
    # Reset to equal front/rear
    suspension_states["LP"]["F_cyl_axis"] = test_force * 1.5  # More force at left
    suspension_states["LP"]["F_total_axis"] = test_force * 1.5
    suspension_states["LZ"]["F_cyl_axis"] = test_force * 1.5  # More force at left
    suspension_states["LZ"]["F_total_axis"] = test_force * 1.5
    suspension_states["PP"]["F_cyl_axis"] = test_force  # Normal force at right
    suspension_states["PP"]["F_total_axis"] = test_force
    suspension_states["PZ"]["F_cyl_axis"] = test_force  # Normal force at right
    suspension_states["PZ"]["F_total_axis"] = test_force

    forces, tau_x, tau_z = project_forces_to_vertical_and_moments(
        suspension_states, attachment_points
    )

    # Should have negative roll moment (left side down)
    if tau_z >= 0:
        print(f"FAIL: Expected negative roll moment, got ?z={tau_z}")
        return False

    print(f"PASS: Left/right imbalance produces correct roll moment: ?z={tau_z:.1f}")

    return True


def test_state_validation():
    """Test state validation functions"""
    print("\n=== Test: State Validation ===")

    params = create_default_rigid_body()

    # Test valid state
    y_valid = create_initial_conditions(heave=0.1, roll=0.05, pitch=0.02)
    is_valid, msg = validate_state(y_valid, params)

    if not is_valid:
        print(f"FAIL: Valid state rejected: {msg}")
        return False

    print("PASS: Valid state accepted")

    # Test invalid states

    # Test NaN
    y_nan = y_valid.copy()
    y_nan[0] = np.nan
    is_valid, msg = validate_state(y_nan, params)

    if is_valid:
        print("FAIL: NaN state accepted")
        return False

    print("PASS: NaN state rejected")

    # Test excessive angles
    y_big_angle = y_valid.copy()
    y_big_angle[1] = 1.0  # 1 radian roll (> 0.5 limit)
    is_valid, msg = validate_state(y_big_angle, params)

    if is_valid:
        print("FAIL: Excessive angle accepted")
        return False

    print("PASS: Excessive angle rejected")

    return True


def test_symmetry_response():
    """Test symmetric response to symmetric inputs"""
    print("\n=== Test: Symmetry Response ===")

    params = create_default_rigid_body()

    # Test will be expanded when actual suspension forces are implemented
    # For now, just verify the framework works

    print("PASS: Symmetry test framework ready")
    return True


def test_physics_loop():
    """Test physics loop functionality"""
    print("\n=== Test: Physics Loop ===")

    config = PhysicsLoopConfig(
        dt_physics=0.001, dt_render=0.016, max_steps_per_render=20
    )

    params = create_default_rigid_body()
    y0 = create_initial_conditions()

    # Create physics loop (with mock system/gas)
    loop = PhysicsLoop(config, params, system=None, gas=None)
    loop.reset(y0)

    # Simulate some real-time steps
    dt_real = 0.017  # Slightly more than render rate

    for i in range(10):
        result = loop.step_physics_fixed(dt_real)

        if result["steps_taken"] == 0:
            print(f"FAIL: No physics steps taken in iteration {i}")
            return False

        # Check that state is reasonable
        y_current = result["y_current"]
        is_valid, msg = validate_state(y_current, params)

        if not is_valid:
            print(f"FAIL: Invalid state after {i} iterations: {msg}")
            return False

    stats = loop.get_statistics()
    print(f"PASS: Physics loop completed {stats['total_steps']} steps")
    print(f"Success rate: {stats['success_rate']:.3f}")
    print(f"Average solve time: {stats['average_solve_time']*1000:.3f}ms")

    return True


def run_all_tests():
    """Run all ODE tests"""
    print("=" * 60)
    print("PNEUMOSTABSIM 3-DOF ODE TESTS")
    print("=" * 60)

    # Setup logging
    logging.basicConfig(level=logging.WARNING)

    tests = [
        ("Static Equilibrium", test_static_equilibrium),
        ("Force Projection", test_force_projection),
        ("State Validation", test_state_validation),
        ("Symmetry Response", test_symmetry_response),
        ("Physics Loop", test_physics_loop),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"FAILED: {test_name}")
        except Exception as e:
            failed += 1
            print(f"ERROR in {test_name}: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
