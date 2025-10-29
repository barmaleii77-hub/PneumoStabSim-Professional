"""Normalise text file encodings and newline styles across the repository.

This utility enforces the canonical UTF-8 encoding policy captured in the
renovation master plan.  It rewrites UTF-8 BOM headers, harmonises newline
styles according to file type, and skips binary artefacts.  The script is
designed to be idempotent so it can be invoked from CI or local shells without
introducing noise in the working tree.

Usage examples::

    # Audit the repository and exit with status 1 when fixes are required.
    python -m tools.encoding_normalizer

    # Apply fixes in-place.
    python -m tools.encoding_normalizer --apply

Specific paths can be provided to limit the scan range.  Paths are interpreted
relative to the repository root by default.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
UTF8_BOM = b"\xef\xbb\xbf"


# Canonical newline expectations mirror the rules in ``.gitattributes``.
LF_SUFFIXES: frozenset[str] = frozenset({
    ".cfg",
    ".cmake",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".pyi",
    ".qml",
    ".qmltypes",
    ".qrc",
    ".qsci",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
})

CRLF_SUFFIXES: frozenset[str] = frozenset({
    ".bat",
    ".cmd",
    ".cs",
    ".csproj",
    ".ps1",
    ".psd1",
    ".psm1",
    ".pyproj",
    ".sln",
    ".slnx",
    ".vbproj",
    ".vcxproj",
})

LF_FILENAMES: frozenset[str] = frozenset({
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    ".gitmodules",
    "CMakeLists.txt",
    "Dockerfile",
    "Makefile",
})

EXCLUDED_DIRS: frozenset[str] = frozenset({
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "venv",
})


@dataclass(slots=True)
class NormalisedFile:
    path: Path
    reasons: list[str]


@dataclass(slots=True)
class SkippedFile:
    path: Path
    reason: str


@dataclass(slots=True)
class FailedFile:
    path: Path
    message: str


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Optional files or directories to scan relative to the repository root.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to the project root inferred from this script.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Rewrite files in-place instead of only reporting pending fixes.",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Process hidden directories (except for .git).",
    )
    parser.add_argument(
        "--fail-on-skip",
        action="store_true",
        help="Exit with a non-zero status when files are skipped due to binary content.",
    )
    return parser.parse_args(argv)


def iter_targets(root: Path, paths: Iterable[Path]) -> Iterator[Path]:
    seen: set[Path] = set()

    if not paths:
        paths = [root]

    for raw_path in paths:
        path = raw_path if raw_path.is_absolute() else root / raw_path
        if not path.exists():
            raise FileNotFoundError(f"Target does not exist: {raw_path}")
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        yield resolved


def expected_newline(path: Path) -> str | None:
    name = path.name
    suffix = path.suffix.lower()
    if name in LF_FILENAMES or suffix in LF_SUFFIXES:
        return "\n"
    if suffix in CRLF_SUFFIXES:
        return "\r\n"
    return None


def should_skip_directory(directory: str, include_hidden: bool) -> bool:
    if directory in EXCLUDED_DIRS:
        return True
    if not include_hidden and directory.startswith(".") and directory != ".github":
        return True
    return False


def collect_files(
    targets: Iterable[Path],
    include_hidden: bool,
) -> Iterator[Path]:
    for target in targets:
        if target.is_file():
            yield target
            continue

        for dirpath, dirnames, filenames in os.walk(target):
            dirnames[:] = [
                name
                for name in dirnames
                if not should_skip_directory(name, include_hidden)
            ]
            base = Path(dirpath)
            for filename in filenames:
                yield base / filename


def is_probably_binary(data: bytes) -> bool:
    if not data:
        return False
    if b"\x00" in data:
        return True
    # Heuristic: if a significant portion of the bytes are outside printable ASCII
    # and whitespace ranges, treat the file as binary to avoid corrupting assets.
    text_chars = b"\n\r\t\f\b" + bytes(range(32, 127))
    non_text = sum(byte not in text_chars for byte in data[:1024])
    return non_text > 64


def normalise_file(
    path: Path, newline: str, apply: bool
) -> tuple[NormalisedFile | None, SkippedFile | None, FailedFile | None]:
    original_bytes = path.read_bytes()

    if is_probably_binary(original_bytes):
        return None, SkippedFile(path, "binary content detected"), None

    working_bytes = original_bytes
    reasons: list[str] = []

    if working_bytes.startswith(UTF8_BOM):
        working_bytes = working_bytes[len(UTF8_BOM) :]
        reasons.append("removed UTF-8 BOM")

    try:
        text = working_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        message = f"failed to decode as UTF-8: {exc}"
        return None, None, FailedFile(path, message)

    lf_text = text.replace("\r\n", "\n").replace("\r", "\n")
    if newline == "\n":
        final_text = lf_text
        newline_label = "LF"
    else:
        final_text = lf_text.replace("\n", "\r\n")
        newline_label = "CRLF"

    if final_text != text:
        reasons.append(f"normalised line endings to {newline_label}")

    final_bytes = final_text.encode("utf-8")

    if not reasons and final_bytes == original_bytes:
        return None, None, None

    if final_bytes == original_bytes:
        # The textual transformation did not change the byte sequence; remove the
        # informational reason to avoid reporting false positives.
        return None, None, None

    if apply:
        path.write_bytes(final_bytes)

    if not reasons:
        reasons.append("re-encoded with canonical UTF-8")

    return NormalisedFile(path, reasons), None, None


def run_normaliser(args: argparse.Namespace) -> int:
    targets = list(iter_targets(args.root.resolve(), args.paths))
    files = collect_files(targets, include_hidden=args.include_hidden)

    normalised: list[NormalisedFile] = []
    skipped: list[SkippedFile] = []
    failures: list[FailedFile] = []

    for file_path in files:
        newline = expected_newline(file_path)
        if newline is None:
            continue

        result, skipped_entry, failed_entry = normalise_file(
            file_path, newline=newline, apply=args.apply
        )
        if failed_entry:
            failures.append(failed_entry)
        elif skipped_entry:
            skipped.append(skipped_entry)
        elif result:
            normalised.append(result)

    for entry in failures:
        rel = entry.path.relative_to(args.root)
        print(f"[encoding-normalizer] ERROR {rel}: {entry.message}")

    for entry in skipped:
        rel = entry.path.relative_to(args.root)
        print(f"[encoding-normalizer] SKIP  {rel}: {entry.reason}")

    for entry in normalised:
        rel = entry.path.relative_to(args.root)
        details = ", ".join(entry.reasons)
        action = "updated" if args.apply else "would update"
        print(f"[encoding-normalizer] {action.upper()} {rel}: {details}")

    if failures:
        return 2

    if normalised:
        if args.apply:
            print(
                f"[encoding-normalizer] Applied normalisation to {len(normalised)} file(s)."
            )
            status = 0
        else:
            print(
                "[encoding-normalizer] Normalisation required for "
                f"{len(normalised)} file(s). Re-run with --apply to rewrite."
            )
            status = 1
    else:
        print("[encoding-normalizer] All tracked files already conform to policy.")
        status = 0

    if skipped and args.fail_on_skip:
        print(
            "[encoding-normalizer] Failing due to skipped files. "
            "Inspect the output above for details."
        )
        status = 1 if status == 0 else status

    return status


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return run_normaliser(args)


if __name__ == "__main__":
    raise SystemExit(main())
