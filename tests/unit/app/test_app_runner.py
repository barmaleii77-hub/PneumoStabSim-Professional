from __future__ import annotations

import argparse
import enum
import os
import types
from dataclasses import dataclass
from pathlib import Path

import pytest

from src.app_runner import ApplicationRunner


@dataclass
class _DummyAppInstance:
    """Minimal QApplication stub used to drive :class:`ApplicationRunner`."""

    exec_result: int = 0

    is_headless: bool = False
    headless_reason: str | None = None

    def setApplicationName(self, _: str) -> None:  # pragma: no cover - trivial
        pass

    def setApplicationVersion(self, _: str) -> None:  # pragma: no cover - trivial
        pass

    def setOrganizationName(self, _: str) -> None:  # pragma: no cover - trivial
        pass

    def exec(self) -> int:
        return self.exec_result

    def quit(self) -> None:  # pragma: no cover - trivial
        pass


class _DummyQtModule:
    """Subset of the Qt module interface consumed by the runner."""

    class HighDpiScaleFactorRoundingPolicy:  # pragma: no cover - behaviour mocked
        PassThrough = object()

    is_headless = False
    headless_reason = None


class _DummyLogger:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def error(
        self, message: str, *args, **kwargs
    ) -> None:  # pragma: no cover - formatting not required
        self.messages.append(message)


class _DummyQQuickWidget:
    class Status(enum.IntEnum):
        Null = 0
        Ready = 1
        Loading = 2
        Error = 3

    def __init__(self, status: Status, errors: list[str] | None = None) -> None:
        self._status = status
        self._errors = errors or []

    def status(self):  # pragma: no cover - simple proxy
        return self._status

    def errors(self):  # pragma: no cover - simple proxy
        return list(self._errors)


def _build_runner(
    monkeypatch: pytest.MonkeyPatch, *, exec_result: int = 0
) -> tuple[ApplicationRunner, list[str]]:
    """Return a runner instance prepared for deterministic testing."""

    runner = ApplicationRunner(
        object, lambda *args, **kwargs: None, _DummyQtModule, object
    )

    # Prevent side effects from subsystems that talk to the real environment.
    monkeypatch.setattr(runner, "setup_logging", lambda verbose_console: None)
    monkeypatch.setattr(runner, "setup_high_dpi", lambda: None)

    def _fake_create_application() -> None:
        app = _DummyAppInstance(exec_result)
        runner.app_instance = app
        runner._is_headless = app.is_headless
        runner._headless_reason = app.headless_reason

    monkeypatch.setattr(runner, "create_application", _fake_create_application)
    monkeypatch.setattr(runner, "_validate_settings_file", lambda: None)
    monkeypatch.setattr(runner, "create_main_window", lambda: None)
    monkeypatch.setattr(runner, "setup_signals", lambda: None)
    monkeypatch.setattr(runner, "setup_test_mode", lambda enabled: None)

    diagnostics_calls: list[str] = []

    def _record_diagnostics() -> None:
        diagnostics_calls.append("called")

    monkeypatch.setattr("src.diagnostics.logs.run_log_diagnostics", _record_diagnostics)

    return runner, diagnostics_calls


def _make_args(*, diag: bool = False) -> argparse.Namespace:
    return argparse.Namespace(verbose=False, test_mode=False, diag=diag)


def test_run_skips_post_diagnostics_without_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, calls = _build_runner(monkeypatch)

    exit_code = runner.run(_make_args(diag=False))

    assert exit_code == 0
    assert calls == []


def test_run_executes_diagnostics_when_flag_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, calls = _build_runner(monkeypatch)

    exit_code = runner.run(_make_args(diag=True))

    assert exit_code == 0
    assert calls == ["called"]


def test_run_executes_diagnostics_on_fatal_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, calls = _build_runner(monkeypatch)

    def _failing_main_window() -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(runner, "create_main_window", _failing_main_window)

    exit_code = runner.run(_make_args(diag=False))

    assert exit_code == 1
    assert calls == ["called"]


def test_run_executes_diagnostics_when_env_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PSS_POST_DIAG_TRACE", "auto")
    runner, calls = _build_runner(monkeypatch)

    exit_code = runner.run(_make_args(diag=False))

    assert exit_code == 0
    assert calls == ["called"]


