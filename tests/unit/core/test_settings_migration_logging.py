from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.tools import settings_migrate


@pytest.fixture()
def temp_settings(tmp_path: Path) -> Path:
    settings_payload = {
        "metadata": {"version": "1.0"},
        "current": {"simulation": {"physics_dt": 0.005}},
        "defaults_snapshot": {"simulation": {"physics_dt": 0.005}},
    }
    cfg = tmp_path / "config" / "app_settings.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(json.dumps(settings_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return cfg


@pytest.fixture()
def temp_migrations_dir(tmp_path: Path) -> Path:
    mig_dir = tmp_path / "config" / "migrations"
    mig_dir.mkdir(parents=True, exist_ok=True)

    # Migration 1: ensure new key
    (mig_dir / "001_add_profile_flag.json").write_text(
        json.dumps(
            {
                "id": "001_add_profile_flag",
                "description": "Add debug profile flag",
                "operations": [
                    {"op": "ensure", "path": "metadata.profile", "value": "debug"}
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Migration 2: set value (will change physics_dt)
    (mig_dir / "002_tune_physics_dt.json").write_text(
        json.dumps(
            {
                "id": "002_tune_physics_dt",
                "description": "Adjust physics dt precision",
                "operations": [
                    {"op": "set", "path": "current.simulation.physics_dt", "value": 0.004},
                    {"op": "set", "path": "defaults_snapshot.simulation.physics_dt", "value": 0.004},
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return mig_dir


def test_migrations_append_jsonl_log(tmp_path: Path, temp_settings: Path, temp_migrations_dir: Path) -> None:
    log_dir = tmp_path / "logs_root"
    log_path = log_dir / "migrations.jsonl"

    assert not log_path.exists(), "Лог миграций не должен существовать до запуска"

    # Run migrations via direct call to module main
    exit_code = settings_migrate.main([
        "--settings",
        str(temp_settings),
        "--migrations",
        str(temp_migrations_dir),
        "--in-place",
        "--verbose",
        "--log-dir",
        str(log_dir),
    ])
    assert exit_code == 0

    assert log_path.exists(), "Ожидается создание файла лога migrations.jsonl"

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 3, "Ожидается >=3 строк (2 миграции + итоговое событие)"

    events = [json.loads(l) for l in lines]
    ids = {e.get("migration") for e in events if "migration" in e}
    assert "001_add_profile_flag" in ids
    assert "002_tune_physics_dt" in ids

    # Final aggregate event
    final_events = [e for e in events if e.get("event") == "migration-run-complete"]
    assert final_events, "Ожидается итоговое событие migration-run-complete"
    final = final_events[-1]
    assert final.get("executed_count") == 2
    # Новые поля хэшей для дифф-аналитики
    assert isinstance(final.get("payload_hash_before"), str)
    assert isinstance(final.get("payload_hash_after"), str)
    # До и после должны быть разными при изменениях
    assert final["payload_hash_before"] != final["payload_hash_after"]


def test_re_run_is_idempotent(tmp_path: Path, temp_settings: Path, temp_migrations_dir: Path) -> None:
    # First run
    settings_migrate.main([
        "--settings",
        str(temp_settings),
        "--migrations",
        str(temp_migrations_dir),
        "--in-place",
    ])

    # Capture original payload hash
    payload1 = json.loads(temp_settings.read_text(encoding="utf-8"))
    hash1 = json.dumps(payload1, sort_keys=True, ensure_ascii=False)

    # Second run (should not apply migrations again)
    settings_migrate.main([
        "--settings",
        str(temp_settings),
        "--migrations",
        str(temp_migrations_dir),
        "--in-place",
    ])

    payload2 = json.loads(temp_settings.read_text(encoding="utf-8"))
    hash2 = json.dumps(payload2, sort_keys=True, ensure_ascii=False)

    assert hash1 == hash2, "Идempotентный повторный запуск не должен менять payload"
