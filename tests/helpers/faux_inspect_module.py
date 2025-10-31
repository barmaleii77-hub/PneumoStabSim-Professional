"""Хелперы, имитирующие модуль типа ``inspect`` с вызовом ``unwrap``."""

from __future__ import annotations
from typing import Any


def unwrap(module: Any) -> Any:
    """Return the ``__wrapped__`` attribute used by compatibility tests."""

    return getattr(module, "__wrapped__")


fake_unwrap = unwrap

__all__ = ["fake_unwrap"]
