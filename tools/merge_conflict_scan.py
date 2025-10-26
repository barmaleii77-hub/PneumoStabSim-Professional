"""Repository merge-conflict marker scanner.

This utility walks the project tree and fails if any file still contains
Git-style merge conflict markers. Keeping the logic in a dedicated module lets
CI and local pre-flight checks ensure the tree stays conflict-free.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

# Standard Git conflict markers. `=======` is intentionally omitted because it
# appears legitimately in ASCII art banners throughout the repository; we only
# flag it when paired with the directional markers below.
MARKERS: tuple[bytes, ...] = (b"<<<<<<< ", b">>>>>>> ", b"||||||| ")
DEFAULT_EXCLUDES: tuple[str, ...] = (".git", "__pycache__", ".vs")


def _should_exclude(path: Path, excludes: Iterable[str]) -> bool:
    return any(part in excludes for part in path.parts)


def _contains_marker(payload: bytes) -> bool:
    for line in payload.splitlines():
        if any(line.startswith(marker) for marker in MARKERS):
            return True
    return False


def find_conflicted_files(root: Path, excludes: Iterable[str]) -> list[Path]:
    conflicted: list[Path] = []
    for candidate in root.rglob("*"):
        if not candidate.is_file():
            continue
        if _should_exclude(candidate, excludes):
            continue
        try:
            payload = candidate.read_bytes()
        except OSError:
            # Ignore unreadable paths (permissions, transient files, etc.).
            continue
        if _contains_marker(payload):
            conflicted.append(candidate)
    return conflicted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fail if Git merge conflict markers remain in the repository.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to scan (defaults to current working directory).",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=list(DEFAULT_EXCLUDES),
        help="Directories to skip during the scan.",
    )
    args = parser.parse_args()

    conflicted = find_conflicted_files(args.root, args.exclude)
    if conflicted:
        for path in conflicted:
            print(path)
        raise SystemExit(
            f"Found {len(conflicted)} file(s) containing Git merge conflict markers."
        )


if __name__ == "__main__":
    main()
