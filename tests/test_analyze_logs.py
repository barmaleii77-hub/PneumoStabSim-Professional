import pytest

from analyze_logs import LogAnalyzer


@pytest.mark.usefixtures("tmp_path")
def test_log_analyzer_creates_missing_structure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    analyzer = LogAnalyzer()
    analyzer.run()

    logs_dir = tmp_path / "logs"
    assert logs_dir.is_dir()
    for subdir in LogAnalyzer.DEFAULT_SUBDIRS:
        assert (logs_dir / subdir).is_dir()
    assert (logs_dir / "run.log").exists()


def test_log_analyzer_respects_env_override(tmp_path, monkeypatch):
    target_dir = tmp_path / "custom-logs"
    monkeypatch.setenv("PNEUMOSTABSIM_LOGS_DIR", str(target_dir))
    monkeypatch.chdir(tmp_path)

    analyzer = LogAnalyzer()
    analyzer.run()

    assert target_dir.is_dir()
    for subdir in LogAnalyzer.DEFAULT_SUBDIRS:
        assert (target_dir / subdir).is_dir()
    assert (target_dir / "run.log").exists()
