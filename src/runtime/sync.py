"""
Synchronization utilities for thread-safe communication
Provides latest-only queue and performance monitoring
"""

import queue
import threading
import time
from typing import Optional, Any, Dict
from dataclasses import dataclass, field


class LatestOnlyQueue:
    """Thread-safe queue that keeps only the latest item
    
    Based on queue.Queue but with "drop old, keep latest" semantics.
    When queue is full (maxsize=1), putting a new item drops the old one.
    """
    
    def __init__(self):
        self._queue = queue.Queue(maxsize=1)
        self._dropped_count = 0
        self._put_count = 0
        self._get_count = 0
        self._lock = threading.Lock()
    
    def put_nowait(self, item: Any) -> bool:
        """Put item without blocking, dropping old item if necessary
        
        Args:
            item: Item to put in queue
            
        Returns:
            True if item was put, False if queue operations failed
        """
        with self._lock:
            self._put_count += 1
            
            try:
                # If queue is full, remove old item first
                if self._queue.full():
                    try:
                        self._queue.get_nowait()
                        self._dropped_count += 1
                    except queue.Empty:
                        pass  # Race condition, queue became empty
                
                # Put new item
                self._queue.put_nowait(item)
                return True
                
            except queue.Full:
                # Should not happen with maxsize=1 and get_nowait above
                self._dropped_count += 1
                return False
    
    def get_nowait(self) -> Optional[Any]:
        """Get item without blocking
        
        Returns:
            Item from queue or None if empty
        """
        with self._lock:
            try:
                item = self._queue.get_nowait()
                self._get_count += 1
                return item
            except queue.Empty:
                return None
    
    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics
        
        Returns:
            Dictionary with put/get/dropped counts
        """
        with self._lock:
            return {
                'put_count': self._put_count,
                'get_count': self._get_count,
                'dropped_count': self._dropped_count,
                'efficiency': self._get_count / max(self._put_count, 1)
            }
    
    def reset_stats(self):
        """Reset all statistics counters"""
        with self._lock:
            self._put_count = 0
            self._get_count = 0
            self._dropped_count = 0
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return self._queue.empty()
    
    def qsize(self) -> int:
        """Get queue size (0 or 1)"""
        return self._queue.qsize()


@dataclass
class PerformanceMetrics:
    """Performance metrics for physics loop monitoring"""
    # Timing statistics
    total_steps: int = 0
    total_time: float = 0.0
    min_step_time: float = float('inf')
    max_step_time: float = 0.0
    avg_step_time: float = 0.0
    
    # Timestep analysis
    target_dt: float = 0.001
    actual_dt_sum: float = 0.0
    dt_variance: float = 0.0
    
    # Performance counters
    frames_dropped: int = 0
    integration_failures: int = 0
    queue_overruns: int = 0
    
    # Real-time factors
    realtime_factor: float = 1.0       # sim_time / real_time
    cpu_usage_percent: float = 0.0
    
    # Last update timestamp
    last_update: float = field(default_factory=time.perf_counter)
    
    def update_step_time(self, step_time: float):
        """Update step timing statistics"""
        self.total_steps += 1
        self.total_time += step_time
        
        self.min_step_time = min(self.min_step_time, step_time)
        self.max_step_time = max(self.max_step_time, step_time)
        self.avg_step_time = self.total_time / self.total_steps
        
        # Update variance (simplified running calculation)
        if self.total_steps > 1:
            delta = step_time - self.avg_step_time
            self.dt_variance += delta * delta / self.total_steps
    
    def update_realtime_factor(self, sim_dt: float, real_dt: float):
        """Update real-time performance factor"""
        if real_dt > 0:
            self.realtime_factor = sim_dt / real_dt
            self.actual_dt_sum += real_dt
    
    def get_fps(self) -> float:
        """Get effective physics FPS"""
        if self.avg_step_time > 0:
            return 1.0 / self.avg_step_time
        return 0.0
    
    def get_target_fps(self) -> float:
        """Get target physics FPS"""
        return 1.0 / self.target_dt
    
    def is_realtime(self, tolerance: float = 0.1) -> bool:
        """Check if simulation is running in real-time
        
        Args:
            tolerance: Allowed deviation from 1.0 realtime factor
            
        Returns:
            True if within tolerance of real-time
        """
        return abs(self.realtime_factor - 1.0) <= tolerance
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary for logging/display"""
        return {
            'steps': self.total_steps,
            'avg_step_time_ms': self.avg_step_time * 1000,
            'fps_actual': self.get_fps(),
            'fps_target': self.get_target_fps(),
            'realtime_factor': self.realtime_factor,
            'frames_dropped': self.frames_dropped,
            'integration_failures': self.integration_failures,
            'efficiency': (self.total_steps - self.frames_dropped) / max(self.total_steps, 1)
        }


