"""HDR assets verification tool.

Usage:
  python -m tools.verify_hdr_assets --summary-json \
    reports/quality/hdr_assets_status.json

Args:
  --summary-json PATH  Путь для JSON отчёта.
  --no-summary         Отключить вывод отчёта на диск.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
HDR_DIR = REPO_ROOT / "assets" / "hdr"
DEFAULT_SUMMARY_JSON = REPO_ROOT / "reports" / "quality" / "hdr_assets_status.json"

REQUIRED_FILES = [
    "studio.hdr",
    "factory.hdr",
    "warehouse.hdr",
]

OPTIONAL_FILES = [
    "studio_preview.png",
    "factory_preview.png",
    "warehouse_preview.png",
]

@dataclass
class HDRStatus:
    name: str
    path: Path
    exists: bool
    size_bytes: int
    mismatch: bool

EXPECTED_SIZES: dict[str, int] = {
    "studio.hdr": 7_000_000,  # примерный размер
    "factory.hdr": 5_500_000,
    "warehouse.hdr": 6_200_000,
}

SIZE_TOLERANCE = 0.40  # 40% допуска


def _evaluate_size(path: Path) -> tuple[int, bool]:
    if not path.exists():
        return 0, False
    size = path.stat().st_size
    expected = EXPECTED_SIZES.get(path.name)
    if expected is None:
        return size, False
    mismatch = not (
        expected * (1 - SIZE_TOLERANCE) <= size <= expected * (1 + SIZE_TOLERANCE)
    )
    return size, mismatch


def _collect_status(files: Iterable[str]) -> list[HDRStatus]:
    result: list[HDRStatus] = []
    for name in files:
        path = HDR_DIR / name
        size, mismatch = _evaluate_size(path)
        result.append(
            HDRStatus(
                name=name,
                path=path,
                exists=path.exists(),
                size_bytes=size,
                mismatch=mismatch,
            )
        )
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
    extra_count = sum(
        1
        for p in HDR_DIR.iterdir()
        if p.name not in REQUIRED_FILES and p.name not in OPTIONAL_FILES
    )
    print(
        "[hdr-verify] ok="
        f"{ok_count} missing={missing_count} mismatch={mismatch_count} "
        f"extra={extra_count}"
    )


def _write_summary_json(path: Path, statuses: list[HDRStatus]) -> None:
    payload = {
        "assets_dir": str(HDR_DIR),
        "required": [
            {
                "name": s.name,
                "exists": s.exists,
                "size_bytes": s.size_bytes,
                "mismatch": s.mismatch,
            }
            for s in statuses
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[hdr-verify] summary written: {path}")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="HDR assets verification")
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=DEFAULT_SUMMARY_JSON,
        help=(
            "Path for JSON status output (default: reports/quality/hdr_assets_status.json); "
            "set --no-summary to disable file output"
        ),
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Disable writing summary JSON file",
    )
    args = parser.parse_args(argv)

    required_statuses = _collect_status(REQUIRED_FILES)
    optional_statuses = _collect_status(OPTIONAL_FILES)
    _print_status(required_statuses + optional_statuses)
    _summarise(required_statuses)

    if not args.no_summary:
        _write_summary_json(args.summary_json, required_statuses)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
