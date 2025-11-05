#!/usr/bin/env python
"""Validate shader sources for BOM usage and GLSL versions."""
from __future__ import annotations

import pathlib
import re
import sys
from typing import Iterable, List

ROOT = pathlib.Path(__file__).resolve().parents[1]
SHADER_ROOT = ROOT / "assets" / "shaders"
BOM = b"\xef\xbb\xbf"
VERSION_RE = re.compile(r"^\s*#\s*version\s+(\d+)(?:\s+(\w+))?", re.IGNORECASE)


def iter_shader_files() -> Iterable[pathlib.Path]:
    patterns = ("*.frag", "*.vert")
    if not SHADER_ROOT.exists():
        return []
    files: List[pathlib.Path] = []
    for pattern in patterns:
        files.extend(SHADER_ROOT.rglob(pattern))
    return sorted(files)


def fail(message: str) -> None:
    print(f"[shader-sanity] ERROR: {message}")


def validate_version(path: pathlib.Path, header: str) -> bool:
    match = VERSION_RE.match(header)
    if not match:
        fail(f"{path}: first line must be '#version …'")
        return False
    version = int(match.group(1))
    profile = (match.group(2) or "").lower()
    name = path.name
    if name.endswith("_es.frag") or name.endswith("_es.vert"):
        if version < 300 or profile != "es":
            fail(f"{path}: expected '#version 300 es', found '{header}'")
            return False
        return True
    if name.endswith("_fallback.frag") or name.endswith("_fallback.vert"):
        if version < 330:
            fail(f"{path}: fallback shaders should target >= 330, found '{header}'")
            return False
        return True
    if version < 450 or profile not in ("", "core"):
        fail(f"{path}: main shaders should target 450 core, found '{header}'")
        return False
    return True


def validate_shader(path: pathlib.Path) -> bool:
    data = path.read_bytes()
    if data.startswith(BOM):
        fail(f"{path}: contains UTF-8 BOM")
        return False
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:  # pragma: no cover
        fail(f"{path}: not valid UTF-8 ({exc})")
        return False
    lines = text.splitlines()
    if not lines:
        fail(f"{path}: empty file")
        return False
    return validate_version(path, lines[0])


def main() -> int:
    shaders = list(iter_shader_files())
    if not shaders:
        print("[shader-sanity] no shader files found under assets/shaders")
        return 0
    ok = True
    for shader in shaders:
        ok &= validate_shader(shader)
    if ok:
        print("[shader-sanity] DONE")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
