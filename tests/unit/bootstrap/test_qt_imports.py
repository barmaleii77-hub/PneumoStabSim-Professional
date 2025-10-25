import sys
import types

import pytest

from src.bootstrap.qt_imports import safe_import_qt


def test_safe_import_qt_missing_libgl(monkeypatch, capsys):
    recorded_errors: list[str] = []

    def log_error(message: str) -> None:
        recorded_errors.append(message)

    def log_warning(message: str) -> None:  # noqa: ARG001
        pass

    fake_package = types.ModuleType("PySide6")
    fake_package.__path__ = []  # type: ignore[attr-defined]

    def _raise_import_error(name: str) -> None:  # noqa: ARG001
        raise ImportError(
            "libGL.so.1: cannot open shared object file: No such file or directory"
        )

    widgets_module = types.ModuleType("PySide6.QtWidgets")
    widgets_module.__getattr__ = _raise_import_error  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "PySide6", fake_package, raising=False)
    monkeypatch.setitem(sys.modules, "PySide6.QtWidgets", widgets_module, raising=False)

    with pytest.raises(SystemExit):
        safe_import_qt(log_warning, log_error)

    stderr = capsys.readouterr().err
    assert "libGL.so.1" in stderr
    assert "Install a Mesa/OpenGL package" in stderr
    assert recorded_errors
    assert "libGL.so.1" in recorded_errors[0]
