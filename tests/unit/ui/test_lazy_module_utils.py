"""Tests for the heuristics guarding lazy module ``__getattr__`` hooks."""

from __future__ import annotations

import inspect

from src.ui._lazy_module_utils import should_suppress_wrapped


class _ProbeBase:
    calls: list[bool]

    def __init__(self) -> None:
        self.calls = []

    def _record(self) -> bool:
        result = should_suppress_wrapped()
        self.calls.append(result)
        return result

    def __getattr__(self, name: str):  # pragma: no cover - invoked dynamically
        if name == "__wrapped__":
            self._record()
            raise AttributeError(name)
        raise AttributeError(name)


def test_should_suppress_wrapped_only_for_inspect() -> None:
    """``inspect.unwrap`` probes ``__wrapped__`` via ``hasattr``."""

    probe = _ProbeBase()
    returned = inspect.unwrap(probe)

    assert returned is probe
    assert probe.calls == [True]


def test_should_not_suppress_for_direct_hasattr() -> None:
    """Direct ``hasattr`` callers should receive the module object."""

    probe = _ProbeBase()
    hasattr(probe, "__wrapped__")

    assert probe.calls == [False]
