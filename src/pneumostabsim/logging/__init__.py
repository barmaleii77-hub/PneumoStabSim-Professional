"""Logging utilities specific to PneumoStabSim."""

from .error_hooks import ErrorHookManager, install_error_hooks

__all__ = ["ErrorHookManager", "install_error_hooks"]
