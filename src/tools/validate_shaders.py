"""Validate shader variant coverage and GLSL profiles.

This script enforces the Phase 3 requirement that each desktop shader provides
an OpenGL fallback and an OpenGL ES variant with the expected ``#version``
annotations.  It is lightweight enough for CI usage and exports helper
functions that unit tests can import.
"""

from __future__ import annotations

import argparse
import codecs
import locale
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SHADER_ROOT = PROJECT_ROOT / "assets" / "shaders"
DEFAULT_REPORTS_ROOT = PROJECT_ROOT / "reports" / "shaders"
SUPPORTED_SUFFIXES = {".frag", ".vert"}

BOM_SEQUENCES: tuple[tuple[str, bytes], ...] = (
    ("UTF-8", codecs.BOM_UTF8),
    ("UTF-16 LE", codecs.BOM_UTF16_LE),
    ("UTF-16 BE", codecs.BOM_UTF16_BE),
    ("UTF-32 LE", codecs.BOM_UTF32_LE),
    ("UTF-32 BE", codecs.BOM_UTF32_BE),
)

LEADING_WHITESPACE_BYTES = {b" ", b"\t", b"\r", b"\n"}

VARIANT_SUFFIXES: tuple[tuple[str, str], ...] = (
    ("_fallback_es", "fallback_es"),
    ("_fallback", "fallback"),
    ("_es", "es"),
)

DEPRECATED_ENTRY_POINTS: tuple[tuple[str, str], ...] = (
    (
        "qt_customMain",
        "deprecated entry point 'qt_customMain'; replace with 'main' for Qt 6.10 compatibility",
    ),
)

EXPECTED_VERSIONS: Mapping[tuple[str, str], str] = {
    ("desktop", ".frag"): "#version 450 core",
    ("desktop", ".vert"): "#version 450 core",
    ("es", ".frag"): "#version 300 es",
    ("es", ".vert"): "#version 300 es",
    ("fallback", ".frag"): "#version 450 core",
    ("fallback_es", ".frag"): "#version 300 es",
}

