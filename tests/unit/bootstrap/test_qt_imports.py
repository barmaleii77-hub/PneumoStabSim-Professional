import sys
import types

from src.bootstrap.qt_imports import safe_import_qt
from src.bootstrap.headless_qt import HeadlessApplication, HeadlessTimer


def test_safe_import_qt_missing_libgl(monkeypatch, capsys):
    recorded_errors: list[str] = []

    def log_error(message: str) -> None:
        recorded_errors.append(message)

    recorded_warnings: list[str] = []

    def log_warning(message: str) -> None:
        recorded_warnings.append(message)

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

    QApplication, message_handler, Qt, QTimer = safe_import_qt(log_warning, log_error)

    stderr = capsys.readouterr().err
    assert "libGL.so.1" not in stderr  # сообщение теперь уходит в логгер

    assert recorded_errors
    assert "libGL.so.1" in recorded_errors[0]

    assert recorded_warnings
    assert "headless diagnostics mode" in recorded_warnings[-1]

    assert QApplication is HeadlessApplication
    assert isinstance(Qt.headless_reason, str)
    assert QTimer is HeadlessTimer
    assert message_handler is not None


def test_safe_import_qt_handles_non_callable_loggers(monkeypatch, capsys):
    fake_package = types.ModuleType("PySide6")
    fake_package.__path__ = []  # type: ignore[attr-defined]

    def _raise_import_error(name: str) -> None:  # noqa: ARG001
        raise ImportError("libGL.so.1: cannot open shared object file")

    widgets_module = types.ModuleType("PySide6.QtWidgets")
    widgets_module.__getattr__ = _raise_import_error  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "PySide6", fake_package, raising=False)
    monkeypatch.setitem(sys.modules, "PySide6.QtWidgets", widgets_module, raising=False)

    QApplication, message_handler, Qt, QTimer = safe_import_qt(True, False)  # type: ignore[arg-type]

    stderr = capsys.readouterr().err
    assert "[safe_import_qt:warning]" in stderr
    assert "[safe_import_qt:error]" in stderr

    assert QApplication is HeadlessApplication
    assert QTimer is HeadlessTimer
    assert isinstance(Qt.headless_reason, str)
    assert message_handler is not None
