"""HDR assets verification tool.

Usage:
  python -m tools.verify_hdr_assets --summary-json \
    reports/quality/hdr_assets_status.json

Args:
  --summary-json PATH  Путь для JSON отчёта.
  --no-summary         Отключить вывод отчёта на диск.
  --manifest PATH      Путь к манифесту (default: assets/hdr/hdr_manifest.json)
  --fetch-missing      (no-op) зарезервировано для будущего автозагрузчика
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Dict, Any

REPO_ROOT = Path(__file__).resolve().parents[1]
HDR_DIR = REPO_ROOT / "assets" / "hdr"
DEFAULT_SUMMARY_JSON = REPO_ROOT / "reports" / "quality" / "hdr_assets_status.json"
DEFAULT_MANIFEST_PATH = HDR_DIR / "hdr_manifest.json"

REQUIRED_FILES = ["studio.hdr", "factory.hdr", "warehouse.hdr"]
OPTIONAL_FILES = ["studio_preview.png", "factory_preview.png", "warehouse_preview.png"]

EXPECTED_SIZES: dict[str, int] = {
    "studio.hdr": 7_000_000,  # примерный размер
    "factory.hdr": 5_500_000,
    "warehouse.hdr": 6_200_000,
}
SIZE_TOLERANCE = 0.40  # 40% допуска


@dataclass
class HDRStatus:
    name: str
    path: Path
    exists: bool
    size_bytes: int
    mismatch: bool


def _evaluate_size(path: Path) -> tuple[int, bool]:
    if not path.exists():
        return 0, False
    size = path.stat().st_size
    expected = EXPECTED_SIZES.get(path.name)
    if expected is None:
        return size, False
    mismatch = not (expected * (1 - SIZE_TOLERANCE) <= size <= expected * (1 + SIZE_TOLERANCE))
    return size, mismatch


def _collect_status(files: Iterable[str]) -> list[HDRStatus]:
    result: list[HDRStatus] = []
    for name in files:
        path = HDR_DIR / name
        size, mismatch = _evaluate_size(path)
        result.append(HDRStatus(name=name, path=path, exists=path.exists(), size_bytes=size, mismatch=mismatch))
    return result


def _print_status(statuses: list[HDRStatus]) -> None:
    for st in statuses:
        if not st.exists:
            print(f"[hdr-verify] ❌ missing: {st.name}")
        elif st.mismatch:
            print(f"[hdr-verify] ⚠️ size mismatch: {st.name} ({st.size_bytes} bytes)")
        else:
            print(f"[hdr-verify] ✅ {st.name} ({st.size_bytes} bytes)")


def _summarise(statuses: list[HDRStatus]) -> None:
    ok_count = sum(1 for s in statuses if s.exists and not s.mismatch)
    missing_count = sum(1 for s in statuses if not s.exists)
    mismatch_count = sum(1 for s in statuses if s.mismatch and s.exists)
    extra_count = sum(1 for p in HDR_DIR.iterdir() if p.name not in REQUIRED_FILES and p.name not in OPTIONAL_FILES)
    print(
        "[hdr-verify] ok="
        f"{ok_count} missing={missing_count} mismatch={mismatch_count} extra={extra_count}"
    )


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_hdr_assets(manifest_path: Path, summary_path: Path) -> int:
    """Verify HDR assets directory, produce manifest + status summary.

    Test contract:
    - First run (no manifest): create manifest with SHA256 for each .hdr file, return 0.
    - Subsequent runs: compare checksums and file existence, return 0 if all OK else 1.
    - Summary JSON: key 'statuses' list of {name, status, size_bytes, ...}.
    - New / untracked files (not in manifest) reported as 'untracked'.
    """
    hdr_dir = manifest_path.parent
    hdr_dir.mkdir(parents=True, exist_ok=True)

    hdr_files = sorted([p for p in hdr_dir.iterdir() if p.is_file() and p.suffix.lower() == ".hdr"])

    # Load or create manifest
    if manifest_path.exists():
        try:
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest_payload = {}
        manifest_files: Dict[str, str] = dict(manifest_payload.get("files", {}))
    else:
        manifest_files = {}

    def _emit_manifest(files: list[Path]) -> None:
        payload = {
            "files": {f.name: _sha256(f) for f in files},
            "count": len(files),
            "dir": str(hdr_dir),
        }
        manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    wrote_manifest = False
    if not manifest_files:
        _emit_manifest(hdr_files)
        wrote_manifest = True
        manifest_files = {f.name: _sha256(f) for f in hdr_files}

    statuses: List[Dict[str, Any]] = []
    all_ok = True

    # Evaluate manifest entries
    for name, expected_hash in manifest_files.items():
        path = hdr_dir / name
        if not path.exists():
            statuses.append({"name": name, "status": "missing", "size_bytes": 0})
            all_ok = False
            continue
        actual_hash = _sha256(path)
        size_bytes = path.stat().st_size
        if actual_hash != expected_hash:
            statuses.append({"name": name, "status": "checksum-mismatch", "size_bytes": size_bytes, "expected": expected_hash, "actual": actual_hash})
            all_ok = False
        else:
            statuses.append({"name": name, "status": "ok", "size_bytes": size_bytes})

    # Untracked new files (present but absent in manifest)
    recorded_names = set(manifest_files.keys())
    for f in hdr_files:
        if f.name not in recorded_names:
            statuses.append({"name": f.name, "status": "untracked", "size_bytes": f.stat().st_size})
            all_ok = False

    summary_payload = {
        "dir": str(hdr_dir),
        "manifest": str(manifest_path),
        "manifest_created": wrote_manifest,
        "statuses": statuses,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if all_ok else 1


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="HDR assets verification")
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=DEFAULT_SUMMARY_JSON,
        help=("Path for JSON status output (default: reports/quality/hdr_assets_status.json); set --no-summary to disable file output"),
    )
    parser.add_argument("--no-summary", action="store_true", help="Disable writing summary JSON file")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH, help="Path to HDR manifest file")
    parser.add_argument("--fetch-missing", action="store_true", help="Attempt to fetch or generate missing HDR assets (currently no-op)")
    args = parser.parse_args(argv)

    # Legacy console status (size / presence) for quick human scan
    required_statuses = _collect_status(REQUIRED_FILES)
    optional_statuses = _collect_status(OPTIONAL_FILES)
    _print_status(required_statuses + optional_statuses)
    _summarise(required_statuses)

    if args.fetch_missing:
        missing = [s for s in required_statuses if not s.exists]
        if missing:
            print(f"[hdr-verify] fetch-missing requested; {len(missing)} required HDR absent (no-op).")

    code = verify_hdr_assets(args.manifest, args.summary_json)
    if args.no_summary and args.summary_json.exists():
        try:
            args.summary_json.unlink()
        except Exception:
            pass
    return code


if __name__ == "__main__":
    raise SystemExit(main())
