"""Regression tests for metadata backfilling on legacy settings payloads."""

from __future__ import annotations

import json
from pathlib import Path

from src.core.settings_defaults import load_default_settings_payload
from src.core.settings_models import dump_settings
from src.core.settings_service import SettingsService

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "settings" / "app_settings.schema.json"


def test_settings_service_restores_metadata_for_legacy_payload(tmp_path: Path) -> None:
    """Missing metadata fields should be restored using defaults and migrations list."""

    payload = load_default_settings_payload()
    payload["metadata"] = {"units_version": "legacy"}

    settings_path = tmp_path / "app_settings.json"
    settings_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    service = SettingsService(settings_path=settings_path, schema_path=SCHEMA_PATH)

    settings = service.load(use_cache=False)
    dump = dump_settings(settings)
    metadata = dump["metadata"]

    assert metadata["units_version"] == "legacy"
    assert metadata["migrations"]
    assert metadata["migrations"][-1] == "0002_remove_geometry_mesh_extras"
    assert "0001_add_diagnostics_defaults" in metadata["migrations"]
    assert metadata["last_migration"] == "0002_remove_geometry_mesh_extras"
    assert metadata["migration_date"]
