"""Scan shader compilation logs and summarise diagnostics for reporting."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from collections.abc import Iterable

ERROR_PATTERN = re.compile(r"\b(error|fatal|fail(?:ed)?)\b", re.IGNORECASE)
WARNING_PATTERN = re.compile(r"\b(warn(?:ing)?)\b", re.IGNORECASE)
FALLBACK_PATTERN = re.compile(r"\bfallback\b", re.IGNORECASE)


def _parse_lines(
    lines: Iterable[str],
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    errors: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    fallback: list[dict[str, object]] = []
    for idx, raw in enumerate(lines, start=1):
        text = raw.strip()
        if not text:
            continue

        if ERROR_PATTERN.search(text):
            errors.append({"line": idx, "message": text})

        if WARNING_PATTERN.search(text):
            warnings.append({"line": idx, "message": text})

        if FALLBACK_PATTERN.search(text):
            fallback.append({"line": idx, "message": text})

    return errors, warnings, fallback


def _print_detailed_entries(summary: list[dict[str, object]]) -> None:
    """Stream individual warning and fallback messages to the console."""

    for item in summary:
        source = item.get("source", "<unknown>")
        for entry in item.get("warnings", []) or []:
            line = entry.get("line", 0)
            message = entry.get("message", "")
            print(
                f"[check_shader_logs] WARNING {source}:{line}: {message}",
                file=sys.stdout,
            )

        for entry in item.get("fallbackEvents", []) or []:
            line = entry.get("line", 0)
            message = entry.get("message", "")
            print(
                f"[check_shader_logs] FALLBACK {source}:{line}: {message}",
                file=sys.stdout,
            )

        for entry in item.get("errors", []) or []:
            line = entry.get("line", 0)
            message = entry.get("message", "")
            print(
                f"[check_shader_logs] ERROR {source}:{line}: {message}",
                file=sys.stderr,
            )


def analyse_shader_log(path: Path) -> dict[str, object]:
    """Return a structured summary for an individual shader log."""

    content = path.read_text(encoding="utf-8", errors="replace")
    errors, warnings, fallback_events = _parse_lines(content.splitlines())
    is_fallback_log = "fallback" in path.name.lower()
    if is_fallback_log and not fallback_events:
        fallback_events.append(
            {"line": 0, "message": "filename indicates fallback shader"}
        )
    return {
        "source": str(path),
        "generated_at": datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "fallback_count": len(fallback_events),
        "errors": errors,
        "warnings": warnings,
        "fallbackEvents": fallback_events,
        "isFallbackLog": is_fallback_log,
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
    destination.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )


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
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Exit with status 1 if any warnings are detected in the logs.",
    )
    parser.add_argument(
        "--expect-fallback",
        action="store_true",
        help="Fail the check if no fallback shader logs or events are found.",
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
    total_fallback_logs = sum(1 for item in summary if item.get("isFallbackLog"))
    total_fallback_events = sum(item.get("fallback_count", 0) for item in summary)

    _print_detailed_entries(summary)

    print(
        "Analysed {count} shader log(s): {errors} error(s), {warnings} warning(s), "
        "{fallback_events} fallback event(s) across {fallback_logs} fallback log(s) → {output}".format(
            count=len(summary),
            errors=total_errors,
            warnings=total_warnings,
            fallback_events=total_fallback_events,
            fallback_logs=total_fallback_logs,
            output=output,
        )
    )

    exit_code = 0
    if total_errors > 0:
        exit_code = 1
    elif args.fail_on_warnings and total_warnings > 0:
        exit_code = 1
    elif args.expect_fallback and total_fallback_logs == 0:
        print("No fallback shader logs were produced.", file=sys.stderr)
        exit_code = 1
    elif args.expect_fallback and total_fallback_events == 0:
        print(
            "Fallback shader logs detected but no fallback events were recorded.",
            file=sys.stderr,
        )
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
