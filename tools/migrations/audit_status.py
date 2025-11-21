"""Settings Migrations Audit Script

Reads config/app_settings.json and reports/migrations.jsonl to determine
latest applied migrations and detect unapplied JSON migration descriptor files.
Outputs a markdown summary to reports/status/MIGRATIONS_AUDIT.md.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

SETTINGS_PATH = Path("config/app_settings.json")
MIGRATIONS_DIR = Path("config/migrations")
LOG_PATH = Path("reports/settings/migrations.jsonl")
OUT_MD = Path("reports/status/MIGRATIONS_AUDIT.md")


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))


def load_log_entries() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    entries: list[dict] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def discover_migration_ids() -> list[str]:
    if not MIGRATIONS_DIR.exists():
        return []
    ids: list[str] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.json")):
        ids.append(path.stem)
    return ids


def main() -> int:
    settings = load_settings()
    logged = load_log_entries()
    known_ids = discover_migration_ids()

    applied_in_settings = settings.get("metadata", {}).get("migrations", []) if isinstance(settings.get("metadata"), dict) else []
    applied_set = set(applied_in_settings)
    unapplied = [mid for mid in known_ids if mid not in applied_set]

    last_log_event = None
    for entry in reversed(logged):
        if entry.get("event") == "migration-run-complete":
            last_log_event = entry
            break

    md = ["# Migrations Audit", "", f"**Generated:** {datetime.utcnow().isoformat()}Z", "", "## Summary"]
    md.append(f"- Total migration files: {len(known_ids)}")
    md.append(f"- Applied (settings metadata): {len(applied_set)}")
    md.append(f"- Unapplied: {len(unapplied)}")
    if unapplied:
        md.append("\n### Unapplied Migration IDs")
        for mid in unapplied:
            md.append(f"- {mid}")
    else:
        md.append("\nNo unapplied migrations detected.")

    if last_log_event:
        md.append("\n### Last Migration Run")
        md.append(f"- Timestamp: {last_log_event.get('timestamp')}")
        md.append(f"- Executed Count: {last_log_event.get('executed_count')}")
        md.append(f"- Payload Hash After: {last_log_event.get('payload_hash_after')}")
    else:
        md.append("\nNo migration-run-complete event found in log.")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Audit written: {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
