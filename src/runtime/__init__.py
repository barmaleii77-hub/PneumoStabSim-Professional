"""
Runtime simulation management
Provides thread-safe simulation loop, state management, and synchronization
"""

from .state import (
    StateSnapshot, FrameState, WheelState, LineState, TankState,
    SystemAggregates, StateBus
)

from .sync import (
    LatestOnlyQueue, PerformanceMetrics, TimingAccumulator,
    ThreadSafeCounter, create_state_queue
)

from .sim_loop import (
    PhysicsWorker, SimulationManager
)

__all__ = [
    # State management
    'StateSnapshot', 'FrameState', 'WheelState', 'LineState', 'TankState',
    'SystemAggregates', 'StateBus',
    
    # Synchronization
    'LatestOnlyQueue', 'PerformanceMetrics', 'TimingAccumulator',
    'ThreadSafeCounter', 'create_state_queue',
    
    # Simulation loop
    'PhysicsWorker', 'SimulationManager'
]