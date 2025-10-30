"""Regression tests for lazy packages exposing ``__wrapped__`` safely."""

from __future__ import annotations

import importlib
import inspect

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
