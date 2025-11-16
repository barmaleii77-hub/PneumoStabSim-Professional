"""HDR assets verification and manifest maintenance.

Проверяет наличие файлов HDR в каталоге рядом с указанным manifest (обычно
assets/hdr) и сравнивает их с манифестом hdr_manifest.json. При отсутствии
манифеста создаёт шаблон. Выводит JSON отчёт со статусами:
  ok | missing | extra | checksum-mismatch.

Usage:
  python -m tools.verify_hdr_assets --summary-json reports/quality/hdr_assets_status.json

Args:
  --manifest PATH (default: assets/hdr/hdr_manifest.json)
  --summary-json PATH (optional) путь для записи итогового отчёта
  --fetch-missing (ignored placeholder: загрузка не реализована)

Формат hdr_manifest.json:
{
  "files": [
     {"name": "studio.hdr", "sha256": "..."},
     ...
  ]
}
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "assets" / "hdr" / "hdr_manifest.json"


@dataclass
class ManifestEntry:
    name: str
    sha256: str


@dataclass
class FileStatus:
    name: str
    status: str  # ok|missing|extra|checksum-mismatch
    expected_sha256: str | None = None
    actual_sha256: str | None = None


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_manifest(path: Path) -> list[ManifestEntry]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    entries: list[ManifestEntry] = []
    for item in payload.get("files", []) if isinstance(payload, dict) else []:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        sha = item.get("sha256")
        if isinstance(name, str) and isinstance(sha, str):
            entries.append(ManifestEntry(name=name, sha256=sha))
    return entries


def _discover_hdr_files(hdr_dir: Path) -> list[Path]:
    if not hdr_dir.exists():
        return []
    return sorted(p for p in hdr_dir.glob("*.hdr") if p.is_file())


def _generate_manifest(entries: Iterable[Path]) -> list[ManifestEntry]:
    manifest_entries: list[ManifestEntry] = []
    for path in entries:
        try:
            manifest_entries.append(
                ManifestEntry(name=path.name, sha256=_hash_file(path))
            )
        except Exception:
            continue
    return manifest_entries


def _write_manifest(path: Path, entries: list[ManifestEntry]) -> None:
    try:
        payload = {"files": [{"name": e.name, "sha256": e.sha256} for e in entries]}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    except Exception:
        pass


def verify_hdr_assets(manifest_path: Path, summary_json: Path | None) -> int:
    hdr_dir = manifest_path.parent  # локальный каталог HDR файлов
    hdr_files = _discover_hdr_files(hdr_dir)
    manifest_entries = _load_manifest(manifest_path)

    if not manifest_entries and hdr_files:
        # Создаём новый манифест если отсутствует
        manifest_entries = _generate_manifest(hdr_files)
        _write_manifest(manifest_path, manifest_entries)
        print(f"[hdr-verify] Manifest created at {manifest_path}")

    manifest_map = {e.name: e for e in manifest_entries}
    discovered_map = {p.name: p for p in hdr_files}

    statuses: list[FileStatus] = []

    # Проверка присутствия и хешей
    for name, entry in manifest_map.items():
        path = discovered_map.get(name)
        if path is None:
            statuses.append(
                FileStatus(name=name, status="missing", expected_sha256=entry.sha256)
            )
            continue
        try:
            actual_sha = _hash_file(path)
        except Exception:
            statuses.append(
                FileStatus(name=name, status="missing", expected_sha256=entry.sha256)
            )
            continue
        if actual_sha != entry.sha256:
            statuses.append(
                FileStatus(
                    name=name,
                    status="checksum-mismatch",
                    expected_sha256=entry.sha256,
                    actual_sha256=actual_sha,
                )
            )
        else:
            statuses.append(
                FileStatus(
                    name=name,
                    status="ok",
                    expected_sha256=entry.sha256,
                    actual_sha256=actual_sha,
                )
            )

    # Дополнительные файлы не в манифесте
    for name, path in discovered_map.items():
        if name not in manifest_map:
            try:
                actual_sha = _hash_file(path)
            except Exception:  # pragma: no cover
                actual_sha = None
            statuses.append(
                FileStatus(name=name, status="extra", actual_sha256=actual_sha)
            )

    summary = {
        "manifest": str(manifest_path),
        "directory": str(hdr_dir),
        "files_total": len(hdr_files),
        "manifest_entries": len(manifest_entries),
        "statuses": [
            {
                "name": s.name,
                "status": s.status,
                "expected_sha256": s.expected_sha256,
                "actual_sha256": s.actual_sha256,
            }
            for s in statuses
        ],
    }

    ok_count = sum(1 for s in statuses if s.status == "ok")
    missing_count = sum(1 for s in statuses if s.status == "missing")
    mismatch_count = sum(1 for s in statuses if s.status == "checksum-mismatch")
    extra_count = sum(1 for s in statuses if s.status == "extra")

    print(
        f"[hdr-verify] ok={ok_count} missing={missing_count} mismatch={mismatch_count} extra={extra_count}"
    )

    if summary_json is not None:
        try:
            summary_json.parent.mkdir(parents=True, exist_ok=True)
            summary_json.write_text(
                json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(f"[hdr-verify] Summary written to {summary_json}")
        except Exception as exc:  # pragma: no cover
            print(f"[hdr-verify] Unable to write summary JSON: {summary_json} ({exc})")

    # Exit code: 0 если нет missing/mismatch иначе 1
    return 0 if (missing_count == 0 and mismatch_count == 0) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify HDR assets manifest integrity")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to hdr_manifest.json (default: assets/hdr/hdr_manifest.json)",
    )
    parser.add_argument(
        "--summary-json", type=Path, default=None, help="Path for JSON status output"
    )
    parser.add_argument(
        "--fetch-missing",
        action="store_true",
        help="Placeholder: attempt to fetch missing assets (not implemented)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    exit_code = verify_hdr_assets(args.manifest, args.summary_json)
    raise SystemExit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
