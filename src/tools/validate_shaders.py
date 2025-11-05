"""Validate shader variant coverage and GLSL profiles.

This script enforces the Phase 3 requirement that each desktop shader provides
an OpenGL fallback and an OpenGL ES variant with the expected ``#version``
annotations.  It is lightweight enough for CI usage and exports helper
functions that unit tests can import.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from contextlib import suppress
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

QSB_PROFILE_ARGUMENTS: tuple[str, ...] = (
    "-D",
    "QSB_USE_UNIFORM_BLOCK",
    "-D",
    "MAIN=main",
    "--glsl",
    "450",
    "--glsl",
    "300es",
    "--hlsl",
    "50",
    "--msl",
    "12",
)


RUNTIME_DEPENDENCY_HINTS: tuple[tuple[str, str], ...] = (
    ("libxkbcommon.so.0", "libxkbcommon0"),
    ("libGL.so.1", "libgl1"),
    ("libEGL.so.1", "libegl1"),
)


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


class ShaderValidationUnavailableError(RuntimeError):
    """Raised when qsb cannot run due to a missing runtime dependency."""


class QsbEnvironmentError(RuntimeError):
    """Raised when qsb fails because the Qt runtime is misconfigured."""


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


def _summarize_environment_failure(
    exit_code: int,
    stdout: str,
    stderr: str,
    command: Sequence[str],
) -> str | None:
    """Return a human-friendly summary for environment-level qsb failures."""

    combined = "\n".join(part for part in (stdout, stderr) if part).lower()
    for library, package in RUNTIME_DEPENDENCY_HINTS:
        if library.lower() in combined:
            return (
                "Qt Shader Baker failed to load required shared library "
                f"'{library}'. Install the system package '{package}' and retry."
            )

    if "qt.qpa.plugin" in combined and "xcb" in combined:
        return (
            "Qt Shader Baker could not load the 'xcb' Qt platform plugin. "
            "Install the Qt X11 runtime dependencies (for example 'libxcb-xinerama0')."
        )

    if exit_code == 127:
        quoted = " ".join(shlex.quote(part) for part in command)
        return (
            "Qt Shader Baker exited with status 127. Ensure the 'qsb' executable is "
            "installed (Qt Shader Tools) or set QSB_COMMAND to its absolute path. "
            f"Command attempted: {quoted or '<unknown>'}."
        )

    return None


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

    for executable in ("qsb", "pyside6-qsb", "pyside2-qsb"):
        resolved = shutil.which(executable)
        if resolved:
            return [resolved]

    candidate_dirs: list[Path] = []

    for var in ("QT_INSTALL_BINS", "QT6_INSTALL_BINS", "QTDIR"):
        value = os.environ.get(var)
        if not value:
            continue
        candidate_dirs.append(Path(value))
        candidate_dirs.append(Path(value) / "bin")

    candidate_dirs.extend(
        Path(path)
        for path in (
            "/usr/lib/qt6/bin",
            "/usr/lib64/qt6/bin",
            "/usr/local/lib/qt6/bin",
            "/opt/qt6/bin",
        )
    )

    for directory in candidate_dirs:
        for executable in ("qsb", "pyside6-qsb", "pyside2-qsb"):
            qsb_path = directory / executable
            if qsb_path.exists() and qsb_path.is_file():
                return [str(qsb_path)]

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


def _extract_missing_shared_library(stderr: str) -> str | None:
    """Return the missing shared library mentioned in *stderr*, if any."""

    marker = "error while loading shared libraries:"
    for line in stderr.splitlines():
        if marker not in line:
            continue
        _, tail = line.split(marker, 1)
        candidate = tail.strip()
        if not candidate:
            continue
        library, *_ = candidate.split(":", 1)
        library = library.strip()
        if library:
            return library
    return None


def _summarize_environment_failure(
    return_code: int, stdout: str, stderr: str, _command: Sequence[str]
) -> str | None:
    """Return a human friendly description for common qsb bootstrap issues."""

    if return_code == 0:
        return None

    combined = "\n".join(filter(None, (stdout, stderr))).lower()
    if not combined:
        return None

    if "qt.qpa.plugin" in combined and "xcb" in combined:
        return (
            "Qt Shader Baker could not load the Qt XCB platform plugin. "
            "Install the headless Qt runtime dependencies (libxcb1, "
            "libxkbcommon0, libxkbcommon-x11-0, libegl1, libgl1) or activate "
            "the project environment before running qsb."
        )

    if "qt.qpa.plugin" in combined and "could not find" in combined:
        return (
            "Qt Shader Baker is missing the Qt platform plugins. "
            "Ensure QT_PLUGIN_PATH is set correctly (source activate_environment.sh) "
            "or reinstall the Qt tooling."
        )

    if "failed to create opengl context" in combined or "could not initialize opengl" in combined:
        return (
            "Qt Shader Baker failed to initialise an OpenGL context. "
            "Install the system OpenGL libraries (e.g. 'apt-get install -y libgl1 libegl1')."
        )

    if "error while loading shared libraries" in combined:
        missing = _extract_missing_shared_library(stderr)
        if missing:
            package_hint = _package_for_library(missing)
            if package_hint:
                return (
                    "Qt Shader Baker could not start because the shared library "
                    f"'{missing}' is missing (install '{package_hint}')."
                )
            return f"Qt Shader Baker could not start because the shared library '{missing}' is missing."

    return None


def _diagnose_qsb_failure(stderr: str) -> list[str]:
    """Return supplemental diagnostic hints based on qsb stderr output."""

    hints: list[str] = []
    lower = (stderr or "").lower()

    if "qt.qpa.plugin" in lower and "xcb" in lower:
        hints.append(
            "    Hint: Install Qt platform dependencies (libxcb1, libxkbcommon0, "
            "libxkbcommon-x11-0) or export QT_QPA_PLATFORM=offscreen."
        )

    if "qt.qpa.plugin" in lower and "could not find" in lower:
        hints.append(
            "    Hint: Ensure QT_PLUGIN_PATH points to the Qt plugins directory "
            "(source activate_environment.sh)."
        )

    if "failed to create opengl context" in lower or "could not initialize opengl" in lower:
        hints.append(
            "    Hint: Install OpenGL runtime libraries such as libgl1 and libegl1 "
            "on the host system."
        )

    missing = _extract_missing_shared_library(stderr)
    if missing:
        package_hint = _package_for_library(missing)
        if package_hint:
            hints.append(
                "    Hint: Install the missing shared library "
                f"'{missing}' via 'apt-get install -y {package_hint}'."
            )
        else:
            hints.append(
                "    Hint: Install the missing shared library "
                f"'{missing}' using your package manager."
            )

    return hints


def _package_for_library(library: str) -> str | None:
    for shared, package in RUNTIME_DEPENDENCY_HINTS:
        if shared == library:
            return package
    return None


def _run_qsb(
    shader: ShaderFile,
    shader_root: Path,
    qsb_command: Sequence[str],
    reports_dir: Path | None,
    errors: ValidationErrors,
) -> None:
    # Qt Shader Baker cannot compile GLSL ES 3.0 sources to SPIR-V without
    # raising the version to 3.10+, which our runtime deliberately avoids to
    # preserve compatibility with OpenGL ES 3.0 contexts. Skip those variants
    # during CI validation for now.
    if shader.variant.endswith("es"):
        return

    output_path, log_path = _shader_reports_paths(reports_dir, shader, shader_root)

    command = [*qsb_command, *QSB_PROFILE_ARGUMENTS]

    temp_output: Path | None = None
    target_output: Path | None = output_path
    if target_output is None:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".qsb")
        temp_output = Path(temp_file.name)
        temp_file.close()
        target_output = temp_output

    if target_output is not None:
        command.extend(["-o", str(target_output)])

    command.append(str(shader.path))

    completed = subprocess.run(command, capture_output=True, text=True)

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    if completed.returncode != 0:
        env_message = _interpret_qsb_startup_failure(
            completed.returncode,
            stderr,
            stdout,
            allow_generic=False,
        )
        if env_message is not None:
            raise ShaderValidationEnvironmentError(env_message)
    if log_path is not None:
        log_contents = ["$ " + " ".join(shlex.quote(arg) for arg in command)]
        if stdout:
            log_contents.append("[stdout]\n" + stdout)
        if stderr:
            log_contents.append("[stderr]\n" + stderr)
        log_path.write_text("\n\n".join(log_contents), encoding="utf-8")

    missing_library = _extract_missing_shared_library(stderr)
    if completed.returncode == 127 and missing_library:
        raise ShaderValidationUnavailableError(
            "Qt Shader Baker could not start because the shared library "
            f"'{missing_library}' is not available in the current environment."
        )

    if completed.returncode != 0:
        env_message = _summarize_environment_failure(
            completed.returncode, stdout, stderr, command
        )
        if env_message is not None:
            raise QsbEnvironmentError(env_message)

        errors.append(
            f"{_relative(shader.path, shader_root)}: qsb failed with exit code {completed.returncode}"
        )
        if stderr:
            first_line = stderr.strip().splitlines()[0]
            errors.append(f"    {first_line}")
            errors.extend(_diagnose_qsb_failure(stderr))

    if temp_output is not None:
        with suppress(FileNotFoundError):
            temp_output.unlink()


def validate_shaders(
    shader_root: Path,
    *,
    qsb_command: Sequence[str] | None = None,
    reports_dir: Path | None = None,
) -> ValidationErrors:
    """Return a list of validation error messages for *shader_root*.

    Raises
    ------
    ShaderValidationUnavailableError
        If ``qsb`` is present but cannot be executed due to a missing
        shared library at runtime (for example ``libxkbcommon.so.0``).
    """

    errors: ValidationErrors = []

    if not shader_root.exists():
        return [f"Shader directory does not exist: {shader_root}"]

    try:
        command = (
            list(qsb_command) if qsb_command is not None else _resolve_qsb_command()
        )
    except (FileNotFoundError, RuntimeError) as exc:
        return [str(exc)]

    _probe_qsb(command)

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
            try:
                _run_qsb(shader, shader_root, command, reports_dir, errors)
            except QsbEnvironmentError as exc:
                return [str(exc)]

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
        default=None,
        help=(
            "Directory to store qsb compilation artefacts/logs. "
            "If omitted, validation runs without writing .qsb outputs."
        ),
    )
    parser.add_argument(
        "--emit-qsb",
        action="store_true",
        help=(
            "Write compiled .qsb files to the default reports directory "
            "(reports/shaders) unless --reports-dir overrides it."
        ),
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
    if reports_dir is None and args.emit_qsb:
        reports_dir = DEFAULT_REPORTS_ROOT
    try:
        errors = validate_shaders(shader_root, reports_dir=reports_dir)
    except ShaderValidationUnavailableError as exc:
        print(f"[validate_shaders] WARNING: {exc}", file=sys.stderr)
        return 0

    if errors:
        for message in errors:
            print(f"[validate_shaders] ERROR: {message}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Shader validation OK: {_relative(shader_root, PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
