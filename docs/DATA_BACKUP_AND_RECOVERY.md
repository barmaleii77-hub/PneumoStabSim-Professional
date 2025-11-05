# Data Backup and Recovery Guide

This guide describes how PneumoStabSim Professional captures user-generated
content, how to create and manage backups, and how to restore data safely. The
procedures are designed for automation (CI/cron jobs) as well as one-off
emergency recoveries executed by administrators.

## 1. User data sources

The backup service consolidates every location where operators or end users can
persist state while running the simulator. The current catalogue is exposed via
`src.services.backup_service.discover_user_data_sources()` and covers:

| Location | Contents | Notes |
| --- | --- | --- |
| `config/app_settings.json` | Runtime configuration mutated by the settings manager and UI panels. | Canonical copy of tunable parameters. |
| `config/orbit_presets.json` | Custom orbit definitions imported or edited by users. | Preserved to maintain scenario libraries. |
| `config/user_profiles/` | Saved graphics/environment presets per user. | Each JSON file corresponds to a profile. |
| `config/ui_layouts/` | Saved dashboard arrangements. | Includes legacy and refactored layout payloads. |
| `reports/` (entire tree) | Session exports, telemetry, diagnostics, QA artefacts, localisation builds, and administrator audits. | Includes subdirectories such as `reports/sessions/`, `reports/telemetry/`, `reports/tests/`, `reports/performance/`, etc. |

> **Tip:** `discover_user_data_sources()` returns a tuple of `Path` objects and
> can be used by tooling (e.g., dashboards or health checks) to keep
> documentation and automation aligned with the code.

## 2. Backup service overview

`src/services/backup_service.py` implements the `BackupService` class. Key
features include:

- Deterministic ZIP archives created in the `backups/` directory (relative to
  the project root by default).
- Embedded manifest (`PSS_BACKUP_MANIFEST.json`) containing creation timestamp,
  included items, and skipped sources for auditing before restores.
- Opt-in pruning of old archives to cap retention.
- Safety checks preventing path traversal during restore operations.
- Extensible data-source list (pass additional `Path` objects to the service
  constructor for environment-specific artefacts).

## 3. Command-line interface

A dedicated CLI wrapper lives in `src/cli/backup.py`. Typical usage:

```bash
# Create a timestamped backup
python -m src.cli.backup create --label nightly

# List available archives with metadata
python -m src.cli.backup list

# Inspect the manifest for a specific archive
python -m src.cli.backup inspect backups/backup_20250305-101500_nightly.zip

# Restore into a staging directory without overwriting existing files
python -m src.cli.backup restore backups/backup_20250305-101500_nightly.zip \
    --target /srv/pss-restore --overwrite

# Keep the five newest archives and delete the rest
python -m src.cli.backup prune 5
```

Pass `--root` and `--backup-dir` if the working directory differs from the
project layout (e.g., when running from systemd timers or CI jobs). Additional
sources can be appended with repeated `--source PATH` arguments.

## 4. GUI launcher

`src/app/backup_gui.py` provides a lightweight Qt-based interface. Launch it via

```bash
python -m src.app.backup_gui
```

If PySide6 is unavailable the module falls back to a console message and
suggests using the CLI. When the GUI is available it displays:

1. The tracked data sources for quick verification.
2. A list of archived backups (with manifest summaries in tooltips).
3. Buttons to create new backups, restore the selected archive, inspect the
   manifest, or refresh the list.

Restores prompt for a destination directory and report how many files were
restored or skipped.

## 5. Recovery procedure

1. **Identify the target archive.** Use the CLI (`list`/`inspect`) or GUI to
   confirm the timestamp and included sources.
2. **Prepare a restore location.** Prefer restoring into a clean staging
   directory before overlaying production data.
3. **Restore data.** Run `python -m src.cli.backup restore <archive> --target
   <path>` (add `--overwrite` if replacing existing files).
4. **Verify integrity.** Review the manifest (`inspect`) and manually inspect key
   files (`config/app_settings.json`, recent `reports/sessions/` snapshots, etc.).
5. **Promote to production.** After validation, replace the live directories or
   reconfigure the application to point at the restored location.

## 6. Administrative recommendations

- **Schedule regular backups.** Automate `python -m src.cli.backup create
  --label nightly` via cron/Task Scheduler and rotate archives with `prune`.
- **Off-site replication.** Sync the `backups/` directory to hardened storage
  (S3, Azure Blob, secure NAS). Ensure manifests travel with the archives.
- **Test restores quarterly.** Use the integration tests
  (`tests/integration/test_backup_restore.py`) as a baseline and perform a full
  dry-run restore on staging infrastructure.
- **Monitor skips.** Review CLI output or manifests for skipped sources—this may
  indicate new directories that need to be added.
- **Secure access.** Restrict permissions on both `backups/` and the data
  sources to prevent tampering. Run backups under a dedicated service account.
- **Document incidents.** Record every recovery in the operations log with
  archive name, target environment, and verification steps completed.

Keeping documentation, automation, and testing aligned ensures the simulator can
be restored quickly with minimal data loss after incidents or migrations.
