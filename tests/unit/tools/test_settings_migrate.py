"""Unit tests for the settings migration runner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.tools import settings_migrate


@pytest.fixture()
def migrations_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "config" / "migrations"
    directory.mkdir(parents=True)
    descriptor = {
        "id": "0001_add_defaults",
        "description": "Populate diagnostics defaults.",
        "operations": [
            {
                "op": "ensure",
                "path": "current.diagnostics",
                "value": {"signal_trace": {"enabled": False}},
            },
            {
                "op": "ensure",
                "path": "metadata.schema_version",
                "value": "0.2.0",
            },
        ],
    }
    (directory / "0001_add_defaults.json").write_text(
        json.dumps(descriptor, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return directory


@pytest.fixture()
def settings_payload(tmp_path: Path) -> Path:
    settings_dir = tmp_path / "config"
    settings_dir.mkdir()
    payload = {
        "metadata": {"units_version": "si_v2"},
        "current": {},
        "defaults_snapshot": {},
    }
    path = settings_dir / "app_settings.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_apply_migrations_populates_defaults(settings_payload: Path, migrations_dir: Path) -> None:
    payload = settings_migrate._load_settings(settings_payload)
    descriptors = settings_migrate.load_migrations(migrations_dir)

    executed = settings_migrate.apply_migrations(payload, descriptors)

    assert executed == ["0001_add_defaults"]
    assert payload["current"]["diagnostics"]["signal_trace"]["enabled"] is False
    assert payload["metadata"]["schema_version"] == "0.2.0"
    assert payload["metadata"]["migrations"] == ["0001_add_defaults"]


def test_apply_migrations_is_idempotent(settings_payload: Path, migrations_dir: Path) -> None:
    payload = settings_migrate._load_settings(settings_payload)
    descriptors = settings_migrate.load_migrations(migrations_dir)

    # First run applies the migration.
    settings_migrate.apply_migrations(payload, descriptors)
    # Second run should skip since the identifier is already recorded.
    executed = settings_migrate.apply_migrations(payload, descriptors)

    assert executed == []
    assert payload["metadata"]["migrations"] == ["0001_add_defaults"]
