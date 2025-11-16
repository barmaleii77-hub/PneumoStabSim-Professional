from __future__ import annotations

import json
from pathlib import Path

from tools.verify_hdr_assets import verify_hdr_assets


def _write_dummy_hdr(path: Path, content: bytes) -> None:
    path.write_bytes(content)


def test_verify_hdr_assets_generates_manifest_and_reports_ok(tmp_path: Path) -> None:
    hdr_dir = tmp_path / "assets" / "hdr"
    hdr_dir.mkdir(parents=True, exist_ok=True)
    file_a = hdr_dir / "a.hdr"
    file_b = hdr_dir / "b.hdr"
    _write_dummy_hdr(file_a, b"AAA")
    _write_dummy_hdr(file_b, b"BBB")

    manifest_path = hdr_dir / "hdr_manifest.json"
    summary_path = tmp_path / "reports" / "quality" / "hdr_assets_status.json"

    # Первичная генерация манифеста
    exit_code = verify_hdr_assets(manifest_path, summary_path)
    assert exit_code == 0, "Ожидался успешный выход при создании манифеста"
    assert manifest_path.exists(), "Манифест должен быть создан"

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "files" in manifest_payload and len(manifest_payload["files"]) == 2

    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    statuses = {entry["name"]: entry for entry in summary_payload.get("statuses", [])}
    assert statuses["a.hdr"]["status"] == "ok"
    assert statuses["b.hdr"]["status"] == "ok"

    # Модификация файла для проверки mismatch
    file_a.write_bytes(b"MODIFIED")
    exit_code_mismatch = verify_hdr_assets(manifest_path, summary_path)
    assert exit_code_mismatch == 1, "Ожидался код выхода 1 при несоответствии хеша"
    summary_payload2 = json.loads(summary_path.read_text(encoding="utf-8"))
    statuses2 = {entry["name"]: entry for entry in summary_payload2.get("statuses", [])}
    assert statuses2["a.hdr"]["status"] == "checksum-mismatch"


def test_verify_hdr_assets_reports_missing(tmp_path: Path) -> None:
    hdr_dir = tmp_path / "assets" / "hdr"
    hdr_dir.mkdir(parents=True, exist_ok=True)
    file_a = hdr_dir / "only.hdr"
    _write_dummy_hdr(file_a, b"AAA")

    manifest_path = hdr_dir / "hdr_manifest.json"
    summary_path = tmp_path / "reports" / "quality" / "hdr_assets_status.json"

    # Создаём манифест
    verify_hdr_assets(manifest_path, summary_path)
    # Удаляем файл и повторяем проверку
    file_a.unlink()
    exit_code_missing = verify_hdr_assets(manifest_path, summary_path)
    assert exit_code_missing == 1, "Ожидался код выхода 1 при отсутствующем файле"
    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    statuses = {entry["name"]: entry for entry in summary_payload.get("statuses", [])}
    assert statuses["only.hdr"]["status"] == "missing"
