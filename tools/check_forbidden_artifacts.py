"""CI check for forbidden temporary artifacts.

Ensures that stray QML backup files and patch rejects are not committed.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

# Directories to skip entirely when scanning for artifacts
SKIP_DIR_NAMES = {
    ".git",
    "archive",  # archived data may legitimately contain old backups
    "venv",
    ".venv",
    "env",
    "node_modules",
    "__pycache__",
}

FORBIDDEN_PATTERNS: tuple[tuple[str, str], ...] = (
    ("*.rej", "Patch reject file"),
    ("*_backup*.qml", "Backup QML file"),
    ("*.qml.backup*", "Backup QML file"),
)


def should_skip(path: Path) -> bool:
    """Return True if the path should be skipped."""
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def find_forbidden(root: Path) -> dict[Path, str]:
    """Locate forbidden artifacts below *root*."""
    discovered: dict[Path, str] = {}
    for pattern, description in FORBIDDEN_PATTERNS:
        for match in root.rglob(pattern):
            if not match.is_file():
                continue
            if should_skip(match):
                continue
            discovered.setdefault(match, description)
    return discovered


def format_report(paths: Iterable[tuple[Path, str]], root: Path) -> str:
    lines = ["Forbidden artifacts detected:"]
    for path, description in sorted(paths, key=lambda item: str(item[0])):
        relative_path = path.relative_to(root)
        lines.append(f"- {relative_path} ({description})")
    return "\n".join(lines)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    forbidden = find_forbidden(repo_root)

    if forbidden:
        report = format_report(forbidden.items(), repo_root)
        print(report)
        return 1

    print("No forbidden artifacts detected.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
