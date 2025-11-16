from __future__ import annotations

import json
from pathlib import Path

from src.tools import settings_migrate


def _read_events(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_idempotent_run_does_not_duplicate_events(tmp_path: Path) -> None:
    # Prepare settings file
    settings_path = tmp_path / "config" / "app_settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(
            {"metadata": {}, "current": {}, "defaults_snapshot": {}},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Prepare migrations directory with one migration
    migrations_dir = tmp_path / "config" / "migrations"
    migrations_dir.mkdir(parents=True, exist_ok=True)
    (migrations_dir / "001_add_flag.json").write_text(
        json.dumps(
            {
                "id": "001_add_flag",
                "description": "Ensure debug flag",
                "operations": [
                    {"op": "ensure", "path": "metadata.debug_enabled", "value": True}
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    log_root = tmp_path / "logs"

    # First run
    exit_code1 = settings_migrate.main(
        [
            "--settings",
            str(settings_path),
            "--migrations",
            str(migrations_dir),
            "--in-place",
            "--log-dir",
            str(log_root),
        ]
    )
    assert exit_code1 == 0
    log_file = log_root / "migrations.jsonl"
    assert log_file.exists()
    events_first = _read_events(log_file)
    migration_events_first = [
        e for e in events_first if e.get("migration") == "001_add_flag"
    ]
    final_events_first = [
        e for e in events_first if e.get("event") == "migration-run-complete"
    ]
    assert len(migration_events_first) == 1
    assert len(final_events_first) == 1

    # Second run (no new migration events, only another final aggregate allowed)
    exit_code2 = settings_migrate.main(
        [
            "--settings",
            str(settings_path),
            "--migrations",
            str(migrations_dir),
            "--in-place",
            "--log-dir",
            str(log_root),
        ]
    )
    assert exit_code2 == 0
    events_second = _read_events(log_file)
    migration_events_second = [
        e for e in events_second if e.get("migration") == "001_add_flag"
    ]
    final_events_second = [
        e for e in events_second if e.get("event") == "migration-run-complete"
    ]

    # Migration should still appear only once
    assert len(migration_events_second) == 1
    # There should now be two final events
    assert len(final_events_second) == 2

    # Hashes before/after must be stable on second run (no changes)
    last_event = final_events_second[-1]
    prev_event = final_events_second[-2]
    assert last_event["payload_hash_before"] == prev_event["payload_hash_after"]
    assert last_event["payload_hash_after"] == prev_event["payload_hash_after"]
