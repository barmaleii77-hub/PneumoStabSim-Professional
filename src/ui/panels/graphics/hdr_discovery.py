"""Helpers for discovering HDR and EXR assets used by the graphics panel."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence, Tuple

__all__ = ["discover_hdr_files"]

_SUPPORTED_PATTERNS: Tuple[str, ...] = ("*.hdr", "*.exr")


def _resolve(path: Path) -> Path:
    """Return ``path.resolve()`` while tolerating filesystem errors."""

    try:
        return path.resolve()
    except OSError:
        return path


def _to_qml_relative(path: Path, qml_root: Path) -> str:
    """Return a POSIX path relative to ``qml_root`` when possible."""

    resolved_root = _resolve(qml_root)
    resolved_path = _resolve(path)

    try:
        relative = resolved_path.relative_to(resolved_root)
        return relative.as_posix()
    except ValueError:
        try:
            relpath = os.path.relpath(resolved_path, start=resolved_root)
            return Path(relpath).as_posix()
        except OSError:
            return resolved_path.as_posix()


def discover_hdr_files(
    search_dirs: Sequence[Path], *, qml_root: Path
) -> list[tuple[str, str]]:
    """Discover available HDR/EXR assets for the graphics panel."""

    results: list[tuple[str, str]] = []
    seen_names: set[str] = set()

    for base in search_dirs:
        base_path = Path(base)
        if not base_path.exists():
            continue

        for pattern in _SUPPORTED_PATTERNS:
            for candidate in sorted(base_path.rglob(pattern)):
                key = candidate.name.lower()
                if key in seen_names:
                    continue
                seen_names.add(key)
                results.append((candidate.name, _to_qml_relative(candidate, qml_root)))

    return results
