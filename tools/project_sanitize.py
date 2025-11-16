"""Utility helpers to remove transient artefacts from the repository.

Расширено: добавлена очистка артефактов tests (junit xml, pytest_* логи) с
параметром --tests-history и сводка в JSON.
"""

from __future__ import annotations
import argparse
import json
import shutil
import sys
from pathlib import Path
from collections.abc import Iterable, Sequence

COMPACT_REPORT_HISTORY_FLAG = "--report-history"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUALITY_ROOT = PROJECT_ROOT / "reports" / "quality"
TRACE_ROOT = QUALITY_ROOT / "launch_traces"
TESTS_ROOT = PROJECT_ROOT / "reports" / "tests"

SOLUTION_PATTERNS: Sequence[str] = ("*.suo", "*.user", "*.VC.db", "*.ipch")
REPORT_PATTERNS: Sequence[tuple[Path, str]] = (
    (QUALITY_ROOT, "autonomous_check_*.log"),
    (QUALITY_ROOT, "environment_report_*.md"),
    (TRACE_ROOT, "launch_trace_*.log"),
    (TRACE_ROOT, "environment_report_*.md"),
)
TEST_PATTERNS: Sequence[str] = (
    "pytest_*.log",
    "pytest_*.xml",
    "manual.xml",
    "coverage.json",  # можно чистить при сжатии истории
    "skipped_tests_summary.md",
)


def _normalise_argv(argv: Sequence[str] | None) -> list[str]:
    """Expand compact ``--report-history`` flags into a separate value token."""

    if argv is None:
        return []

    normalised: list[str] = []
    for token in argv:
        if token.startswith(COMPACT_REPORT_HISTORY_FLAG):
            if token == COMPACT_REPORT_HISTORY_FLAG:
                normalised.append(token)
                continue

            remainder = token[len(COMPACT_REPORT_HISTORY_FLAG) :]
            if remainder and remainder.lstrip("-+").isdigit():
                normalised.extend([COMPACT_REPORT_HISTORY_FLAG, remainder])
                continue

            if remainder.startswith("="):
                value = remainder[1:]
                if value and value.lstrip("-+").isdigit():
                    normalised.extend([COMPACT_REPORT_HISTORY_FLAG, value])
                    continue

        normalised.append(token)

    return normalised


def _is_within_git(path: Path) -> bool:
    """Return True if the path is located inside the Git metadata directory."""

    try:
        return ".git" in path.relative_to(PROJECT_ROOT).parts
    except ValueError:
        # Path lies outside the project root – treat as inside Git to avoid deletion.
        return True


def _iter_pycache() -> Iterable[Path]:
    for directory in PROJECT_ROOT.rglob("__pycache__"):
        if not _is_within_git(directory):
            yield directory


def _iter_pyc_files() -> Iterable[Path]:
    for file_path in PROJECT_ROOT.rglob("*.pyc"):
        if not _is_within_git(file_path):
            yield file_path


def _iter_solution_artifacts() -> Iterable[Path]:
    for pattern in SOLUTION_PATTERNS:
        yield from PROJECT_ROOT.glob(pattern)


def _remove_path(path: Path, *, dry_run: bool, verbose: bool) -> bool:
    if not path.exists():
        return False

    if dry_run:
        print(f"[dry-run] Would remove {path.relative_to(PROJECT_ROOT)}")
        return True

    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)

    if verbose:
        print(f"Removed {path.relative_to(PROJECT_ROOT)}")
    return True


def _prune_reports(*, keep: int, dry_run: bool, verbose: bool) -> int:
    removed = 0
    if keep < 0:
        keep = 0

    for directory, pattern in REPORT_PATTERNS:
        if not directory.exists():
            continue

        matched = sorted(directory.glob(pattern))
        excess = len(matched) - keep
        if excess <= 0:
            continue

        for path in matched[:excess]:
            if _remove_path(path, dry_run=dry_run, verbose=verbose):
                removed += 1

    return removed


def _prune_directory_patterns(
    directory: Path, patterns: Sequence[str], keep: int, *, dry_run: bool, verbose: bool
) -> int:
    removed = 0
    if keep < 0:
        keep = 0
    for pattern in patterns:
        matched = sorted(directory.glob(pattern))
        excess = len(matched) - keep
        if excess <= 0:
            continue
        for path in matched[:excess]:
            if _remove_path(path, dry_run=dry_run, verbose=verbose):
                removed += 1
    return removed


def sanitize_repository(
    *, dry_run: bool, verbose: bool, report_history: int, tests_history: int
) -> None:
    removed_items = 0
    pycache_removed = 0
    test_logs_pruned = 0
    quality_logs_pruned = 0

    for path in _iter_pycache():
        if _remove_path(path, dry_run=dry_run, verbose=verbose):
            removed_items += 1
            pycache_removed += 1

    for file_path in _iter_pyc_files():
        if _remove_path(file_path, dry_run=dry_run, verbose=verbose):
            removed_items += 1
            pycache_removed += 1

    for artifact in _iter_solution_artifacts():
        if _remove_path(artifact, dry_run=dry_run, verbose=verbose):
            removed_items += 1

    quality_logs_pruned += _prune_reports(
        keep=report_history,
        dry_run=dry_run,
        verbose=verbose,
    )
    removed_items += quality_logs_pruned

    if TESTS_ROOT.exists():
        test_logs_pruned += _prune_directory_patterns(
            TESTS_ROOT, TEST_PATTERNS, tests_history, dry_run=dry_run, verbose=verbose
        )
        removed_items += test_logs_pruned

    if removed_items == 0:
        message = "No sanitisation actions were necessary."
    else:
        message = (
            f"Sanitisation completed: {removed_items} artefact(s) processed (pycache={pycache_removed}, "
            f"quality_pruned={quality_logs_pruned}, tests_pruned={test_logs_pruned})."
        )
    print(message)

    # Сводка JSON для последующего анализа
    summary_path = QUALITY_ROOT / "sanitize_summary.json"
    summary_payload = {
        "pycache_removed": pycache_removed,
        "quality_logs_pruned": quality_logs_pruned,
        "tests_logs_pruned": test_logs_pruned,
        "total_processed": removed_items,
        "report_history": report_history,
        "tests_history": tests_history,
        "dry_run": dry_run,
    }
    try:
        QUALITY_ROOT.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(summary_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except Exception:
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Remove transient caches, stale diagnostic artefacts, and solution "
            "temporary files from the repository."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List the actions without deleting files.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print each removal as it happens."
    )
    parser.add_argument(
        "--report-history",
        type=int,
        default=3,
        help="How many historical quality report artefacts to keep (default: 3).",
    )
    parser.add_argument(
        "--tests-history",
        type=int,
        default=2,
        help="How many historical test artefacts (pytest_*.xml/log) to keep (default: 2).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(_normalise_argv(argv))
    sanitize_repository(
        dry_run=args.dry_run,
        verbose=args.verbose,
        report_history=args.report_history,
        tests_history=args.tests_history,
    )


if __name__ == "__main__":
    main(sys.argv[1:])
