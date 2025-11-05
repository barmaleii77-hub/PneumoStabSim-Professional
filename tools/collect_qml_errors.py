"""Parse QML runtime logs and collect diagnostics into a structured report."""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"qml.*error", re.IGNORECASE),
    re.compile(r"qml.*warning", re.IGNORECASE),
    re.compile(r"qrc:/.*(failed|error)", re.IGNORECASE),
    re.compile(r"(critical|fatal)", re.IGNORECASE),
)

IGNORED_SUBSTRINGS = {
    "setHighDpiScaleFactorRoundingPolicy",
    "QFontDatabase",
}


def scan_lines(lines: Iterable[str]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for idx, raw in enumerate(lines, start=1):
        text = raw.strip()
        if not text:
            continue
        if any(token in text for token in IGNORED_SUBSTRINGS):
            continue
        for pattern in PATTERNS:
            if pattern.search(text):
                findings.append({"line": idx, "message": text})
                break
    return findings


def analyse_log(path: Path) -> dict[str, object]:
    content = path.read_text(encoding="utf-8", errors="replace")
    findings = scan_lines(content.splitlines())
    return {
        "source": str(path),
        "timestamp": datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "entries": findings,
        "total_entries": len(findings),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="Path to the QML runtime log")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path for the JSON report (defaults to reports/tests)",
    )
    args = parser.parse_args()

    report = analyse_log(args.log)
    output = args.output
    if output is None:
        root = Path(__file__).resolve().parents[1]
        output_dir = root / "reports" / "tests"
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / (Path(args.log).stem + "_qml_report.json")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Collected {report['total_entries']} QML diagnostics → {output}")

    if report["total_entries"] > 0:
        exit(1)


if __name__ == "__main__":
    main()