# Identifier usage that is no longer supported by Qt 6.10+ shader pipelines.
# The key stores the forbidden token, the value provides a short remediation
# hint that surfaces in validation error messages.
FORBIDDEN_IDENTIFIER_GUIDANCE: Mapping[str, str] = {
    "qt_customMain": "replace with 'main()' to satisfy Qt 6.10 entry point requirements",
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


ValidationErrors = list[str]


@dataclass(slots=True)
class ShaderValidationReport:
    """Container describing the outcome of shader validation."""

    errors: list[str]
    warnings: list[str]


QSB_ENV_VARIABLE = "QSB_COMMAND"


class ShaderValidationUnavailableError(RuntimeError):
    """Raised when qsb cannot run due to a missing runtime dependency."""


class QsbEnvironmentError(RuntimeError):
    """Raised when qsb fails because the Qt runtime is misconfigured."""


class ShaderValidationEnvironmentError(QsbEnvironmentError):
    """Raised when the environment prevents qsb from even starting."""


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


def _detect_leading_bom_or_whitespace(path: Path) -> str | None:
    """Return a descriptive error when the file does not immediately start with ``#``."""

    data = path.read_bytes()
    for label, marker in BOM_SEQUENCES:
        if marker and data.startswith(marker):
            return (
                "leading "
                f"{label} byte-order mark; remove it so '#version' is the first bytes"
            )

    if not data:
        return None

    first_byte = data[:1]
    if first_byte in LEADING_WHITESPACE_BYTES:
        return "leading whitespace before '#version' directive"

    if first_byte == b"#":
        return None

    leading_line = data.splitlines()[0][:32]
    preview = leading_line.decode("utf-8", errors="replace")
    return f"unexpected content before '#version' directive (starts with {preview!r})"


def _detect_deprecated_entry_point(path: Path) -> str | None:
    """Return an error message when the shader uses a removed entry point."""

    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return f"unable to read file with UTF-8 encoding: {exc}"

    for symbol, message in DEPRECATED_ENTRY_POINTS:
        if symbol in source:
            return message
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
        rel = path.relative_to(root)
        return rel.as_posix()
    except ValueError:
        # Путь за пределами корня — возвращаем POSIX-представление абсолютного пути
        return Path(str(path)).as_posix()


def _validate_versions(
    files: Iterable[ShaderFile], root: Path, errors: ValidationErrors
) -> None:
    for shader in files:
        leading_issue = _detect_leading_bom_or_whitespace(shader.path)
        if leading_issue is not None:
            errors.append(f"{_relative(shader.path, root)}: {leading_issue}")
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

        deprecated_entry = _detect_deprecated_entry_point(shader.path)
        if deprecated_entry is not None:
            errors.append(f"{_relative(shader.path, root)}: {deprecated_entry}")


def _check_forbidden_identifiers(
    files: Iterable[ShaderFile], root: Path, errors: ValidationErrors
) -> None:
    """Ensure shaders avoid legacy entry points rejected by Qt 6.10."""

    for shader in files:
        try:
            contents = shader.path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(
                f"{_relative(shader.path, root)}: failed to read source: {exc}"
            )
            continue

        for identifier, guidance in FORBIDDEN_IDENTIFIER_GUIDANCE.items():
            if identifier in contents:
                errors.append(
                    f"{_relative(shader.path, root)}: forbidden identifier '{identifier}' detected; {guidance}"
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

    if (
        "failed to create opengl context" in combined
        or "could not initialize opengl" in combined
    ):
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


def _extract_shader_warnings(stdout: str, stderr: str) -> list[str]:
    """Return warning lines emitted by qsb during compilation."""

    warnings: list[str] = []
    for stream in (stdout, stderr):
        for raw_line in (stream or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if "warning" not in line.lower():
                continue
            if line not in warnings:
                warnings.append(line)
    return warnings


def _interpret_qsb_startup_failure(
    return_code: int,
    stderr: str,
    stdout: str,
    *,
    allow_generic: bool,
) -> str | None:
    """Return an explanatory message when qsb cannot start."""

    if return_code == 0:
        return None

    summary = _summarize_environment_failure(return_code, stdout, stderr, ())
    if summary is not None:
        return summary

    if not allow_generic:
        return None

    stripped_stdout = stdout.strip()
    stripped_stderr = stderr.strip()
    combined_lines = [line for line in (stripped_stdout, stripped_stderr) if line]
    if combined_lines:
        combined = "\n".join(combined_lines)
        return (
            "Qt Shader Baker failed to start. "
            f"Exit code {return_code}. Output:\n{combined}"
        )

    if return_code == 127:
        return (
            "Qt Shader Baker could not start (exit code 127). "
            "Ensure Qt Shader Tools is installed and available in PATH."
        )

    return f"Qt Shader Baker failed to start with exit code {return_code}."


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

    if (
        "failed to create opengl context" in lower
        or "could not initialize opengl" in lower
    ):
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


def _probe_qsb(command: Sequence[str]) -> None:
    """Ensure that the qsb command is executable in the current environment."""

    try:
        completed = subprocess.run(
            [*command, "--version"], capture_output=True, text=True
        )
    except OSError as exc:  # pragma: no cover - defensive guard
        raise ShaderValidationUnavailableError(
            f"Failed to execute Qt Shader Baker: {exc}"
        ) from exc

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""

    if completed.returncode == 0:
        return

    missing_library = _extract_missing_shared_library(stderr)
    if completed.returncode == 127 and missing_library:
        raise ShaderValidationUnavailableError(
            "Qt Shader Baker could not start because the shared library "
            f"'{missing_library}' is not available in the current environment."
        )

    message = _interpret_qsb_startup_failure(
        completed.returncode,
        stderr,
        stdout,
        allow_generic=True,
    )
    if message is not None:
        raise ShaderValidationEnvironmentError(message)


def _wrap_python_qsb_if_needed(command: Sequence[str]) -> list[str]:
    """On Windows with non-ASCII temp paths, test qsb stubs may be written using
    the current ANSI code page, causing Python to fail decoding the source as UTF-8.

    To make execution robust, detect `python.exe <script.py>` commands and, if the
    target script contains non-ASCII bytes and lacks an encoding cookie, generate a
    temporary wrapper that prepends an explicit coding header matching the preferred
    system encoding. The original bytes are preserved, so string literals remain valid.
    """
    cmd = list(command)
    if len(cmd) < 2:
        return cmd
    exe_name = Path(cmd[0]).name.lower()
    if "python" not in exe_name:
        return cmd
    script_path = Path(cmd[1])
    if script_path.suffix.lower() != ".py":
        return cmd
    try:
        data = script_path.read_bytes()
    except OSError:
        return cmd

    # Fast path: ASCII-only source is safe with any decoder
    if all(b < 0x80 for b in data):
        return cmd

    # If file already declares encoding, keep original
    head = data.splitlines()[:2]
    if any(line.strip().startswith(b"# -*- coding:") or line.strip().startswith(b"# coding=") for line in head):
        return cmd

    enc = locale.getpreferredencoding(False) or "cp1252"
    header = f"# -*- coding: {enc} -*-\n".encode("ascii")
    wrapper_bytes = header + data
    try:
        wrapper_path = script_path.with_name(script_path.stem + "_enc.py")
        wrapper_path.write_bytes(wrapper_bytes)
        cmd[1] = str(wrapper_path)
    except OSError:
        # Fall back to original command if we cannot write wrapper
        return list(command)
    return cmd


def _run_qsb(
    shader: ShaderFile,
    shader_root: Path,
    qsb_command: Sequence[str],
    reports_dir: Path | None,
    errors: ValidationErrors,
    warnings: list[str],
) -> None:
    # Qt Shader Baker cannot compile GLSL ES 3.0 sources to SPIR-V without
    # raising the version to 3.10+, which our runtime deliberately avoids to
    # preserve compatibility with OpenGL ES 3.0 contexts. Skip those variants
    # during CI validation for now.
    if shader.variant.endswith("es"):
        return

    output_path, log_path = _shader_reports_paths(reports_dir, shader, shader_root)

    # Wrap python-based qsb stubs to ensure source encoding is declared explicitly
    qsb_command = _wrap_python_qsb_if_needed(qsb_command)

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

    if log_path is not None:
        log_contents = ["$ " + shlex.join(command)]
        if stdout:
            log_contents.append("[stdout]\n" + stdout)
        if stderr:
            log_contents.append("[stderr]\n" + stderr)
        log_path.write_text("\n\n".join(log_contents), encoding="utf-8")

    if completed.returncode == 0:
        for warning in _extract_shader_warnings(stdout, stderr):
            warnings.append(
                f"{_relative(shader.path, shader_root)}: shader warning: {warning}"
            )

    if completed.returncode != 0:
        missing_library = _extract_missing_shared_library(stderr)
        if completed.returncode == 127 and missing_library:
            raise ShaderValidationUnavailableError(
                "Qt Shader Baker could not start because the shared library "
                f"'{missing_library}' is not available in the current environment."
            )

        env_message = _interpret_qsb_startup_failure(
            completed.returncode,
            stderr,
            stdout,
            allow_generic=False,
        )
        if env_message is not None:
            raise ShaderValidationEnvironmentError(env_message)

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
) -> ShaderValidationReport:
    """Validate *shader_root* and return a :class:`ShaderValidationReport`.

    Raises
    ------
    ShaderValidationUnavailableError
        If ``qsb`` is present but cannot be executed due to a missing
        shared library at runtime (for example ``libxkbcommon.so.0``).
    """

    errors: ValidationErrors = []
    warnings: list[str] = []

    if not shader_root.exists():
        return ShaderValidationReport(
            errors=[f"Shader directory does not exist: {shader_root}"],
            warnings=warnings,
        )

    try:
        command = (
            list(qsb_command) if qsb_command is not None else _resolve_qsb_command()
        )
    except (FileNotFoundError, RuntimeError) as exc:
        return ShaderValidationReport(errors=[str(exc)], warnings=warnings)

    # Ensure python-based stubs are robust to non-ASCII paths during probe
    command = _wrap_python_qsb_if_needed(command)

    try:
        _probe_qsb(command)
    except ShaderValidationUnavailableError:
        raise
    except QsbEnvironmentError as exc:
        return ShaderValidationReport(errors=[str(exc)], warnings=warnings)

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
        _check_forbidden_identifiers(files, shader_root, errors)

        for shader in files:
            try:
                _run_qsb(shader, shader_root, command, reports_dir, errors, warnings)
            except QsbEnvironmentError as exc:
                return ShaderValidationReport(errors=[str(exc)], warnings=warnings)

    return ShaderValidationReport(errors=errors, warnings=warnings)


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
        result = validate_shaders(shader_root, reports_dir=reports_dir)
    except ShaderValidationUnavailableError as exc:
        print(f"[validate_shaders] WARNING: {exc}", file=sys.stderr)
        return 0

    if result.errors:
        for message in result.errors:
            print(f"[validate_shaders] ERROR: {message}", file=sys.stderr)
        return 1

    for warning in result.warnings:
        print(f"[validate_shaders] WARNING: {warning}", file=sys.stderr)

    if not args.quiet:
        var_summary = ""
        if result.warnings:
            var_summary = f" (warnings: {len(result.warnings)})"
        print(
            f"Shader validation OK{var_summary}: {_relative(shader_root, PROJECT_ROOT)}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
