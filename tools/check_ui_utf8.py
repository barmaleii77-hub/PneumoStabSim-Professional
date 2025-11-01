"""Pre-commit hook to ensure UI-related files are UTF-8 encoded."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
TARGET_DIRECTORIES = ("src", "assets", "docs")
TARGET_EXTENSIONS = {".py", ".qml", ".md"}


def _iter_target_files() -> Iterator[Path]:
    for directory in TARGET_DIRECTORIES:
        dir_path = ROOT_DIR / directory
        if not dir_path.exists():
            continue

        for path in dir_path.rglob("*"):
            if path.is_file() and path.suffix.lower() in TARGET_EXTENSIONS:
                yield path


def _check_file(path: Path) -> bool:
    try:
        path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    except OSError:
        # Treat IO errors as failures so they are surfaced to the user.
        return False
    return True


def main() -> int:
    invalid_files = [path for path in _iter_target_files() if not _check_file(path)]

    if invalid_files:
        print("Found files with invalid UTF-8 encoding:")
        for path in invalid_files:
            print(f" - {path.relative_to(ROOT_DIR)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
