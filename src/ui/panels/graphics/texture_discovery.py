"""Helpers for discovering material textures for the graphics panel."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

__all__ = ["discover_texture_files"]

_SUPPORTED_PATTERNS: tuple[str, ...] = ("*.png",)


def _resolve(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path


def _to_qml_relative(path: Path, qml_root: Path) -> str:
    resolved_root = _resolve(qml_root)
    resolved_path = _resolve(path)

    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        try:
            rel = os.path.relpath(resolved_path, start=resolved_root)
            return Path(rel).as_posix()
        except OSError:
            return resolved_path.as_posix()


def discover_texture_files(
    search_dirs: Sequence[Path], *, qml_root: Path
) -> list[tuple[str, str]]:
    """Discover PNG textures relative to the QML root directory."""

    results: list[tuple[str, str]] = []
    seen: set[str] = set()

    for base in search_dirs:
        base_path = Path(base)
        if not base_path.exists():
            continue

        for pattern in _SUPPORTED_PATTERNS:
            for candidate in sorted(base_path.rglob(pattern)):
                key = candidate.name.lower()
                if key in seen:
                    continue
                seen.add(key)
                results.append((candidate.name, _to_qml_relative(candidate, qml_root)))

    return results
