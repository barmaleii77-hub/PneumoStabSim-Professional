"""
Simplified runtime init without physics imports
"""

from .state import (
    StateSnapshot,
    FrameState,
    WheelState,
    LineState,
    TankState,
    SystemAggregates,
    StateBus,
)

from .sync import (
    LatestOnlyQueue,
    PerformanceMetrics,
    TimingAccumulator,
    ThreadSafeCounter,
    create_state_queue,
)

# Skip sim_loop import for now due to physics dependencies
# from .sim_loop import (
#     PhysicsWorker, SimulationManager
# )

__all__ = [
    # State management
    "StateSnapshot",
    "FrameState",
    "WheelState",
    "LineState",
    "TankState",
    "SystemAggregates",
    "StateBus",
    # Synchronization
    "LatestOnlyQueue",
    "PerformanceMetrics",
    "TimingAccumulator",
    "ThreadSafeCounter",
    "create_state_queue",
    # Simulation loop - disabled for now
    # 'PhysicsWorker', 'SimulationManager'
]
