"""Regression tests for the :mod:`tools.validate_settings` helper."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import pytest

from tools import validate_settings


class _FakeError:
    """Simple error stub mimicking :mod:`jsonschema` validation errors."""

    def __init__(self, path: Iterable[Any], message: str) -> None:
        self.path = tuple(path)
        self.message = message


class _FakeValidator:
    """Minimal validator stub capturing the schema passed by the CLI."""

    def __init__(self, schema: Any) -> None:
        self._schema = schema

    def iter_errors(self, payload: Any):  # pragma: no cover - simple iterator
        return [
            _FakeError(("root", "second"), "must be a number"),
            _FakeError(("root", "first"), "must be a string"),
        ]


def test_collect_schema_errors_orders_paths_human_readably(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure schema validation errors are sorted for deterministic output."""

    monkeypatch.setattr(
        validate_settings, "Draft202012Validator", _FakeValidator, raising=False
    )

    payload = {"root": {"first": 1, "second": "value"}}
    schema = {"type": "object"}

    errors = validate_settings._collect_schema_errors(payload, schema, _FakeValidator)  # type: ignore[arg-type]

    assert errors == [
        "root.first: must be a string",
        "root.second: must be a number",
    ]


def test_main_reports_missing_settings_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI should emit a helpful error if the target settings file is absent."""

    schema_file = tmp_path / "schema.json"
    schema_file.write_text("{}", encoding="utf-8")

    exit_code = validate_settings.main(
        [
            "--settings-file",
            str(tmp_path / "missing.json"),
            "--schema-file",
            str(schema_file),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "File not found" in captured.err


def test_main_reports_invalid_schema(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Invalid schemas should propagate a clear validation failure."""

    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{}", encoding="utf-8")

    schema_file = tmp_path / "schema.json"
    schema_file.write_text(
        '{"type": "object", "required": "should-be-array"}',
        encoding="utf-8",
    )

    exit_code = validate_settings.main(
        [
            "--settings-file",
            str(settings_file),
            "--schema-file",
            str(schema_file),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Invalid schema" in captured.err
