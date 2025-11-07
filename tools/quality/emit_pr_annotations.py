"""Aggregate static-analysis warnings and emit a unified annotations log."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

from tools import collect_qml_errors

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUALITY_REPORT_DIR = PROJECT_ROOT / "reports" / "quality"
TEST_REPORT_DIR = PROJECT_ROOT / "reports" / "tests"
LOG_DIR = PROJECT_ROOT / "logs"
WARNING_LOG_PATH = PROJECT_ROOT / "reports" / "warnings.log"

FLAKE8_PATTERN = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+):(?P<col>\d+):\s*(?P<code>[A-Z0-9]+)\s*(?P<message>.+)$"
)
MYPY_PATTERN = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+)(?::(?P<col>\d+))?:\s*(?P<level>error|warning|note):\s*(?P<message>.+)$",
    re.IGNORECASE,
)
QMLLINT_PATTERN = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+):(?P<col>\d+):\s*warning:\s*(?P<message>.+)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class WarningEntry:
    path: str
    line: int | None
    message: str


def _normalise_path(raw: str) -> str:
    text = raw.strip()
    if not text:
        return text
    if text.startswith("qrc:/"):
        return text
    if text.startswith("file://"):
        text = text.replace("file://", "", 1)
    candidate = Path(text)
    if not candidate.is_absolute():
        candidate = (PROJECT_ROOT / text).resolve()
    try:
        return str(candidate.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(candidate)


def _iter_tool_lines(path: Path) -> Iterator[str]:
    content = path.read_text(encoding="utf-8", errors="replace")
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("$") or stripped.startswith("[exit code"):
            continue
        yield stripped


def _collect_from_log(
    path: Path, pattern: re.Pattern[str], *, prefix: str
) -> list[WarningEntry]:
    entries: list[WarningEntry] = []
    if not path.exists():
        return entries
    for raw in _iter_tool_lines(path):
        match = pattern.match(raw)
        if not match:
            continue
        normalized_path = _normalise_path(match.group("path"))
        line = int(match.group("line"))
        message = match.group("message").strip()
        code = match.groupdict().get("code")
        label = f"{prefix} {code}".strip() if code else prefix
        entries.append(WarningEntry(normalized_path, line, f"[{label}] {message}"))
    return entries


def _collect_flake8() -> list[WarningEntry]:
    return _collect_from_log(
        QUALITY_REPORT_DIR / "flake8.log", FLAKE8_PATTERN, prefix="flake8"
    )


def _collect_mypy() -> list[WarningEntry]:
    entries: list[WarningEntry] = []
    path = QUALITY_REPORT_DIR / "mypy.log"
    if not path.exists():
        return entries
    for raw in _iter_tool_lines(path):
        match = MYPY_PATTERN.match(raw)
        if not match:
            continue
        level = match.group("level").lower()
        if level not in {"error", "warning"}:
            continue
        normalized_path = _normalise_path(match.group("path"))
        line = int(match.group("line"))
        message = match.group("message").strip()
        entries.append(WarningEntry(normalized_path, line, f"[mypy {level}] {message}"))
    return entries


def _collect_qmllint() -> list[WarningEntry]:
    return _collect_from_log(
        QUALITY_REPORT_DIR / "qmllint.log",
        QMLLINT_PATTERN,
        prefix="qmllint warning",
    )


def _iter_runtime_logs(extra_roots: Iterable[Path]) -> Iterator[Path]:
    default_roots = [LOG_DIR, TEST_REPORT_DIR]
    seen: set[Path] = set()
    for root in [*default_roots, *extra_roots]:
        if not root:
            continue
        candidate = root if root.is_absolute() else (PROJECT_ROOT / root)
        if not candidate.exists():
            continue
        for path in sorted(candidate.rglob("*.log")):
            if path in seen:
                continue
            seen.add(path)
            yield path


def _collect_qml_runtime(extra_roots: Iterable[Path]) -> list[WarningEntry]:
    entries: list[WarningEntry] = []
    for log_path in _iter_runtime_logs(extra_roots):
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        findings = collect_qml_errors.scan_lines(lines)
        for finding in findings:
            line_no = int(finding.get("line", 0)) or None
            message = str(finding.get("message", "QML warning")).strip()
            entries.append(
                WarningEntry(
                    _normalise_path(str(log_path)),
                    line_no,
                    f"[qml-runtime] {message}",
                )
            )
    return entries


def _write_entries(entries: Iterable[WarningEntry]) -> None:
    unique = {
        (entry.path, entry.line if entry.line is not None else -1, entry.message)
        for entry in entries
    }
    sorted_entries = sorted(
        unique,
        key=lambda item: (item[0], item[1], item[2]),
    )

    WARNING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with WARNING_LOG_PATH.open("w", encoding="utf-8") as handle:
        handle.write("# Aggregated warnings for PR annotations\n")
        for path, line, message in sorted_entries:
            if line >= 1:
                handle.write(f"{path}:{line} - {message}\n")
            else:
                handle.write(f"{path} - {message}\n")

    print(
        f"[emit_pr_annotations] Recorded {len(sorted_entries)} warning(s) → {WARNING_LOG_PATH.relative_to(PROJECT_ROOT)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect analyser warnings for GitHub annotations",
    )
    parser.add_argument(
        "--runtime-root",
        action="append",
        type=Path,
        default=[],
        help="Additional directories to scan for QML runtime logs",
    )
    args = parser.parse_args()

    collected: list[WarningEntry] = []
    collected.extend(_collect_flake8())
    collected.extend(_collect_mypy())
    collected.extend(_collect_qmllint())
    collected.extend(_collect_qml_runtime(args.runtime_root))

    _write_entries(collected)


if __name__ == "__main__":
    main()
