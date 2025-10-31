from __future__ import annotations

import importlib
import sys
from typing import Callable
from unittest import mock

import pytest


def _purge_bootstrap_modules() -> None:
    """Remove cached ``src.bootstrap`` modules to force a fresh import."""

    for name in list(sys.modules):
        if name.startswith("src.bootstrap"):
            sys.modules.pop(name, None)


def test_safe_import_qt_reports_missing_numpy() -> None:
    """``safe_import_qt`` should surface a clear message when NumPy is absent."""

    _purge_bootstrap_modules()

    original_import = __import__

    def fake_import(
        name: str,
        globals_: dict[str, object] | None = None,
        locals_: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == "numpy":
            raise ModuleNotFoundError("No module named 'numpy'", name="numpy")
        return original_import(name, globals_, locals_, fromlist, level)

    with mock.patch("builtins.__import__", side_effect=fake_import):
        module = importlib.import_module("src.bootstrap")
        stub: Callable[[Callable[[str], None], Callable[[str], None]], object]
        stub = module.safe_import_qt

        with pytest.raises(ModuleNotFoundError) as excinfo:
            stub(lambda _: None, lambda _: None)

    assert "NumPy is required" in str(excinfo.value)
    assert "pip install -r requirements.txt" in str(excinfo.value)

    _purge_bootstrap_modules()
    importlib.import_module("src.bootstrap")
