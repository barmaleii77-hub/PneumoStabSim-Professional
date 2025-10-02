"""
Simple road module test
"""

import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_road_import():
    """Test basic road module imports"""
    print("=== Testing Road Module Imports ===")
    
    try:
        from road.types import SourceKind, Iso8608Class, CorrelationSpec
        from road.generators import generate_sine_profile, generate_iso8608_profile
        from road.engine import RoadInput
        from road.scenarios import get_preset_by_name
        
        print("SUCCESS: All road modules imported")
        return True
        
    except Exception as e:
        print(f"ERROR: Import failed: {e}")
        return False


def test_sine_generation():
    """Test basic sine profile generation"""
    print("\n=== Testing Sine Profile Generation ===")
    
    try:
        from road.generators import generate_sine_profile
        
        t, profile = generate_sine_profile(
            duration=5.0,
            velocity=20.0,
            amplitude=0.05,
            frequency=1.0,
            resample_hz=100.0
        )
        
        print(f"Generated {len(t)} samples over {t[-1]:.1f}s")
        print(f"Profile range: {np.min(profile):.3f} to {np.max(profile):.3f}m")
        
        # Basic checks
        if len(t) == len(profile) and np.all(np.isfinite(profile)):
            print("SUCCESS: Sine profile generation")
            return True
        else:
            print("ERROR: Invalid profile data")
            return False
            
    except Exception as e:
        print(f"ERROR: Sine generation failed: {e}")
        return False


def test_road_engine():
    """Test RoadInput engine"""
    print("\n=== Testing RoadInput Engine ===")
    
    try:
        from road.types import SourceKind, RoadConfig
        from road.engine import RoadInput
        
        # Create configuration
        config = RoadConfig(
            source=SourceKind.SINE,
            velocity=25.0,
            duration=10.0,
            amplitude=0.03,
            frequency=2.0,
            wheelbase=3.2,
            track=1.6
        )
        
        # Create and configure road input
        road_input = RoadInput()
        road_input.configure(config)
        road_input.prime()
        
        # Test excitation
        excitation = road_input.get_wheel_excitation(5.0)
        
        print(f"Excitation at t=5.0s: {excitation}")
        
        # Check format
        expected_keys = {'LF', 'RF', 'LR', 'RR'}
        if set(excitation.keys()) == expected_keys:
            print("SUCCESS: RoadInput engine working")
            return True
        else:
            print("ERROR: Invalid excitation format")
            return False
            
    except Exception as e:
        print(f"ERROR: RoadInput test failed: {e}")
        return False


def test_highway_preset():
    """Test highway preset"""
    print("\n=== Testing Highway Preset ===")
    
    try:
        from road.scenarios import get_preset_by_name
        from road.engine import create_road_input_from_preset
        
        # Create road input from preset
        road_input = create_road_input_from_preset('highway_100kmh')
        road_input.prime()
        
        info = road_input.get_info()
        print(f"Highway preset: {info['velocity']:.1f}m/s, {info['duration']:.1f}s")
        
        # Test a few time points
        times = [1.0, 10.0, 30.0]
        
        for t in times:
            excitation = road_input.get_wheel_excitation(t)
            values = list(excitation.values())
            
            if all(np.isfinite(v) for v in values):
                print(f"t={t:4.1f}s: LF={excitation['LF']*1000:5.2f}mm")
            else:
                print(f"ERROR: Non-finite values at t={t}s")
                return False
        
        print("SUCCESS: Highway preset working")
        return True
        
    except Exception as e:
        print(f"ERROR: Highway preset test failed: {e}")
        return False


def main():
    """Run simple road tests"""
    print("="*50)
    print("ROAD MODULE SIMPLE TESTS")
    print("="*50)
    
    tests = [
        test_road_import,
        test_sine_generation,
        test_road_engine,
        test_highway_preset
    ]
    
    passed = 0
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nRESULTS: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("ALL TESTS PASSED - ROAD MODULE READY!")
        return True
    else:
        print("Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)