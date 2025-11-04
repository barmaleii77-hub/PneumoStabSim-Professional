"""Validate shader variant coverage and GLSL profiles.

This script enforces the Phase 3 requirement that each desktop shader provides
an OpenGL fallback and an OpenGL ES variant with the expected ``#version``
annotations.  It is lightweight enough for CI usage and exports helper
functions that unit tests can import.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SHADER_ROOT = PROJECT_ROOT / "assets" / "shaders"
SUPPORTED_SUFFIXES = {".frag", ".vert"}

VARIANT_SUFFIXES: tuple[tuple[str, str], ...] = (
    ("_fallback_es", "fallback_es"),
    ("_fallback", "fallback"),
    ("_es", "es"),
)

EXPECTED_VERSIONS: Mapping[tuple[str, str], str] = {
    ("desktop", ".frag"): "#version 450 core",
    ("desktop", ".vert"): "#version 450 core",
    ("es", ".frag"): "#version 300 es",
    ("es", ".vert"): "#version 300 es",
    ("fallback", ".frag"): "#version 330 core",
    ("fallback_es", ".frag"): "#version 300 es",
}


@dataclass(frozen=True)
class ShaderFile:
    """Metadata captured for a single shader variant."""

    path: Path
    variant: str
    extension: str

    @property
    def base_name(self) -> str:
        return classify_shader(self.path)[0]


ValidationErrors = List[str]


def classify_shader(path: Path) -> tuple[str, str]:
    """Return the base name and variant label for *path*."""

    stem = path.stem
    for suffix, label in VARIANT_SUFFIXES:
        if stem.endswith(suffix):
            return stem[: -len(suffix)], label
    return stem, "desktop"


def _read_first_significant_line(path: Path) -> str | None:
    """Return the first non-empty, non-comment line from *path*."""

    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            stripped = raw.strip()
            if not stripped or stripped.startswith("//"):
                continue
            return stripped
    return None


def _collect_shader_files(shader_root: Path) -> dict[tuple[str, str], list[ShaderFile]]:
    """Group shader files by base name and extension."""

    grouped: dict[tuple[str, str], list[ShaderFile]] = {}
    for path in sorted(shader_root.rglob("*")):
        if not path.is_file() or path.suffix not in SUPPORTED_SUFFIXES:
            continue
        base, variant = classify_shader(path)
        grouped.setdefault((base, path.suffix), []).append(
            ShaderFile(path=path, variant=variant, extension=path.suffix)
        )
    return grouped


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _validate_versions(
    files: Iterable[ShaderFile], root: Path, errors: ValidationErrors
) -> None:
    for shader in files:
        expected = EXPECTED_VERSIONS.get((shader.variant, shader.extension))
        if expected is None:
            continue
        directive = _read_first_significant_line(shader.path)
        if directive is None:
            errors.append(f"{_relative(shader.path, root)}: missing #version directive")
            continue
        if directive != expected:
            errors.append(
                f"{_relative(shader.path, root)}: expected '{expected}' but found '{directive}'"
            )


def validate_shaders(shader_root: Path) -> ValidationErrors:
    """Return a list of validation error messages for *shader_root*."""

    errors: ValidationErrors = []

    if not shader_root.exists():
        return [f"Shader directory does not exist: {shader_root}"]

    grouped = _collect_shader_files(shader_root)
    for (base, extension), files in sorted(grouped.items()):
        desktops = [item for item in files if item.variant == "desktop"]
        if not desktops:
            continue

        es_variants = [item for item in files if item.variant == "es"]
        if not es_variants:
            errors.append(
                f"{base}{extension}: missing GLES variant (expected file '*_es{extension}')"
            )

        if extension == ".frag":
            fallback_variants = [item for item in files if item.variant == "fallback"]
            if not fallback_variants:
                errors.append(
                    f"{base}{extension}: missing fallback variant (expected file '*_fallback{extension}')"
                )

            fallback_es_variants = [item for item in files if item.variant == "fallback_es"]
            if not fallback_es_variants:
                errors.append(
                    f"{base}{extension}: missing fallback ES variant (expected file '*_fallback_es{extension}')"
                )

        _validate_versions(files, shader_root, errors)

    return errors


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--shader-root",
        type=Path,
        default=DEFAULT_SHADER_ROOT,
        help="Path to the shader assets directory (default: assets/shaders)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress success output; errors are always printed to stderr.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    shader_root = args.shader_root.resolve()
    errors = validate_shaders(shader_root)

    if errors:
        for message in errors:
            print(f"[validate_shaders] ERROR: {message}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Shader validation OK: {_relative(shader_root, PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
