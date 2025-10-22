# Veja a descrição de que forma o código foi alterado e aplique as mudanças no arquivo referente a `tools\check_ui_utf8.py`.

#!/usr/bin/env python3
"""Ensure all UI files decode as UTF-8 without errors."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_EXTENSIONS = {".py", ".qml", ".ui"}
DEFAULT_ROOTS = (Path("src/ui"),)


def iter_ui_files(roots: Sequence[Path], extensions: Iterable[str]) -> Iterable[Path]:
    normalized_exts = {ext if ext.startswith(".") else f".{ext}" for ext in extensions}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in normalized_exts:
                yield path


def check_utf8(paths: Sequence[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        try:
            with path.open("r", encoding="utf-8") as handle:
                handle.read()
        except UnicodeDecodeError as exc:
            errors.append(f"{path}: {exc}")
    return errors


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "roots",
        metavar="ROOT",
        nargs="*",
        type=Path,
        default=list(DEFAULT_ROOTS),
        help="Directories to scan (default: src/ui)",
    )
    parser.add_argument(
        "--ext",
        dest="extensions",
        action="append",
        default=list(DEFAULT_EXTENSIONS),
        help="File extensions to validate (default: .py, .qml, .ui)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    roots = [root if root.is_absolute() else Path.cwd() / root for root in args.roots]
    extensions = args.extensions or list(DEFAULT_EXTENSIONS)

    ui_files = list(iter_ui_files(roots, extensions))
    errors = check_utf8(ui_files)

    # Исправление вывода символов в Windows-консоли
    try:
        # Устанавливаем кодировку консоли на UTF-8
        if os.name == "nt":
            sys.stdout.reconfigure(encoding="utf-8")

        if errors:
            print("❌ UTF-8 validation failed for the following files:")
            for error in errors:
                print(f"  - {error}")
            return 1

        print(f"✅ UTF-8 validation passed for {len(ui_files)} UI files.")
        return 0
    except Exception as e:
        print(f"Ошибка: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
