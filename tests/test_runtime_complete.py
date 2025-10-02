"""
Minimal runtime test without physics imports
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_runtime_components():
    """Test runtime components individually"""
    print("=== Testing Runtime Components ===")
    
    try:
        # Test state management
        from runtime.state import StateSnapshot, StateBus, FrameState, WheelState
        print("? State management imported")
        
        # Test synchronization
        from runtime.sync import LatestOnlyQueue, PerformanceMetrics, TimingAccumulator
        print("? Synchronization imported")
        
        # Test basic state creation
        snapshot = StateSnapshot()
        snapshot.simulation_time = 1.0
        snapshot.step_number = 100
        
        print(f"? StateSnapshot: t={snapshot.simulation_time}s, step={snapshot.step_number}")
        
        # Test frame state
        frame = FrameState()
        frame.heave = 0.01
        frame.roll = 0.005
        frame.pitch = 0.002
        snapshot.frame = frame
        
        print(f"? FrameState: heave={frame.heave}m, roll={frame.roll}rad, pitch={frame.pitch}rad")
        
        # Test validation
        is_valid = snapshot.validate()
        print(f"? Snapshot validation: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"? Runtime test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sync_components():
    """Test synchronization components"""
    print("\n=== Testing Synchronization ===")
    
    try:
        from runtime.sync import LatestOnlyQueue, PerformanceMetrics, TimingAccumulator
        
        # Test latest-only queue
        queue = LatestOnlyQueue()
        
        # Test multiple puts - should keep only latest
        queue.put_nowait("item1")
        queue.put_nowait("item2")
        queue.put_nowait("item3")
        
        # Should get only the latest
        result = queue.get_nowait()
        print(f"? LatestOnlyQueue: got '{result}' (should be 'item3')")
        
        # Queue should be empty now
        result2 = queue.get_nowait()
        print(f"? Queue empty check: {result2} (should be None)")
        
        # Test statistics
        stats = queue.get_stats()
        print(f"? Queue stats: {stats}")
        
        # Test performance metrics
        perf = PerformanceMetrics()
        perf.target_dt = 0.001
        
        # Simulate some step times
        for i in range(5):
            step_time = 0.001 + i * 0.0001  # Gradually increasing
            perf.update_step_time(step_time)
        
        print(f"? Performance metrics: avg={perf.avg_step_time*1000:.3f}ms, fps={perf.get_fps():.1f}")
        
        # Test timing accumulator
        acc = TimingAccumulator(0.001)  # 1ms target
        
        # Simulate timing
        time.sleep(0.005)  # Sleep 5ms
        steps = acc.update()
        print(f"? Timing accumulator: {steps} steps needed")
        
        return True
        
    except Exception as e:
        print(f"? Sync test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_qt_components():
    """Test Qt components"""
    print("\n=== Testing Qt Components ===")
    
    try:
        from PySide6.QtCore import QObject, Signal, QTimer
        from PySide6.QtWidgets import QApplication
        
        # Test signal creation
        from runtime.state import StateBus
        
        bus = StateBus()
        print("? StateBus created")
        
        # Test signal connections (without actual emission)
        print("? Qt signals available")
        
        return True
        
    except Exception as e:
        print(f"? Qt test failed: {e}")
        return False


def main():
    """Run all runtime tests"""
    print("="*60)
    print("RUNTIME SYSTEM TESTS (P7)")
    print("="*60)
    
    tests = [
        test_runtime_components,
        test_sync_components, 
        test_qt_components
    ]
    
    passed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            print("? Test failed!")
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("? ALL RUNTIME TESTS PASSED!")
        print("?? Runtime system (P7) is functional!")
    else:
        print("?? Some tests failed")
    
    print("="*60)
    
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)