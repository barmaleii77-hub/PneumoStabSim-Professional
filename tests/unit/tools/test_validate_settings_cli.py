from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import validate_settings


@pytest.fixture()
def schema_path() -> Path:
    return Path("config/app_settings.schema.json").resolve()


@pytest.fixture()
def settings_path() -> Path:
    return Path("config/app_settings.json").resolve()


def test_validate_settings_cli_success(capsys, schema_path: Path, settings_path: Path) -> None:
    exit_code = validate_settings.main(
        ["--settings-file", str(settings_path), "--schema-file", str(schema_path), "--quiet"]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_validate_settings_cli_reports_schema_errors(tmp_path: Path, capsys, schema_path: Path) -> None:
    broken_settings = tmp_path / "broken.json"
    broken_settings.write_text(json.dumps({"metadata": {}}), encoding="utf-8")

    exit_code = validate_settings.main(
        ["--settings-file", str(broken_settings), "--schema-file", str(schema_path)]
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Settings validation failed" in captured.err
    assert "current" in captured.err


def test_validate_settings_cli_handles_invalid_json(tmp_path: Path, capsys, schema_path: Path) -> None:
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{ invalid", encoding="utf-8")

    exit_code = validate_settings.main(
        ["--settings-file", str(invalid_json), "--schema-file", str(schema_path)]
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Invalid JSON" in captured.err
