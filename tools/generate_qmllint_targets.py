"""Generate qmllint_targets.txt with explicit .qml file paths.

Usage:
    uv run -- python -m tools.generate_qmllint_targets [--root assets/qml] [--output qmllint_targets.txt]

Ensures directories are expanded into concrete file paths because qmllint does
not accept directories directly in this project workflow.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

DEFAULT_ROOT = Path("assets/qml")
DEFAULT_OUTPUT = Path("qmllint_targets.txt")


def discover_qml(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*.qml") if p.is_file())


def write_targets(files: list[Path], output: Path) -> None:
    lines = [f.as_posix() for f in files]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate qmllint target file")
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Root directory to scan for .qml files",
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT, help="Output file path"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    files = discover_qml(args.root)
    if not files:
        print(f"No .qml files discovered under {args.root}")
        return 1
    write_targets(files, args.output)
    print(f"Generated {len(files)} QML file paths → {args.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
