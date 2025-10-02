"""
Simple test for runtime system
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_basic_runtime():
    """Test basic runtime imports"""
    print("Testing runtime imports...")
    
    try:
        from runtime.state import StateSnapshot, StateBus
        print("? State management imported")
        
        from runtime.sync import LatestOnlyQueue, PerformanceMetrics
        print("? Synchronization imported")
        
        # Test state snapshot creation
        snapshot = StateSnapshot()
        print(f"? StateSnapshot created: step={snapshot.step_number}")
        
        # Test queue
        queue = LatestOnlyQueue()
        queue.put_nowait("test")
        result = queue.get_nowait()
        print(f"? LatestOnlyQueue working: {result}")
        
        return True
        
    except Exception as e:
        print(f"? Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_basic_runtime() 
    print("Runtime test:", "PASSED" if success else "FAILED")
    exit(0 if success else 1)