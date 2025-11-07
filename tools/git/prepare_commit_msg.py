#!/usr/bin/env python3
"""Prepare-commit-msg hook that suggests Conventional Commit scopes.

This helper analyses the staged changes and injects a comment with the inferred
scopes into the commit message template. The hint makes it easier for
contributors to pick the right ``type(scope): summary`` format without enforcing
it automatically.

Usage (Git hook)::

    ln -s ../../tools/git/prepare_commit_msg.py .git/hooks/prepare-commit-msg
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from collections.abc import Iterable, Sequence

IGNORED_SOURCES = {"merge", "squash", "commit"}

_SCOPE_RULES: Sequence[tuple[str, str]] = (
    ("src/ui/panels/geometry", "ui-geometry"),
    ("src/ui/panels/graphics", "ui-graphics"),
    ("src/ui/panels/modes", "ui-modes"),
    ("src/ui/panels", "ui-panels"),
    ("src/ui", "ui"),
    ("src/core", "core"),
    ("src/common", "common"),
    ("src/infrastructure", "infrastructure"),
    ("src/simulation", "simulation"),
    ("src/diagnostics", "diagnostics"),
    ("src/bootstrap", "bootstrap"),
    ("config", "config"),
    ("assets/qml", "qml"),
    ("assets", "assets"),
    ("tests/ui", "tests-ui"),
    ("tests/simulation", "tests-simulation"),
    ("tests", "tests"),
    ("tools", "tools"),
    ("docs", "docs"),
)


def _get_staged_files() -> list[str]:
    """Return staged file paths using POSIX separators."""
    result = subprocess.run(
        [
            "git",
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACMRTUXB",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in {0, 1}:
        # git returns 1 when there is no diff; treat as empty set.
        raise SystemExit(result.returncode)
    paths: list[str] = []
    for raw_path in result.stdout.splitlines():
        path = raw_path.strip()
        if not path:
            continue
        # Normalize to POSIX separators for rule matching.
        normalized = Path(path).as_posix()
        if normalized.startswith(".git/"):
            continue
        paths.append(normalized)
    return paths


def _infer_scope(path: str) -> str:
    for prefix, scope in _SCOPE_RULES:
        if path.startswith(prefix):
            return scope
    head = path.split("/", 1)[0]
    return head.replace("_", "-").replace(".", "-").lower()


def _collect_scopes(paths: Iterable[str]) -> list[str]:
    scopes = {_infer_scope(path) for path in paths}
    scopes = {scope for scope in scopes if scope}
    return sorted(scopes)


def _read_message(path: Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    return content.splitlines()


def _write_message(path: Path, lines: Sequence[str]) -> None:
    text = "\n".join(lines)
    if lines:
        text += "\n"
    path.write_text(text, encoding="utf-8")


def _should_skip_for_source(args: Sequence[str]) -> bool:
    if len(args) < 3:
        return False
    source = args[2]
    return source in IGNORED_SOURCES


def main(argv: Sequence[str]) -> int:
    if len(argv) < 2:
        return 0

    if _should_skip_for_source(argv):
        return 0

    message_path = Path(argv[1])
    staged_files = _get_staged_files()
    scopes = _collect_scopes(staged_files)
    if not scopes:
        return 0

    existing_lines = [
        line
        for line in _read_message(message_path)
        if not line.startswith("# Suggested scopes:")
    ]
    suggestion = f"# Suggested scopes: {', '.join(scopes)}"
    new_lines = [suggestion, *existing_lines]
    _write_message(message_path, new_lines)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
