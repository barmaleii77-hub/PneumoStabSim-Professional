"""Regression tests for lazy packages exposing ``__wrapped__`` safely."""

from __future__ import annotations

import importlib
import inspect
import sys

from tests.helpers.faux_inspect_module import fake_unwrap


def _assert_module_identity(module_name: str) -> None:
    module = importlib.import_module(module_name)

    # ``inspect.unwrap`` should return the actual module object so tooling that
    # relies on the function (including PySide6) continues to work.
    assert inspect.unwrap(module) is module

    # Direct attribute access should also be safe for consumers that do not
    # guard the ``module.__wrapped__`` lookup with ``try``/``except``.
    assert getattr(module, "__wrapped__") is module

    # Some third-party modules shadow ``inspect`` and provide their own
    # ``unwrap`` helper.  They expect ``module.__wrapped__`` to succeed without
    # raising ``AttributeError``.
    assert fake_unwrap(module) is module


def test_main_window_pkg_unwrap_returns_module() -> None:
    _assert_module_identity("src.ui.main_window_pkg")


def test_panels_unwrap_returns_module() -> None:
    _assert_module_identity("src.ui.panels")


def test_unwrap_handles_rebound_inspect(monkeypatch) -> None:
    modules = ["src.ui.panels", "src.ui.main_window_pkg"]

    original_unwrap = inspect.unwrap

    def custom_unwrap(func, *, stop=None):
        f = func
        memo = {id(f): f}
        recursion_limit = sys.getrecursionlimit()
        while not isinstance(func, type) and hasattr(func, "__wrapped__"):
            if stop is not None and stop(func):
                break
            func = func.__wrapped__
            identifier = id(func)
            if identifier in memo or len(memo) >= recursion_limit:
                raise ValueError(f"wrapper loop when unwrapping {f!r}")
            memo[identifier] = func
        return func

    monkeypatch.setattr(inspect, "unwrap", custom_unwrap)
    try:
        for module_name in modules:
            module = importlib.import_module(module_name)
            assert inspect.unwrap(module) is module
            assert getattr(module, "__wrapped__") is module
            if hasattr(module, "__dict__") and "__wrapped__" in module.__dict__:
                del module.__dict__["__wrapped__"]
    finally:
        monkeypatch.setattr(inspect, "unwrap", original_unwrap)


def test_custom_hasattr_probes_return_module() -> None:
    module = importlib.import_module("src.ui.main_window_pkg")

    def custom_hasattr(obj, name):
        getattr(obj, name)
        return True

    def custom_unwrap(target):
        if hasattr(target, "__wrapped__"):
            return target.__wrapped__
        return target

    namespace = custom_unwrap.__globals__
    original_hasattr = namespace.get("hasattr")
    try:
        namespace["hasattr"] = custom_hasattr
        assert custom_unwrap(module) is module
    finally:
        if original_hasattr is None:
            namespace.pop("hasattr", None)
        else:
            namespace["hasattr"] = original_hasattr
