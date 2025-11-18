from __future__ import annotations

import json
import logging
import shutil
import zipfile
from pathlib import Path

import pytest

from src.services.backup_service import BackupService, discover_user_data_sources


@pytest.fixture()
def sample_project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "config/user_profiles").mkdir(parents=True)
    (root / "config/ui_layouts").mkdir(parents=True)
    (root / "reports/sessions/20250101-000000").mkdir(parents=True)
    (root / "reports/telemetry").mkdir(parents=True)

    (root / "config/app_settings.json").write_text(
        json.dumps({"graphics": {"quality": "high"}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (root / "config/orbit_presets.json").write_text(
        json.dumps({"default": {"mode": "standard"}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (root / "config/user_profiles" / "test.json").write_text(
        json.dumps({"name": "Integration"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (root / "config/ui_layouts" / "layout.json").write_text(
        json.dumps({"widgets": []}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (root / "reports/sessions/20250101-000000/config_snapshot.json").write_text(
        json.dumps({"session": "2025"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (root / "reports/telemetry/user_actions.jsonl").write_text(
        '{"action": "start"}\n',
        encoding="utf-8",
    )
    return root


def test_discover_user_data_sources_matches_expectations() -> None:
    expected = {
        Path("config/app_settings.json"),
        Path("config/orbit_presets.json"),
        Path("config/user_profiles"),
        Path("config/ui_layouts"),
        Path("reports"),
    }
    assert set(discover_user_data_sources()) == expected


def test_backup_round_trip(sample_project: Path) -> None:
    service = BackupService(root=sample_project, backup_dir=sample_project / "backups")
    report = service.create_backup(label="integration")

    assert not report.skipped
    manifest = service.inspect_backup(report.archive_path)
    assert "config/app_settings.json" in manifest["included"]
    assert "config/user_profiles/test.json" in manifest["included"]

    # Remove directories to prove restore reconstructs them
    shutil.rmtree(sample_project / "config")
    shutil.rmtree(sample_project / "reports")

    restore_report = service.restore_backup(report.archive_path)
    assert restore_report.skipped == ()
    assert (
        json.loads(
            (sample_project / "config/app_settings.json").read_text(encoding="utf-8")
        )["graphics"]["quality"]
        == "high"
    )
    assert (
        sample_project / "reports/sessions/20250101-000000/config_snapshot.json"
    ).exists()


def test_restore_respects_overwrite_flag(sample_project: Path) -> None:
    service = BackupService(root=sample_project, backup_dir=sample_project / "backups")
    report = service.create_backup(label="overwrite")

    original_contents = (sample_project / "config/app_settings.json").read_text(
        encoding="utf-8"
    )
    modified_contents = original_contents.replace("high", "low")
    (sample_project / "config/app_settings.json").write_text(
        modified_contents, encoding="utf-8"
    )

    restore_report = service.restore_backup(report.archive_path, overwrite=False)
    assert Path("config/app_settings.json") in restore_report.skipped
    assert (sample_project / "config/app_settings.json").read_text(
        encoding="utf-8"
    ) == modified_contents

    restore_report_overwrite = service.restore_backup(
        report.archive_path, overwrite=True
    )
    assert Path("config/app_settings.json") in restore_report_overwrite.restored
    assert (sample_project / "config/app_settings.json").read_text(
        encoding="utf-8"
    ) == original_contents


def test_backup_reports_missing_sources(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "config").mkdir()
    (root / "config/app_settings.json").write_text("{}", encoding="utf-8")

    service = BackupService(
        root=root,
        backup_dir=root / "backups",
        data_sources=[Path("config/app_settings.json"), Path("missing/data")],
    )
    report = service.create_backup()

    assert Path("missing/data") in report.skipped
    assert Path("config/app_settings.json") in report.included
    manifest = service.inspect_backup(report.archive_path)
    assert "missing/data" in manifest["skipped"]


def test_restore_rejects_corrupted_archive(
    sample_project: Path, caplog: pytest.LogCaptureFixture
) -> None:
    service = BackupService(root=sample_project, backup_dir=sample_project / "backups")
    report = service.create_backup(label="corrupted")

    # Corrupt the archive to mimic transmission/storage errors
    report.archive_path.write_bytes(b"not-a-zip")

    caplog.set_level(logging.ERROR, logger="services.backup")
    with pytest.raises(zipfile.BadZipFile):
        service.restore_backup(report.archive_path)

    assert any("backup_corrupted" in record.getMessage() for record in caplog.records)


def test_restore_records_audit_payload_for_corrupted_archive(
    sample_project: Path, caplog: pytest.LogCaptureFixture
) -> None:
    service = BackupService(root=sample_project, backup_dir=sample_project / "backups")
    report = service.create_backup(label="corrupted-audit")

    report.archive_path.write_bytes(b"corrupted-data")

    caplog.set_level(logging.ERROR, logger="services.backup")
    with pytest.raises(zipfile.BadZipFile):
        service.restore_backup(report.archive_path)

    audit_records = [
        record
        for record in caplog.records
        if getattr(record, "event", "") == "backup_corrupted"
    ]
    assert audit_records, "Expected structured audit record for corrupted archive"
    audit_record = audit_records[-1]
    assert audit_record.archive == str(report.archive_path)
    assert "zip" in str(audit_record.error)


def test_restore_rejects_manifest_mismatch(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root = tmp_path / "project"
    backup_dir = root / "backups"
    backup_dir.mkdir(parents=True)
    service = BackupService(root=root, backup_dir=backup_dir)

    archive_path = backup_dir / "manual.zip"
    with zipfile.ZipFile(archive_path, "w") as handle:
        handle.writestr(
            "config/app_settings.json",
            json.dumps({"graphics": {"quality": "low"}}, ensure_ascii=False),
        )
        handle.writestr(
            "PSS_BACKUP_MANIFEST.json",
            json.dumps(
                {
                    "included": ["config/other.json"],
                    "skipped": [],
                    "version": "1.0",
                    "root": str(root),
                    "sources": [],
                },
                ensure_ascii=False,
            ),
        )

    caplog.set_level(logging.ERROR, logger="services.backup")
    with pytest.raises(ValueError, match="manifest"):
        service.restore_backup(archive_path, target_root=root / "restored")

    assert any(
        "backup_manifest_mismatch" in record.getMessage() for record in caplog.records
    )


def test_restore_logs_manifest_mismatch_details(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root = tmp_path / "project"
    backup_dir = root / "backups"
    backup_dir.mkdir(parents=True)
    service = BackupService(root=root, backup_dir=backup_dir)

    archive_path = backup_dir / "audit-manifest.zip"
    with zipfile.ZipFile(archive_path, "w") as handle:
        handle.writestr("config/app_settings.json", "{}")
        handle.writestr(
            "PSS_BACKUP_MANIFEST.json",
            json.dumps(
                {
                    "included": ["config/other.json"],
                    "skipped": [],
                    "version": "1.0",
                    "root": str(root),
                    "sources": ["config/app_settings.json"],
                },
                ensure_ascii=False,
            ),
        )

    caplog.set_level(logging.ERROR, logger="services.backup")
    with pytest.raises(ValueError):
        service.restore_backup(archive_path, target_root=root / "restored")

    audit_records = [
        record
        for record in caplog.records
        if getattr(record, "event", "") == "backup_manifest_mismatch"
    ]
    assert audit_records, "Audit log must capture manifest mismatches"
    audit_record = audit_records[-1]
    assert audit_record.missing == ["config/other.json"]
    assert audit_record.unexpected == ["config/app_settings.json"]


def test_restore_rejects_unsafe_members(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root = tmp_path / "project"
    backup_dir = root / "backups"
    backup_dir.mkdir(parents=True)
    service = BackupService(root=root, backup_dir=backup_dir)

    archive_path = backup_dir / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as handle:
        handle.writestr("../../escape.txt", "malicious")
        handle.writestr(
            "PSS_BACKUP_MANIFEST.json",
            json.dumps({"included": ["../../escape.txt"]}, ensure_ascii=False),
        )

    caplog.set_level(logging.ERROR, logger="services.backup")
    with pytest.raises(ValueError):
        service.restore_backup(archive_path, target_root=root / "restored")

    assert any(
        "backup_restore_rejected" in record.getMessage() for record in caplog.records
    )


def test_restore_logs_path_escape_attempts(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root = tmp_path / "project"
    backup_dir = root / "backups"
    backup_dir.mkdir(parents=True)
    service = BackupService(root=root, backup_dir=backup_dir)

    archive_path = backup_dir / "absolute.zip"
    with zipfile.ZipFile(archive_path, "w") as handle:
        handle.writestr("/etc/passwd", "forbidden")
        handle.writestr(
            "PSS_BACKUP_MANIFEST.json",
            json.dumps(
                {"included": ["/etc/passwd"], "skipped": []}, ensure_ascii=False
            ),
        )

    caplog.set_level(logging.ERROR, logger="services.backup")
    with pytest.raises(ValueError):
        service.restore_backup(archive_path, target_root=root / "restored")

    audit_records = [
        record
        for record in caplog.records
        if getattr(record, "event", "") == "backup_restore_rejected"
    ]
    assert audit_records, "Audit log must capture unsafe path attempts"
    assert any("absolute" in record.getMessage() for record in audit_records)


def test_restore_rejects_invalid_manifest_structure(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root = tmp_path / "project"
    backup_dir = root / "backups"
    backup_dir.mkdir(parents=True)
    service = BackupService(root=root, backup_dir=backup_dir)

    archive_path = backup_dir / "invalid-manifest.zip"
    with zipfile.ZipFile(archive_path, "w") as handle:
        handle.writestr("config/app_settings.json", "{}")
        handle.writestr(
            "PSS_BACKUP_MANIFEST.json",
            json.dumps(
                {
                    "included": "not-a-list",
                    "skipped": [],
                    "version": "1.0",
                    "root": str(root),
                    "sources": ["config/app_settings.json"],
                },
                ensure_ascii=False,
            ),
        )

    caplog.set_level(logging.ERROR, logger="services.backup")
    with pytest.raises(ValueError, match="structure"):
        service.restore_backup(archive_path, target_root=root / "restored")

    audit_records = [
        record
        for record in caplog.records
        if getattr(record, "event", "") == "backup_manifest_invalid"
    ]
    assert audit_records, "Audit log must capture invalid manifest structures"
    assert audit_records[-1].manifest_keys == [
        "included",
        "skipped",
        "version",
        "root",
        "sources",
    ]


def test_restore_rejects_directory_traversal_entry(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root = tmp_path / "project"
    backup_dir = root / "backups"
    backup_dir.mkdir(parents=True)
    service = BackupService(root=root, backup_dir=backup_dir)

    archive_path = backup_dir / "escape-dir.zip"
    with zipfile.ZipFile(archive_path, "w") as handle:
        handle.writestr("../escape/", "")
        handle.writestr(
            "PSS_BACKUP_MANIFEST.json",
            json.dumps(
                {"included": [], "skipped": []}, ensure_ascii=False
            ),
        )

    caplog.set_level(logging.ERROR, logger="services.backup")
    with pytest.raises(ValueError, match="escapes"):
        service.restore_backup(archive_path, target_root=root / "restored")

    audit_records = [
        record
        for record in caplog.records
        if getattr(record, "event", "") == "backup_restore_rejected"
    ]
    assert audit_records, "Audit log must capture directory traversal attempts"
    assert "escape" in str(audit_records[-1].error)
