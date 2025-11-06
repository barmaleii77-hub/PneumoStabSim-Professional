from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import pytest

from tools import ci_tasks


def _make_dummy_module(name: str) -> ModuleType:
    module = ModuleType(name)
    return module


def test_resolve_qml_linter_uses_configured_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A configured linter command takes precedence when it exists."""

    monkeypatch.setenv("QML_LINTER", "custom-qmllint")

    def fake_which(binary: str) -> str | None:
        return "/opt/bin/custom-qmllint" if binary == "custom-qmllint" else None

    monkeypatch.setattr(ci_tasks.shutil, "which", fake_which)

    command = ci_tasks._resolve_qml_linter()

    assert command == ("/opt/bin/custom-qmllint",)


def test_resolve_qml_linter_falls_back_to_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


def test_resolve_qml_linter_raises_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


class _RecorderStub:
    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    def start(self, root_command: str) -> None:  # pragma: no cover - not used
        self.records.clear()

    def finalize(self, success: bool) -> None:  # pragma: no cover - not used
        return

    def record(
        self,
        *,
        name: str,
        printable_command: str,
        returncode: int,
        log_path: Path | None,
    ) -> None:
        self.records.append(
            {
                "name": name,
                "command": printable_command,
                "returncode": returncode,
                "log_path": log_path,
            }
        )


def _prepare_qml_lint_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[_RecorderStub, Path]:
    recorder = _RecorderStub()
    quality_root = tmp_path / "reports" / "quality"

    monkeypatch.setattr(ci_tasks, "RECORDER", recorder)
    monkeypatch.setattr(ci_tasks, "QUALITY_REPORT_ROOT", quality_root)
    monkeypatch.setattr(ci_tasks, "PROJECT_ROOT", tmp_path)

    target = tmp_path / "Dummy.qml"
    target.write_text("Item {}\n", encoding="utf-8")

    monkeypatch.setattr(ci_tasks, "_collect_qml_targets", lambda: [target])
    monkeypatch.setattr(
        ci_tasks,
        "_resolve_qml_linter",
        lambda: (sys.executable, "-c", "print('ok from qmllint')"),
    )

    return recorder, quality_root


def test_task_qml_lint_creates_log_artifact_by_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    recorder, quality_root = _prepare_qml_lint_environment(monkeypatch, tmp_path)
    monkeypatch.delenv("CI_TASKS_QML_LOG_ARTIFACTS", raising=False)

    ci_tasks.task_qml_lint()

    log_file = quality_root / "qmllint.log"
    assert log_file.exists()
    assert "## Target: Dummy.qml" in log_file.read_text(encoding="utf-8")
    assert recorder.records
    assert recorder.records[0]["log_path"] == log_file


def test_task_qml_lint_skips_log_artifact_when_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    recorder, quality_root = _prepare_qml_lint_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("CI_TASKS_QML_LOG_ARTIFACTS", "0")

    ci_tasks.task_qml_lint()

    assert not (quality_root / "qmllint.log").exists()
    assert recorder.records
    assert recorder.records[0]["log_path"] is None


def test_task_qml_lint_rejects_invalid_log_flag(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _prepare_qml_lint_environment(monkeypatch, tmp_path)
    monkeypatch.setenv("CI_TASKS_QML_LOG_ARTIFACTS", "definitely")

    with pytest.raises(ci_tasks.TaskError):
        ci_tasks.task_qml_lint()
