"""Scan shader compilation logs and summarise diagnostics for reporting."""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

ERROR_PATTERN = re.compile(r"\b(error|fatal|fail(?:ed)?)\b", re.IGNORECASE)
WARNING_PATTERN = re.compile(r"\b(warn(?:ing)?)\b", re.IGNORECASE)


def _parse_lines(lines: Iterable[str]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    errors: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    for idx, raw in enumerate(lines, start=1):
        text = raw.strip()
        if not text:
            continue
        if ERROR_PATTERN.search(text):
            errors.append({"line": idx, "message": text})
        elif WARNING_PATTERN.search(text):
            warnings.append({"line": idx, "message": text})
    return errors, warnings


def analyse_shader_log(path: Path) -> dict[str, object]:
    """Return a structured summary for an individual shader log."""

    content = path.read_text(encoding="utf-8", errors="replace")
    errors, warnings = _parse_lines(content.splitlines())
    return {
        "source": str(path),
        "generated_at": datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


# Backwards compatibility alias used by the integration tests
analyse_log = analyse_shader_log


def scan_directory(directory: Path, recursive: bool = False) -> list[dict[str, object]]:
    """Scan ``directory`` for ``*.log`` files and return their summaries."""

    if not directory.exists():
        raise FileNotFoundError(f"Shader log directory does not exist: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Expected a directory, got: {directory}")

    pattern = "**/*.log" if recursive else "*.log"
    return [analyse_shader_log(path) for path in sorted(directory.glob(pattern))]


def _default_output() -> Path:
    root = Path(__file__).resolve().parents[1]
    target = root / "reports" / "tests" / "shader_logs_summary.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _write_summary(summary: list[dict[str, object]], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        type=Path,
        help="Path to a shader log file or directory containing *.log files",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Scan directories recursively for log files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON report path (defaults to reports/tests/shader_logs_summary.json)",
    )
    args = parser.parse_args()

    path: Path = args.path
    if path.is_file():
        summary = [analyse_shader_log(path)]
    else:
        summary = scan_directory(path, recursive=args.recursive)

    output = args.output or _default_output()
    _write_summary(summary, output)

    total_errors = sum(item["error_count"] for item in summary)
    total_warnings = sum(item["warning_count"] for item in summary)
    print(
        f"Analysed {len(summary)} shader log(s): {total_errors} error(s), {total_warnings} warning(s) → {output}"
    )

    if total_errors > 0:
        exit(1)


if __name__ == "__main__":
    main()
