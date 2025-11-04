"""Validate HDR skybox orientation consistency.

This utility inspects the baseline material catalogue stored in
``config/baseline/materials.json`` and verifies that HDR skyboxes expose a
normalised orientation payload.  The report mirrors the expectations encoded in
Phase 3 of the renovation programme: every HDR entry must declare the expected
coordinate frame (``z-up``) and a rotation offset expressed in degrees.

When the validator finds a mismatch it writes a Markdown report to
``reports/performance/hdr_orientation.md`` and exits with a non-zero status so
that CI pipelines fail fast.  The report is human-friendly and includes enough
context for artists to re-export the offending assets.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.ui.panels.lighting.baseline import (
    MaterialsBaseline,
    OrientationIssue,
    load_materials_baseline,
)

DEFAULT_BASELINE_PATH = Path("config/baseline/materials.json")
DEFAULT_REPORT_PATH = Path("reports/performance/hdr_orientation.md")


@dataclass(frozen=True)
class _ValidationResult:
    baseline: MaterialsBaseline
    issues: Sequence[OrientationIssue]


def _render_markdown(result: _ValidationResult) -> str:
    baseline = result.baseline
    issues_by_id = {issue.skybox.id: issue for issue in result.issues}

    lines: list[str] = ["# HDR Orientation Report", ""]
    lines.append(f"- Total skyboxes: {len(baseline.skyboxes)}")
    lines.append(f"- Issues detected: {len(result.issues)}")
    generated_ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    lines.append(f"- Generated: {generated_ts}")
    lines.append("")

    if not baseline.skyboxes:
        lines.append("No HDR skyboxes registered in config/baseline/materials.json.")
        return "\n".join(lines)

    lines.extend(
        [
            "| Skybox | File | Orientation | Rotation | Status | Notes |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )

    for entry in baseline.skyboxes:
        issue = issues_by_id.get(entry.id)
        status = "❌" if issue else "✅"
        note = issue.message if issue else entry.notes or ""
        lines.append(
            "| {name} | {file} | {orientation} | {rotation:.1f}° | {status} | {note} |".format(
                name=entry.label,
                file=entry.file,
                orientation=entry.orientation,
                rotation=entry.rotation,
                status=status,
                note=note.replace("\n", " "),
            )
        )

    return "\n".join(lines)


def _run_validation(baseline_path: Path) -> _ValidationResult:
    baseline = load_materials_baseline(baseline_path)
    issues = baseline.detect_orientation_issues()
    return _ValidationResult(baseline=baseline, issues=issues)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate HDR orientation metadata against the baseline catalogue",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE_PATH,
        help="Path to config/baseline/materials.json",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Destination for the generated Markdown report",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Echo the report to stdout in addition to writing the file",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Emit GitHub Actions annotations when issues are detected",
    )
    return parser.parse_args(argv)


def _ensure_parent_directory(path: Path) -> None:
    parent = path.parent
    if parent and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = _run_validation(args.baseline)

    report_content = _render_markdown(result)
    _ensure_parent_directory(args.report)
    args.report.write_text(report_content, encoding="utf-8")

    if args.stdout:
        print(report_content)

    if result.issues:
        if args.ci:
            for issue in result.issues:
                skybox = issue.skybox
                message = (
                    f"[{skybox.id}] {issue.kind}: {issue.message} (file={skybox.file})"
                )
                print(f"::error title=HDR orientation::{message}")
        print(
            f"Found {len(result.issues)} HDR orientation issue(s); see {args.report}",
            file=sys.stderr,
        )
        return 1

    print(
        f"HDR orientation validation passed for {len(result.baseline.skyboxes)}"
        " skybox entries.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
