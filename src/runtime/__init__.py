"""
Runtime simulation management
Provides thread-safe simulation loop, state management, and synchronization
"""

"""Runtime simulation management with lazy entry points."""

from importlib import import_module
from typing import TYPE_CHECKING

from .state import (
    FrameState,
    LineState,
    StateBus,
    StateSnapshot,
    SystemAggregates,
    TankState,
    WheelState,
)

from .sync import (
    LatestOnlyQueue,
    PerformanceMetrics,
    ThreadSafeCounter,
    TimingAccumulator,
    create_state_queue,
)

if TYPE_CHECKING:  # pragma: no cover - import guard for type checkers
    from .sim_loop import PhysicsWorker, SimulationManager

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
    # Simulation loop
    "PhysicsWorker",
    "SimulationManager",
]


def __getattr__(name: str):
    if name in {"PhysicsWorker", "SimulationManager"}:
        module = import_module(".sim_loop", __name__)
        attr = getattr(module, name)
        globals()[name] = attr
        return attr
    raise AttributeError(name)
