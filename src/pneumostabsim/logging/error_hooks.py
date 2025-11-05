"""Compatibility shim for legacy ``pneumostabsim.logging`` imports."""

from __future__ import annotations

from src.infrastructure.logging.error_hooks import (  # noqa: F401
    ErrorHookManager,
    install_error_hooks,
)

__all__ = ["ErrorHookManager", "install_error_hooks"]
