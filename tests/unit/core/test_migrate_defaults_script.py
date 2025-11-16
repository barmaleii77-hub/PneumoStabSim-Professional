from __future__ import annotations

import json
from pathlib import Path

import pytest

import migrate_defaults_to_json as script


def test_migrate_defaults_dry_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out_path = tmp_path / "config" / "app_settings.json"

    # Запуск dry-run
    exit_code = script.main(["--output", str(out_path), "--dry-run"])
    assert exit_code == 0
    assert not out_path.exists(), "dry-run не должен создавать файл"

    # Реальный запуск
    exit_code2 = script.main(["--output", str(out_path)])
    assert exit_code2 == 0
    assert out_path.exists()

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert set(payload) == {"current", "defaults_snapshot", "metadata"}
    assert "graphics" in payload["current"]
    assert "graphics" in payload["defaults_snapshot"]
    meta = payload["metadata"]
    assert "version" in meta and isinstance(meta["version"], str)
    assert "total_parameters" in meta and isinstance(meta["total_parameters"], int)
