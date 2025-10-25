"""
Synchronization utilities for thread-safe communication
Provides latest-only queue and performance monitoring
"""

import queue
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


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

    def get_stats(self) -> Dict[str, float]:
        """Get queue statistics

        Returns:
            Dictionary with put/get/dropped counts
        """
        with self._lock:
            return {
                "put_count": float(self._put_count),
                "get_count": float(self._get_count),
                "dropped_count": float(self._dropped_count),
                "efficiency": self._get_count / max(self._put_count, 1),
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
    min_step_time: float = float("inf")
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
    realtime_factor: float = 1.0  # sim_time / real_time
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
            "steps": self.total_steps,
            "avg_step_time_ms": self.avg_step_time * 1000,
            "fps_actual": self.get_fps(),
            "fps_target": self.get_target_fps(),
            "realtime_factor": self.realtime_factor,
            "frames_dropped": self.frames_dropped,
            "integration_failures": self.integration_failures,
            "efficiency": (self.total_steps - self.frames_dropped)
            / max(self.total_steps, 1),
        }


class TimingAccumulator:
    """Fixed timestep accumulator for stable physics.

    Implements the "Fix Your Timestep" pattern for decoupling the physics
    timestep from the rendering framerate.
    """

    def __init__(
        self,
        target_dt: float = 0.001,
        max_steps_per_frame: int = 10,
        max_frame_time: float = 0.05,
    ) -> None:
        self.target_dt = float(target_dt)
        self.accumulator = 0.0
        self.last_time = time.perf_counter()
        self.max_steps_per_frame = max(1, int(max_steps_per_frame))
        self.max_frame_time = float(max_frame_time)

        # Statistics
        self.steps_taken = 0
        self.frames_processed = 0
        self.total_real_time = 0.0
        self.total_sim_time = 0.0

    def update(self) -> int:
        """Update accumulator and return number of physics steps to take.

        Returns:
            Number of physics steps to execute (0 or more).
        """

        current_time = time.perf_counter()
        real_dt = current_time - self.last_time
        self.last_time = current_time

        # Clamp maximum frame time to prevent spiral of death
        if real_dt > self.max_frame_time:
            real_dt = self.max_frame_time

        self.accumulator += real_dt
        self.total_real_time += real_dt
        self.frames_processed += 1

        steps_to_take = 0
        while (
            self.accumulator >= self.target_dt
            and steps_to_take < self.max_steps_per_frame
        ):
            self.accumulator -= self.target_dt
            self.total_sim_time += self.target_dt
            steps_to_take += 1

        self.steps_taken += steps_to_take
        return steps_to_take

    def get_interpolation_alpha(self) -> float:
        """Return interpolation factor for smooth rendering."""

        if self.target_dt <= 0:
            return 0.0
        return self.accumulator / self.target_dt

    def get_realtime_factor(self) -> float:
        """Return current real-time performance factor."""

        if self.total_real_time > 0:
            return self.total_sim_time / self.total_real_time
        return 1.0

    def reset(self) -> None:
        """Reset accumulator and statistics."""

        self.accumulator = 0.0
        self.last_time = time.perf_counter()
        self.steps_taken = 0
        self.frames_processed = 0
        self.total_real_time = 0.0
        self.total_sim_time = 0.0


class StateSnapshotBuffer:
    """Thread-safe ring buffer storing the latest state snapshots."""

    def __init__(self, maxlen: int = 2048) -> None:
        if maxlen <= 0:
            raise ValueError("Snapshot buffer size must be positive")

        self._buffer: deque[Any] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    @property
    def capacity(self) -> int:
        """Return the maximum number of snapshots retained."""

        # ``maxlen`` is never ``None`` because we validate in ``__init__``.
        return int(self._buffer.maxlen or 0)

    def append(self, snapshot: Any) -> None:
        """Add a snapshot, discarding the oldest if capacity is exceeded."""

        with self._lock:
            self._buffer.append(snapshot)

    def extend(self, snapshots: Iterable[Any]) -> None:
        """Append multiple snapshots preserving order."""

        with self._lock:
            for snapshot in snapshots:
                self._buffer.append(snapshot)

    def clear(self) -> None:
        """Remove all buffered snapshots."""

        with self._lock:
            self._buffer.clear()

    def to_list(self) -> List[Any]:
        """Return a copy of buffered snapshots in insertion order."""

        with self._lock:
            return list(self._buffer)

    def latest(self) -> Optional[Any]:
        """Return the most recent snapshot or ``None`` if empty."""

        with self._lock:
            if self._buffer:
                return self._buffer[-1]
            return None

    def __len__(self) -> int:  # pragma: no cover - trivial
        with self._lock:
            return len(self._buffer)


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
    "LatestOnlyQueue",
    "PerformanceMetrics",
    "TimingAccumulator",
    "StateSnapshotBuffer",
    "ThreadSafeCounter",
    "create_state_queue",
]
