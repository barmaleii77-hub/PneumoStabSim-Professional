from __future__ import annotations

import sys
from types import ModuleType

import pytest

from tools import ci_tasks


def _make_dummy_module(name: str) -> ModuleType:
    module = ModuleType(name)
    return module


def test_resolve_qml_linter_uses_configured_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    """A configured linter command takes precedence when it exists."""

    monkeypatch.setenv("QML_LINTER", "custom-qmllint")

    def fake_which(binary: str) -> str | None:
        return "/opt/bin/custom-qmllint" if binary == "custom-qmllint" else None

    monkeypatch.setattr(ci_tasks.shutil, "which", fake_which)

    command = ci_tasks._resolve_qml_linter()

    assert command == ("/opt/bin/custom-qmllint",)


def test_resolve_qml_linter_falls_back_to_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """When binaries are missing the PySide6 module fallback is used."""

    monkeypatch.delenv("QML_LINTER", raising=False)
    monkeypatch.setattr(ci_tasks.shutil, "which", lambda _: None)

    pyside_pkg = _make_dummy_module("PySide6")
    scripts_pkg = _make_dummy_module("PySide6.scripts")
    qmllint_module = _make_dummy_module("PySide6.scripts.qmllint")

    pyside_pkg.__path__ = []  # type: ignore[attr-defined]
    scripts_pkg.__path__ = []  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "PySide6", pyside_pkg)
    monkeypatch.setitem(sys.modules, "PySide6.scripts", scripts_pkg)
    monkeypatch.setitem(sys.modules, "PySide6.scripts.qmllint", qmllint_module)

    command = ci_tasks._resolve_qml_linter()

    assert command == (sys.executable, "-m", "PySide6.scripts.qmllint")


def test_resolve_qml_linter_raises_when_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """A clear error is raised when no linter binary or module can be resolved."""

    monkeypatch.delenv("QML_LINTER", raising=False)
    monkeypatch.setattr(ci_tasks.shutil, "which", lambda _: None)
    blocked_pkg = _make_dummy_module("PySide6")
    monkeypatch.setitem(sys.modules, "PySide6", blocked_pkg, raising=False)
    monkeypatch.delitem(sys.modules, "PySide6.scripts", raising=False)
    monkeypatch.delitem(sys.modules, "PySide6.scripts.qmllint", raising=False)

    with pytest.raises(ci_tasks.TaskError) as excinfo:
        ci_tasks._resolve_qml_linter()

    assert "Install Qt tooling" in str(excinfo.value)
