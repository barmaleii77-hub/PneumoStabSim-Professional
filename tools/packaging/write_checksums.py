"""Generate SHA-256 checksum sidecar files for release artifacts."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
from collections.abc import Iterable

SUPPORTED_EXTENSIONS: tuple[str, ...] = (".zip", ".tar.gz", ".whl")


def _iter_artifacts(directory: Path, extensions: Iterable[str]) -> list[Path]:
    candidates: list[Path] = []
    for entry in sorted(directory.glob("**/*")):
        if entry.is_dir():
            continue
        if not entry.name:
            continue
        for ext in extensions:
            if entry.name.endswith(ext):
                candidates.append(entry)
                break
    return candidates


def _write_checksum(path: Path) -> Path:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checksum_path = Path(f"{path}.sha256")
    checksum_path.write_text(f"{digest}  {path.name}{os.linesep}", encoding="utf-8")
    return checksum_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path("dist/packages"),
        help="Directory containing artifacts that should be checksummed.",
    )
    parser.add_argument(
        "--extension",
        action="append",
        dest="extensions",
        help="Optional list of extensions (default: .zip, .tar.gz, .whl).",
    )
    args = parser.parse_args(argv)

    target_dir = args.directory.resolve()
    if not target_dir.exists():
        raise SystemExit(f"Artifact directory does not exist: {target_dir}")

    extensions = tuple(args.extensions) if args.extensions else SUPPORTED_EXTENSIONS
    artifacts = _iter_artifacts(target_dir, extensions)
    if not artifacts:
        return 0

    for artifact in artifacts:
        _write_checksum(artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
