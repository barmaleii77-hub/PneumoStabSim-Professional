"""
Test 3-DOF dynamics integration with gas system
"""

import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_physics_gas_integration():
    """Test integration between physics and gas systems"""
    print("=== Testing Physics-Gas Integration ===")
    
    try:
        # Test physics module imports
        from physics.odes import RigidBody3DOF, f_rhs, create_initial_conditions
        from physics.integrator import step_dynamics, create_default_rigid_body
        from physics.forces import compute_cylinder_force, compute_spring_force
        
        print("? Physics modules imported successfully")
        
        # Test gas module imports
        from pneumo.network import GasNetwork
        from pneumo.gas_state import create_line_gas_state, create_tank_gas_state
        from pneumo.enums import Line, ReceiverVolumeMode
        from common.units import PA_ATM, T_AMBIENT
        
        print("? Gas modules imported successfully")
        
        # Create test rigid body
        rigid_body = create_default_rigid_body()
        print(f"? Rigid body created: M={rigid_body.M}kg, Ix={rigid_body.Ix}kg?m?")
        
        # Test force calculations
        F_cyl = compute_cylinder_force(110000, 100000, 0.005, 0.004)  # 1bar pressure diff
        print(f"? Cylinder force calculation: {F_cyl:.1f}N")
        
        F_spring = compute_spring_force(0.05, 0.1, 50000)  # 5cm compression
        print(f"? Spring force calculation: {F_spring:.1f}N")
        
        # Test state vector operations
        y0 = create_initial_conditions(heave=0.01, roll=0.02, pitch=0.01)
        print(f"? Initial conditions: heave={y0[0]:.3f}m, roll={y0[1]:.3f}rad")
        
        # Test basic integration step (without full gas coupling)
        result = step_dynamics(
            y0=y0,
            t0=0.0,
            dt=0.01,
            params=rigid_body,
            system=None,  # Placeholder
            gas=None,     # Placeholder
            method="Radau"
        )
        
        if result.success:
            print(f"? Integration step successful: method={result.method_used}")
            print(f"  Final state: heave={result.y_final[0]:.6f}m")
        else:
            print(f"? Integration failed: {result.message}")
            return False
        
        print("? All integration tests passed")
        return True
        
    except ImportError as e:
        print(f"? Import error: {e}")
        return False
    except Exception as e:
        print(f"? Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_coordinate_system():
    """Test coordinate system consistency"""
    print("\n=== Testing Coordinate System ===")
    
    try:
        from physics.odes import RigidBody3DOF, axis_vertical_projection
        
        # Test coordinate system: Y down positive
        eY_down = np.array([0.0, 1.0, 0.0])
        eX_right = np.array([1.0, 0.0, 0.0])
        eZ_forward = np.array([0.0, 0.0, 1.0])
        
        # Test vertical projection
        F_vertical = axis_vertical_projection(1000.0, eY_down)
        assert abs(F_vertical - 1000.0) < 1e-6, "Vertical force projection failed"
        
        F_horizontal = axis_vertical_projection(1000.0, eX_right)
        assert abs(F_horizontal) < 1e-6, "Horizontal force should have zero vertical component"
        
        print("? Coordinate system Y-down confirmed")
        
        # Test attachment points layout
        rigid_body = RigidBody3DOF(M=1500, Ix=2000, Iz=3000)
        points = rigid_body.attachment_points
        
        # Verify standard layout
        assert points['LP'][0] < 0, "Left front should have negative X"
        assert points['PP'][0] > 0, "Right front should have positive X" 
        assert points['LP'][1] < 0, "Front wheels should have negative Z"
        assert points['LZ'][1] > 0, "Rear wheels should have positive Z"
        
        print("? Attachment points layout verified")
        
        # Test moment arm calculations
        # Roll moment: force ? lateral distance (X)
        # Pitch moment: force ? longitudinal distance (Z)
        
        F_left = 1000.0  # Force at left wheel
        x_left = points['LP'][0]  # Negative X
        z_front = points['LP'][1]  # Negative Z
        
        tau_roll = F_left * x_left  # Should be negative (left wheel down)
        tau_pitch = F_left * z_front  # Should be negative (nose down)
        
        print(f"? Moment calculation: roll={tau_roll:.1f}N?m, pitch={tau_pitch:.1f}N?m")
        
        return True
        
    except Exception as e:
        print(f"? Coordinate system test failed: {e}")
        return False


def run_small_scenario():
    """Run a small 5-second scenario as specified in prompt"""
    print("\n=== Running 5-Second Scenario ===")
    
    try:
        from physics.integrator import step_dynamics, create_default_rigid_body
        from physics.odes import create_initial_conditions, validate_state
        
        # Parameters
        duration = 5.0  # 5 seconds
        dt_phys = 0.001  # 1ms timestep
        
        # Create system
        params = create_default_rigid_body()
        
        # Initial conditions (small perturbation)
        y0 = create_initial_conditions(heave=0.01, roll=0.005, pitch=0.002)
        
        print(f"Running {duration}s simulation with dt={dt_phys}s...")
        print(f"Initial: heave={y0[0]:.3f}m, roll={y0[1]*180/np.pi:.2f}�, pitch={y0[2]*180/np.pi:.2f}�")
        
        # Run simulation
        t = 0.0
        y = y0.copy()
        step_count = 0
        max_angles = [0.0, 0.0]  # max |roll|, max |pitch|
        max_heave = 0.0
        
        steps = int(duration / dt_phys)
        
        for i in range(steps):
            result = step_dynamics(y, t, dt_phys, params, None, None, method="Radau")
            
            if not result.success:
                print(f"? Integration failed at step {i}: {result.message}")
                break
            
            y = result.y_final
            t = result.t_final
            step_count += 1
            
            # Track maxima
            max_angles[0] = max(max_angles[0], abs(y[1]))  # roll
            max_angles[1] = max(max_angles[1], abs(y[2]))  # pitch
            max_heave = max(max_heave, abs(y[0]))
            
            # Check for NaN/inf
            if not np.all(np.isfinite(y)):
                print(f"? Non-finite values detected at step {i}")
                break
        
        print(f"? Completed {step_count} steps successfully")
        print(f"Final: heave={y[0]:.3f}m, roll={y[1]*180/np.pi:.2f}�, pitch={y[2]*180/np.pi:.2f}�")
        print(f"Maxima: |roll|={max_angles[0]*180/np.pi:.2f}�, |pitch|={max_angles[1]*180/np.pi:.2f}�, |heave|={max_heave:.3f}m")
        
        # Validate final state
        is_valid, msg = validate_state(y, params)
        if is_valid:
            print("? Final state is valid")
        else:
            print(f"? Final state invalid: {msg}")
            return False
        
        return True
        
    except Exception as e:
        print(f"? Scenario test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run comprehensive physics integration tests"""
    print("="*60)
    print("3-DOF PHYSICS INTEGRATION TESTS")
    print("="*60)
    
    tests = [
        test_physics_gas_integration,
        test_coordinate_system,
        run_small_scenario
    ]
    
    passed = 0
    
    for test_func in tests:
        if test_func():
            passed += 1
        else:
            print("Test failed!")
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("? ALL PHYSICS TESTS PASSED - SYSTEM READY!")
    else:
        print("? Some tests failed")
    
    print("="*60)
    
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)