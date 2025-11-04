"""Validate shader variant coverage and GLSL profiles.

This script enforces the Phase 3 requirement that each desktop shader provides
an OpenGL fallback and an OpenGL ES variant with the expected ``#version``
annotations.  It is lightweight enough for CI usage and exports helper
functions that unit tests can import.
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SHADER_ROOT = PROJECT_ROOT / "assets" / "shaders"
DEFAULT_REPORTS_ROOT = PROJECT_ROOT / "reports" / "shaders"
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
    ("fallback", ".frag"): "#version 450 core",
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

QSB_ENV_VARIABLE = "QSB_COMMAND"


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


def _resolve_qsb_command() -> list[str]:
    """Return the qsb command configured for the current environment."""

    configured = os.environ.get(QSB_ENV_VARIABLE)
    if configured:
        command = [item for item in shlex.split(configured) if item]
        if not command:
            raise RuntimeError(
                "Environment variable QSB_COMMAND is set but empty; provide an executable"
            )
        return command

    resolved = shutil.which("qsb")
    if resolved:
        return [resolved]

    raise FileNotFoundError(
        "qsb executable not found; install Qt Shader Tools or set QSB_COMMAND"
    )


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _shader_reports_paths(
    reports_dir: Path | None, shader: ShaderFile, root: Path
) -> tuple[Path | None, Path | None]:
    if reports_dir is None:
        return None, None

    relative = shader.path.relative_to(root)
    base = reports_dir / relative
    output_path = base.with_suffix(".qsb")
    log_path = base.with_suffix(".log")
    _ensure_directory(output_path.parent)
    return output_path, log_path


def _run_qsb(
    shader: ShaderFile,
    shader_root: Path,
    qsb_command: Sequence[str] | None,
    reports_dir: Path | None,
    errors: ValidationErrors,
) -> None:
    if qsb_command is None:
        return
    output_path, log_path = _shader_reports_paths(reports_dir, shader, shader_root)

    command = [
        *qsb_command,
        "--glsl",
        "450",
        "--glsl",
        "300es",
        "--hlsl",
        "50",
        "--msl",
        "12",
    ]
    if output_path is not None:
        command.extend(["-o", str(output_path)])
    command.append(str(shader.path))

    completed = subprocess.run(command, capture_output=True, text=True)

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    if log_path is not None:
        log_contents = ["$ " + " ".join(shlex.quote(arg) for arg in command)]
        if stdout:
            log_contents.append("[stdout]\n" + stdout)
        if stderr:
            log_contents.append("[stderr]\n" + stderr)
        log_path.write_text("\n\n".join(log_contents), encoding="utf-8")

    if completed.returncode != 0:
        errors.append(
            f"{_relative(shader.path, shader_root)}: qsb failed with exit code {completed.returncode}"
        )
        if stderr:
            first_line = stderr.strip().splitlines()[0]
            errors.append(f"    {first_line}")


def validate_shaders(
    shader_root: Path,
    *,
    qsb_command: Sequence[str] | None = None,
    reports_dir: Path | None = None,
    warnings: list[str] | None = None,
) -> ValidationErrors:
    """Return a list of validation error messages for *shader_root*."""

    errors: ValidationErrors = []
    collected_warnings: list[str] = []

    if not shader_root.exists():
        return [f"Shader directory does not exist: {shader_root}"]

    try:
        command = (
            list(qsb_command) if qsb_command is not None else _resolve_qsb_command()
        )
    except (FileNotFoundError, RuntimeError) as exc:
        command = None
        collected_warnings.append(str(exc))

    if reports_dir is not None:
        _ensure_directory(reports_dir)

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

            fallback_es_variants = [
                item for item in files if item.variant == "fallback_es"
            ]
            if not fallback_es_variants:
                errors.append(
                    f"{base}{extension}: missing fallback ES variant (expected file '*_fallback_es{extension}')"
                )

        _validate_versions(files, shader_root, errors)

        for shader in files:
            _run_qsb(shader, shader_root, command, reports_dir, errors)

    if warnings is not None:
        warnings.extend(collected_warnings)
    elif collected_warnings:
        setattr(validate_shaders, "_last_warnings", list(collected_warnings))

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
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS_ROOT,
        help="Directory to store qsb compilation artefacts/logs (default: reports/shaders)",
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
    reports_dir = args.reports_dir.resolve() if args.reports_dir else None
    warning_messages: list[str] = []
    errors = validate_shaders(
        shader_root, reports_dir=reports_dir, warnings=warning_messages
    )

    for message in warning_messages:
        print(f"[validate_shaders] WARNING: {message}", file=sys.stderr)

    if errors:
        for message in errors:
            print(f"[validate_shaders] ERROR: {message}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Shader validation OK: {_relative(shader_root, PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