class TimingAccumulator:
    """Fixed timestep accumulator for stable physics
    
    Implements the "Fix Your Timestep" pattern for decoupling
    physics timestep from rendering framerate.
    """
    
    def __init__(self, target_dt: float = 0.001):
        self.target_dt = target_dt
        self.accumulator = 0.0
        self.last_time = time.perf_counter()
        self.max_steps_per_frame = 10  # Prevent spiral of death
        
        # Statistics
        self.steps_taken = 0
        self.frames_processed = 0
        self.total_real_time = 0.0
        self.total_sim_time = 0.0
    
    def update(self) -> int:
        """Update accumulator and return number of physics steps to take
        
        Returns:
            Number of physics steps to execute (0 or more)
        """
        current_time = time.perf_counter()
        real_dt = current_time - self.last_time
        self.last_time = current_time
        
        # Clamp maximum frame time to prevent spiral of death
        if real_dt > 0.05:  # 50ms max frame time
            real_dt = 0.05
        
        self.accumulator += real_dt
        self.total_real_time += real_dt
        self.frames_processed += 1
        
        # Calculate number of steps to take
        steps_to_take = 0
        
        while self.accumulator >= self.target_dt and steps_to_take < self.max_steps_per_frame:
            self.accumulator -= self.target_dt
            self.total_sim_time += self.target_dt
            steps_to_take += 1
        
        self.steps_taken += steps_to_take
        return steps_to_take
    
    def get_interpolation_alpha(self) -> float:
        """Get interpolation factor for smooth rendering
        
        Returns:
            Alpha value (0.0 to 1.0) for interpolating between physics states
        """
        return self.accumulator / self.target_dt
    
    def get_realtime_factor(self) -> float:
        """Get current real-time performance factor"""
        if self.total_real_time > 0:
            return self.total_sim_time / self.total_real_time
        return 1.0
    
    def reset(self):
        """Reset accumulator and statistics"""
        self.accumulator = 0.0
        self.last_time = time.perf_counter()
        self.steps_taken = 0
        self.frames_processed = 0
        self.total_real_time = 0.0
        self.total_sim_time = 0.0


class ThreadSafeCounter:
    """Thread-safe counter for statistics"""
    
    def __init__(self, initial_value: int = 0):
        self._value = initial_value
        self._lock = threading.Lock()
    
    def increment(self, amount: int = 1) -> int:
        """Increment counter and return new value"""
        with self._lock:
            self._value += amount
            return self._value
    
    def decrement(self, amount: int = 1) -> int:
        """Decrement counter and return new value"""
        with self._lock:
            self._value -= amount
            return self._value
    
    def get(self) -> int:
        """Get current value"""
        with self._lock:
            return self._value
    
    def set(self, value: int) -> int:
        """Set value and return previous value"""
        with self._lock:
            old_value = self._value
            self._value = value
            return old_value
    
    def reset(self) -> int:
        """Reset to zero and return previous value"""
        return self.set(0)


# Convenience function for creating latest-only queue
def create_state_queue() -> LatestOnlyQueue:
    """Create a state queue optimized for StateSnapshot sharing"""
    return LatestOnlyQueue()


# Export main classes
__all__ = [
    'LatestOnlyQueue', 'PerformanceMetrics', 'TimingAccumulator', 
    'ThreadSafeCounter', 'create_state_queue'
]