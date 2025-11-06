from __future__ import annotations

import ctypes
import importlib.util
import sys
from pathlib import Path

import builtins

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
run_smoke_check = verify_qt_setup.run_smoke_check


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


def test_allow_missing_runtime_handles_libxkbcommon(monkeypatch, tmp_path):
    """Отсутствие libxkbcommon.so.0 не должно валить проверку при допуске."""

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: D401
        if name.startswith("PySide6"):
            raise ImportError(
                "libxkbcommon.so.0: cannot open shared object file: No such file or directory"
            )
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    # Допускаем отсутствие Qt рантайма
    code = run_smoke_check(
        expected_version="6.10", expected_platform=None, report_dir=tmp_path, allow_missing_runtime=True
    )
    assert code == 0

    logs = sorted(tmp_path.glob("qt_environment_*.log"))
    assert logs, "report file was not written"
    content = logs[-1].read_text(encoding="utf-8")
    assert "libxkbcommon.so.0" in content
    assert "libxkbcommon0" in content or "Install the system package 'libxkbcommon0'" in content


def test_strict_missing_runtime_fails_for_libxkbcommon(monkeypatch, tmp_path):
    """Без допуска отсутствующий libxkbcommon должен приводить к коду 1."""

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("PySide6"):
            raise ImportError(
                "libxkbcommon.so.0: cannot open shared object file: No such file or directory"
            )
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    code = run_smoke_check(
        expected_version="6.10", expected_platform=None, report_dir=tmp_path, allow_missing_runtime=False
    )
    assert code == 1
