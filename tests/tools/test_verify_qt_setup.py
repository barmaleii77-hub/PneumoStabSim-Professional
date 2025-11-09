from __future__ import annotations

from pathlib import Path

from tools.environment import verify_qt_setup as qt_env


def test_extract_missing_dependency_detects_known_library() -> None:
    message = "ImportError: libxkbcommon.so.0: cannot open shared object file"
    assert qt_env._extract_missing_dependency(message) == "libxkbcommon.so.0"


def test_run_smoke_check_warns_when_runtime_missing(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(qt_env, "_check_pyside_version", lambda expected: "6.10.0")
    monkeypatch.setattr(qt_env, "_check_environment_paths", lambda name: None)
    monkeypatch.setattr(qt_env, "_check_qlibraryinfo", lambda: Path("/qt/plugins"))

    def fake_probe(expected_platform):
        raise qt_env.QtRuntimeUnavailableError(
            qt_env._format_dependency_message("libxkbcommon.so.0"), fatal=False
        )

    monkeypatch.setattr(qt_env, "_probe_qt_runtime", fake_probe)
    monkeypatch.setattr(
        qt_env,
        "_check_opengl_runtime",
        lambda: qt_env.ProbeResult(True, "OpenGL runtime available"),
    )

    exit_code = qt_env.run_smoke_check("6.10", None, tmp_path)

    assert exit_code == 0
    report_path = tmp_path / "qt_environment_latest.log"
    contents = report_path.read_text(encoding="utf-8")
    assert "WARN" in contents
    assert "libxkbcommon.so.0" in contents
