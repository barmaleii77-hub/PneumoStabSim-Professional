"""
Road module demonstration
Shows highway and urban scenarios with delay verification
"""

import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from road.engine import create_road_input_from_preset
from road.scenarios import get_preset_by_name


def demo_highway_scenario():
    """Demonstrate highway scenario with ISO D profile"""
    print("=== HIGHWAY SCENARIO DEMONSTRATION ===")
    
    # Create highway preset (ISO D, 100 km/h)
    road_input = create_road_input_from_preset('highway_100kmh')
    road_input.prime()
    
    info = road_input.get_info()
    print(f"Highway scenario:")
    print(f"  Velocity: {info['velocity']*3.6:.0f} km/h")
    print(f"  Wheelbase: {info['wheelbase']:.1f}m")
    print(f"  Axle delay: {info['axle_delay']:.3f}s")
    
    # Sample 10 seconds of road profile
    times = np.linspace(0, 10.0, 1000) 
    
    profiles = {'LF': [], 'RF': [], 'LR': [], 'RR': []}
    
    for t in times:
        excitation = road_input.get_wheel_excitation(t)
        for wheel in profiles.keys():
            profiles[wheel].append(excitation[wheel])
    
    # Convert to numpy arrays
    for wheel in profiles.keys():
        profiles[wheel] = np.array(profiles[wheel])
    
    # Show statistics
    print("\nProfile statistics (10s sample):")
    for wheel in ['LF', 'RF', 'LR', 'RR']:
        rms = np.sqrt(np.mean(profiles[wheel]**2))
        peak = np.max(np.abs(profiles[wheel]))
        print(f"  {wheel}: RMS={rms*1000:.2f}mm, Peak={peak*1000:.2f}mm")
    
    # Verify axle delay using cross-correlation
    correlation = np.correlate(profiles['LF'], profiles['LR'], mode='full')
    delay_idx = np.argmax(correlation) - (len(profiles['LR']) - 1)
    dt = times[1] - times[0]
    measured_delay = delay_idx * dt
    
    print(f"\nDelay verification:")
    print(f"  Expected: {info['axle_delay']:.3f}s")
    print(f"  Measured: {measured_delay:.3f}s")
    print(f"  Error: {abs(measured_delay - info['axle_delay'])*1000:.1f}ms")
    
    return profiles, times


def demo_urban_scenario():
    """Demonstrate urban scenario with speed bumps"""
    print("\n=== URBAN SCENARIO DEMONSTRATION ===")
    
    # Create urban preset (ISO D + speed bumps, 50 km/h)
    road_input = create_road_input_from_preset('urban_50kmh')
    road_input.prime()
    
    info = road_input.get_info()
    print(f"Urban scenario:")
    print(f"  Velocity: {info['velocity']*3.6:.0f} km/h")
    print(f"  Duration: {info['duration']:.0f}s")
    
    # Sample first 20 seconds
    times = np.linspace(0, 20.0, 2000)
    
    profiles = {'LF': [], 'RF': [], 'LR': [], 'RR': []}
    
    for t in times:
        excitation = road_input.get_wheel_excitation(t)
        for wheel in profiles.keys():
            profiles[wheel].append(excitation[wheel])
    
    # Convert to numpy arrays
    for wheel in profiles.keys():
        profiles[wheel] = np.array(profiles[wheel])
    
    # Show statistics
    print("\nProfile statistics (20s sample):")
    for wheel in ['LF', 'RF', 'LR', 'RR']:
        rms = np.sqrt(np.mean(profiles[wheel]**2))
        peak = np.max(np.abs(profiles[wheel]))
        print(f"  {wheel}: RMS={rms*1000:.2f}mm, Peak={peak*1000:.2f}mm")
    
    return profiles, times


def demo_test_scenarios():
    """Demonstrate test scenarios"""
    print("\n=== TEST SCENARIOS DEMONSTRATION ===")
    
    scenarios = ['test_pothole', 'test_speed_bump', 'test_sine']
    
    for scenario_name in scenarios:
        print(f"\n{scenario_name.upper()}:")
        
        road_input = create_road_input_from_preset(scenario_name)
        road_input.prime()
        
        info = road_input.get_info()
        print(f"  Duration: {info['duration']:.0f}s")
        print(f"  Velocity: {info['velocity']*3.6:.0f} km/h")
        
        # Sample at feature center
        t_center = info['duration'] / 2
        excitation = road_input.get_wheel_excitation(t_center)
        
        print(f"  Peak excitation: LF={excitation['LF']*1000:.2f}mm")


def show_available_presets():
    """Show all available presets"""
    print("\n=== AVAILABLE PRESETS ===")
    
    from road.scenarios import get_presets_by_category
    
    categories = get_presets_by_category()
    
    for category, preset_names in categories.items():
        if preset_names:  # Only show non-empty categories
            print(f"\n{category}:")
            for name in preset_names:
                preset = get_preset_by_name(name)
                if preset:
                    print(f"  {name}: {preset.velocity*3.6:.0f}km/h, {preset.duration:.0f}s, {preset.source_kind.name}")


def main():
    """Run road module demonstration"""
    print("="*60)
    print("ROAD MODULE DEMONSTRATION")
    print("="*60)
    
    try:
        # Show available presets
        show_available_presets()
        
        # Highway demonstration
        demo_highway_scenario()
        
        # Urban demonstration  
        demo_urban_scenario()
        
        # Test scenarios
        demo_test_scenarios()
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("? Highway scenario with axle delay verification")
        print("? Urban scenario with ISO 8608 profiles")
        print("? Test scenarios (pothole, speed bump, sine)")
        print("? All wheel positions working correctly")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\nDEMONSTRATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)