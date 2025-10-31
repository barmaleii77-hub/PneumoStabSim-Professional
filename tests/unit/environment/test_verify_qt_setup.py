from __future__ import annotations

import ctypes
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools" / "environment" / "verify_qt_setup.py"

spec = importlib.util.spec_from_file_location(
    "tools.environment.verify_qt_setup", MODULE_PATH
)
assert spec is not None and spec.loader is not None
verify_qt_setup = importlib.util.module_from_spec(spec)
sys.modules.setdefault(spec.name, verify_qt_setup)
spec.loader.exec_module(verify_qt_setup)

ProbeResult = verify_qt_setup.ProbeResult
_check_opengl_runtime = verify_qt_setup._check_opengl_runtime


def test_check_opengl_runtime_reports_success(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux", raising=False)

    loaded: list[str] = []

    def fake_cdll(name: str):
        loaded.append(name)
        if name == "libGL.so.1":
            return object()
        raise OSError("missing")

    monkeypatch.setattr(ctypes, "CDLL", fake_cdll)

    result = _check_opengl_runtime()
    assert isinstance(result, ProbeResult)
    assert result.ok
    assert "libGL.so.1" in result.message
    assert loaded[0] == "libGL.so.1"


def test_check_opengl_runtime_reports_install_hint(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux", raising=False)

    def fake_cdll(name: str):  # noqa: ARG001
        raise OSError("missing")

    monkeypatch.setattr(ctypes, "CDLL", fake_cdll)

    result = _check_opengl_runtime()
    assert isinstance(result, ProbeResult)
    assert not result.ok
    assert "libGL.so.1" in result.message
    assert "apt-get install -y libgl1" in result.message
