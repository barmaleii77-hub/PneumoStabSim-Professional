"""CI check for forbidden temporary artifacts.

Ensures that stray temporary files, log outputs and patch rejects are not
committed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Iterable, Tuple

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

# Specific repository-relative subpaths to skip
SKIP_SUBPATHS = {Path("docs/_build"), Path("docs/api/generated")}

FORBIDDEN_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("*.rej", "Patch reject file"),
    ("*.orig", "Patch/merge backup file"),
    ("*.bak", "Backup file"),
    ("*~", "Editor backup file"),
    ("*.tmp", "Temporary file"),
    ("*.log", "Temporary log file"),
    ("*_backup*.qml", "Backup QML file"),
    ("*.qml.backup*", "Backup QML file"),
)


def should_skip(path: Path, repo_root: Path) -> bool:
    """Return True if the path should be skipped.

    Skips common virtualenv/build directories and configured repo-relative
    subpaths (for example docs build output).
    """

    # Skip if any component of the path is an ignored directory name
    if any(part in SKIP_DIR_NAMES for part in path.parts):
        return True

    # If path is not under repository root, skip it to avoid surprises
    try:
        relative = path.relative_to(repo_root)
    except Exception:
        return True

    # Skip specific subpaths inside the repository
    for skip_path in SKIP_SUBPATHS:
        try:
            relative.relative_to(skip_path)
        except ValueError:
            # Not under this skip_path
            continue
        # If relative is under skip_path, skip it
        return True

    return False


def find_forbidden(root: Path) -> Dict[Path, str]:
    """Locate forbidden artifacts below *root*.

    Returns a mapping of path -> description for each discovered forbidden file.
    """

    discovered: Dict[Path, str] = {}
    for pattern, description in FORBIDDEN_PATTERNS:
        for match in root.rglob(pattern):
            if not match.is_file():
                continue
            if should_skip(match, root):
                continue
            discovered.setdefault(match, description)
    return discovered


def format_report(paths: Iterable[Tuple[Path, str]], root: Path) -> str:
    """Format a human-readable report of discovered forbidden artifacts."""

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