def test_check_qml_initialization_logs_engine_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PSS_POST_DIAG_TRACE", raising=False)
    runner = ApplicationRunner(
        object, lambda *args, **kwargs: None, _DummyQtModule, object
    )
    logger = _DummyLogger()
    runner.app_logger = logger

    widget = _DummyQQuickWidget(
        _DummyQQuickWidget.Status.Error,
        ["file:///assets/qml/main.qml:12 Type Foo unavailable"],
    )
    window = types.SimpleNamespace(_qquick_widget=widget, _qml_root_object=None)

    runner._check_qml_initialization(window)

    env_value = os.environ.get("PSS_POST_DIAG_TRACE", "")
    assert "qml-check:qml-engine-error" in env_value.split("|")
    assert logger.messages
    assert "Foo unavailable" in logger.messages[0]


def test_check_qml_initialization_detects_missing_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PSS_POST_DIAG_TRACE", raising=False)
    runner = ApplicationRunner(
        object, lambda *args, **kwargs: None, _DummyQtModule, object
    )
    logger = _DummyLogger()
    runner.app_logger = logger

    window = types.SimpleNamespace(_qquick_widget=object(), _qml_root_object=None)

    runner._check_qml_initialization(window)

    env_value = os.environ.get("PSS_POST_DIAG_TRACE", "")
    assert "qml-check:status-missing" in env_value.split("|")
    assert any("status()" in message for message in logger.messages)


def test_check_qml_initialization_passes_when_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PSS_POST_DIAG_TRACE", raising=False)
    runner = ApplicationRunner(
        object, lambda *args, **kwargs: None, _DummyQtModule, object
    )
    logger = _DummyLogger()
    runner.app_logger = logger

    widget = _DummyQQuickWidget(_DummyQQuickWidget.Status.Ready)
    window = types.SimpleNamespace(_qquick_widget=widget, _qml_root_object=object())

    runner._check_qml_initialization(window)

    assert os.environ.get("PSS_POST_DIAG_TRACE") in (None, "")
    assert logger.messages == []


def test_run_schema_validation_skips_when_validator_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = ApplicationRunner(
        object, lambda *args, **kwargs: None, _DummyQtModule, object
    )
    project_root = Path(__file__).resolve().parents[4]
    validator_path = project_root / "tools" / "validate_settings.py"
    real_exists = Path.exists

    def _fake_exists(self: Path) -> bool:  # pragma: no cover - simple shim
        if self == validator_path:
            return False
        return real_exists(self)

    monkeypatch.setattr(Path, "exists", _fake_exists, raising=False)
    schema_path = tmp_path / "schema.json"
    schema_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(runner, "_resolve_schema_path", lambda: schema_path)

    cfg_path = tmp_path / "settings.json"
    cfg_path.write_text("{}", encoding="utf-8")

    runner._run_schema_validation(cfg_path)


def test_run_schema_validation_raises_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = ApplicationRunner(
        object, lambda *args, **kwargs: None, _DummyQtModule, object
    )
    project_root = Path(__file__).resolve().parents[4]
    validator_path = project_root / "tools" / "validate_settings.py"
    real_exists = Path.exists

    def _exists(self: Path) -> bool:  # pragma: no cover - shim
        if self == validator_path:
            return True
        return real_exists(self)

    monkeypatch.setattr(Path, "exists", _exists, raising=False)
    monkeypatch.setattr(
        runner, "_resolve_schema_path", lambda: validator_path.with_suffix(".schema")
    )

    def _fake_run(*_args, **_kwargs):
        return types.SimpleNamespace(returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr("subprocess.run", _fake_run)

    with pytest.raises(RuntimeError) as exc:
        runner._run_schema_validation(validator_path.with_suffix(".json"))

    assert "exit code 1" in str(exc.value)


def test_run_schema_validation_wraps_os_error(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = ApplicationRunner(
        object, lambda *args, **kwargs: None, _DummyQtModule, object
    )
    project_root = Path(__file__).resolve().parents[4]
    validator_path = project_root / "tools" / "validate_settings.py"

    monkeypatch.setattr(Path, "exists", lambda _self: True, raising=False)
    monkeypatch.setattr(
        runner, "_resolve_schema_path", lambda: validator_path.with_suffix(".schema")
    )

    def _raise(*_args, **_kwargs):
        raise OSError("not executable")

    monkeypatch.setattr("subprocess.run", _raise)

    with pytest.raises(RuntimeError) as exc:
        runner._run_schema_validation(validator_path.with_suffix(".json"))

    assert "Failed to execute settings validator" in str(exc.value)
