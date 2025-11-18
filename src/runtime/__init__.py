"""Runtime simulation management
Provides thread-safe simulation loop, state management, and synchronization.

Lazy attribute resolution keeps heavy simulation modules out of the import path
until they are explicitly requested by the caller.
"""

from importlib import import_module

_LAZY_EXPORTS = {
    # State management
    "StateSnapshot": ".state",
    "FrameState": ".state",
    "WheelState": ".state",
    "LineState": ".state",
    "TankState": ".state",
    "SystemAggregates": ".state",
    "StateBus": ".state",
    # Synchronization
    "LatestOnlyQueue": ".sync",
    "PerformanceMetrics": ".sync",
    "TimingAccumulator": ".sync",
    "ThreadSafeCounter": ".sync",
    "create_state_queue": ".sync",
    # Simulation loop
    "PhysicsWorker": ".sim_loop",
    "SimulationManager": ".sim_loop",
}

__all__ = list(_LAZY_EXPORTS.keys())


def __getattr__(name: str):
    module_name = _LAZY_EXPORTS.get(name)
    if module_name:
        module = import_module(module_name, __name__)
        attr = getattr(module, name)
        globals()[name] = attr
        return attr
    raise AttributeError(name)
