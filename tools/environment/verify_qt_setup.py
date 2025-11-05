"""Qt toolchain smoke-check helper.

This module verifies that the PneumoStabSim Professional development
environment exposes the expected Qt runtime bits required for Qt Quick 3D
scenes.  The script is intentionally lightweight so it can run on headless CI
agents once Qt has been provisioned via :mod:`tools.setup_qt`.

Example usage::

    python -m tools.environment.verify_qt_setup
    python -m tools.environment.verify_qt_setup --expected-version 6.10

The command exits with ``0`` when every probe succeeds and ``1`` if any check
fails.
"""

from __future__ import annotations

import argparse
import ctypes
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

STRICT_ENV_VAR = "QT_ENV_CHECK_STRICT"
DEFAULT_OPENGL_HINT = (
    "Install the system OpenGL runtime (e.g. 'apt-get install -y libgl1')."
)

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from src.bootstrap.dependency_config import (
        DependencyConfigError,
        DependencyVariant,
        resolve_dependency_variant,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback when dependencies missing

    @dataclass(frozen=True)
    class DependencyVariant:  # type: ignore[override]
        """Minimal fallback variant when dependency metadata is unavailable."""

        human_name: str
        library_name: str
        install_hint: str | None = None

    class DependencyConfigError(RuntimeError):
        """Raised when dependency metadata cannot be resolved."""

    def resolve_dependency_variant(
        name: str, *, platform_key: str | None = None
    ) -> DependencyVariant:
        if name != "opengl_runtime":
            raise DependencyConfigError(
                f"Fallback resolver cannot satisfy dependency '{name}'."
            )
        return DependencyVariant(
            human_name="libGL.so.1",
            library_name="GL",
            install_hint=DEFAULT_OPENGL_HINT,
        )


@dataclass
class ProbeResult:
    """Container describing the outcome of a probe."""

    ok: bool
    message: str
    fatal: bool = True


class QtRuntimeUnavailableError(ProbeError):
    """Raised when the Qt runtime cannot be initialised due to missing deps."""

    def __init__(self, message: str, *, fatal: bool = False) -> None:
        super().__init__(message)
        self.fatal = fatal


def _dependency_hint(library: str) -> str:
    hint = RUNTIME_DEPENDENCY_HINTS.get(library)
    if hint:
        return hint
    return (
        "Install the missing Qt runtime library via your package manager or run "
        "'make install-qt-runtime'."
    )


def _extract_missing_dependency(message: str) -> str | None:
    for library in RUNTIME_DEPENDENCY_HINTS:
        if library in message:
            return library
    return None


def _format_dependency_message(library: str) -> str:
    hint = _dependency_hint(library)
    return (
        f"Qt runtime dependency '{library}' is not available in the current environment. "
        f"{hint} You can also run 'make install-qt-runtime'."
    )


def _classify_runtime_error(exc: Exception) -> tuple[str, bool]:
    message = str(exc)
    library = _extract_missing_dependency(message)
    if library:
        return _format_dependency_message(library), False
    return (f"Qt runtime initialisation failed: {message}", True)


class MissingSystemLibraryError(ProbeError):
    """Raised when a required system library for PySide6 cannot be loaded."""

    def __init__(self, library_name: str, install_hint: str) -> None:
        message = (
            "PySide6 cannot load required system library "
            f"'{library_name}'. {install_hint}"
        )
        super().__init__(message)
        self.library_name = library_name
        self.install_hint = install_hint


def _strict_checks_enabled() -> bool:
    raw = os.environ.get(STRICT_ENV_VAR, "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _split_path_entries(raw: str | None) -> list[Path]:
    if not raw:
        return []
    return [Path(entry).expanduser() for entry in raw.split(os.pathsep) if entry]


def _build_library_candidates(variant: DependencyVariant) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()

    def _push(name: str | None) -> None:
        if not name:
            return
        if name not in seen:
            seen.add(name)
            candidates.append(name)

    _push(getattr(variant, "human_name", None))
    library_name = getattr(variant, "library_name", None)
    _push(library_name)
    if library_name and not library_name.startswith("lib"):
        _push(f"lib{library_name}.so.1")

    return candidates or ["libGL.so.1"]


def _resolve_opengl_dependency() -> tuple[list[str], str]:
    try:
        variant = resolve_dependency_variant("opengl_runtime")
    except DependencyConfigError:
        return ["libGL.so.1"], DEFAULT_OPENGL_HINT

    candidates = _build_library_candidates(variant)
    hint = variant.install_hint or DEFAULT_OPENGL_HINT
    return candidates, hint


def _identify_missing_system_library(exc: ImportError) -> tuple[str, str] | None:
    message = str(exc)
    candidates, install_hint = _resolve_opengl_dependency()
    for candidate in candidates:
        if candidate in message:
            return candidate, install_hint
    return None


def _handle_missing_system_library(
    results: list[ProbeResult],
    exc: MissingSystemLibraryError,
    expected_version: str,
    expected_platform: str | None,
    report_dir: Path | None,
) -> int:
    strict = _strict_checks_enabled()
    results.append(ProbeResult(not strict, str(exc)))
    if strict:
        results.append(
            ProbeResult(
                False,
                (
                    "Strict Qt environment verification requested via "
                    f"{STRICT_ENV_VAR}; missing system libraries are fatal."
                ),
            )
        )
    else:
        results.append(
            ProbeResult(
                True,
                "Skipping Qt runtime probes because required system "
                "libraries are unavailable.",
            )
        )

    successes, failures = _format_results(results)
    exit_code = 1 if (strict or failures) else 0

    if report_dir is not None:
        try:
            report_path = _write_report(
                report_dir,
                expected_version,
                expected_platform,
                successes,
                failures,
                exit_code,
            )
        except OSError as report_exc:
            failures.append(f"[FAIL] Unable to write environment report: {report_exc}")
            exit_code = 1
        else:
            successes.append(f"[OK] Environment report saved to {report_path}.")

    for line in successes + failures:
        print(line)

    return exit_code


def _check_pyside_version(expected_prefix: str) -> str:
    try:
        from PySide6 import __version__ as pyside_version  # type: ignore[attr-defined]
    except ImportError as exc:  # pragma: no cover - defensive path
        missing = _identify_missing_system_library(exc)
        if missing is not None:
            library_name, install_hint = missing
            raise MissingSystemLibraryError(library_name, install_hint) from exc
        raise ProbeError("PySide6 is not installed. Run 'make uv-sync' first.") from exc

    if expected_prefix and not pyside_version.startswith(expected_prefix):
        raise ProbeError(
            "PySide6 version mismatch: "
            f"expected prefix {expected_prefix}, got {pyside_version}"
        )

    return pyside_version


def _check_environment_paths(var_name: str) -> None:
    entries = _split_path_entries(os.environ.get(var_name))
    if not entries:
        raise ProbeError(
            f"Environment variable {var_name} is not defined or empty. "
            "Ensure you activated the Qt-aware shell (activate_environment.*)."
        )

    missing = [str(path) for path in entries if not path.exists()]
    if missing:
        raise ProbeError(
            f"Environment variable {var_name} references missing directories: "
            + ", ".join(missing)
        )


def _check_qlibraryinfo() -> Path:
    try:
        from PySide6.QtCore import QLibraryInfo
    except ImportError as exc:  # pragma: no cover - defensive path
        raise ProbeError(
            "Unable to import PySide6.QtCore. Is PySide6 installed?"
        ) from exc

    plugins_dir = Path(
        QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)  # type: ignore[attr-defined]
    )
    if not plugins_dir.exists():
        raise ProbeError(
            f"QLibraryInfo reports a non-existent Qt plugins directory: {plugins_dir}"
        )
    return plugins_dir


def _probe_qt_runtime(expected_platform: str | None = None) -> str:
    try:
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtQml import QQmlEngine
        from PySide6.QtQuick3D import QQuick3DGeometry
    except ImportError as exc:  # pragma: no cover - defensive path
        missing = _identify_missing_system_library(exc)
        if missing is not None:
            library_name, install_hint = missing
            raise MissingSystemLibraryError(library_name, install_hint) from exc
        raise ProbeError(
            "Unable to import PySide6 Qt modules required for runtime verification."
        ) from exc

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    try:
        app = QGuiApplication([])
    except Exception as exc:  # pragma: no cover - defensive
        message, fatal = _classify_runtime_error(exc)
        raise QtRuntimeUnavailableError(message, fatal=fatal) from exc
    try:
        platform_name = QGuiApplication.platformName()
        if not platform_name:
            raise ProbeError("Qt did not report an active platform plugin.")
        if expected_platform and platform_name != expected_platform:
            raise ProbeError(
                "Unexpected Qt platform plugin: "
                f"expected {expected_platform}, got {platform_name}"
            )

        try:
            engine = QQmlEngine()
        except Exception as exc:  # pragma: no cover - defensive
            message, fatal = _classify_runtime_error(exc)
            raise QtRuntimeUnavailableError(message, fatal=fatal) from exc
        try:
            if not engine.importPathList():
                raise ProbeError("QQmlEngine.importPathList() returned no entries.")
        finally:
            engine.deleteLater()

        try:
            geometry = QQuick3DGeometry()
        except Exception as exc:  # pragma: no cover - defensive
            message, fatal = _classify_runtime_error(exc)
            raise QtRuntimeUnavailableError(message, fatal=fatal) from exc
        geometry.deleteLater()

        return platform_name
    finally:
        app.quit()


def _check_opengl_runtime() -> ProbeResult:
    if not sys.platform.startswith("linux"):
        return ProbeResult(
            True, f"OpenGL runtime check skipped on platform {sys.platform}."
        )

    candidates, install_hint = _resolve_opengl_dependency()
    strict = _strict_checks_enabled()

    for candidate in candidates:
        try:
            ctypes.CDLL(candidate)
        except OSError:
            continue
        else:
            return ProbeResult(True, f"OpenGL runtime '{candidate}' is loadable.")

    message = (
        "OpenGL runtime libraries are missing: "
        + ", ".join(candidates)
        + f". {install_hint}"
    )

    if strict:
        return ProbeResult(False, message)

    return ProbeResult(
        True,
        message + " Skipping OpenGL probe because QT_ENV_CHECK_STRICT is not enabled.",
    )


def _format_results(
    results: Iterable[ProbeResult],
) -> tuple[list[str], list[str], list[str]]:
    successes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    for result in results:
        if result.ok:
            successes.append(f"[OK] {result.message}")
            continue

        if result.fatal:
            failures.append(f"[FAIL] {result.message}")
        else:
            warnings.append(f"[WARN] {result.message}")

    return successes, warnings, failures


def _write_report(
    report_dir: Path,
    expected_version: str,
    expected_platform: str | None,
    successes: Sequence[str],
    warnings: Sequence[str],
    failures: Sequence[str],
    exit_code: int,
) -> Path:
    timestamp = datetime.now(timezone.utc)
    report_dir.mkdir(parents=True, exist_ok=True)

    header = [
        "# Qt environment verification report",
        f"Timestamp (UTC): {timestamp.isoformat()}",
        f"Expected PySide6 prefix: {expected_version}",
        f"Expected platform plugin: {expected_platform or 'auto-detect'}",
        f"Result: {'success' if exit_code == 0 else 'failure'}",
        "",
        "## Probe summary",
    ]
    body = list(successes) + list(warnings) + list(failures)
    contents = "\n".join(header + body) + "\n"

    unique_name = timestamp.strftime("qt_environment_%Y%m%dT%H%M%SZ.log")
    report_path = report_dir / unique_name
    report_path.write_text(contents, encoding="utf-8")

    latest_path = report_dir / "qt_environment_latest.log"
    latest_path.write_text(contents, encoding="utf-8")

    return report_path


def run_smoke_check(
    expected_version: str,
    expected_platform: str | None,
    report_dir: Path | None = None,
) -> int:
    results: list[ProbeResult] = []

    runtime_ready = True

    try:
        version = _check_pyside_version(expected_version)
    except MissingSystemLibraryError as exc:
        return _handle_missing_system_library(
            results, exc, expected_version, expected_platform, report_dir
        )
    except ProbeError as exc:
        results.append(ProbeResult(False, str(exc)))
        runtime_ready = False
    else:
        results.append(
            ProbeResult(
                True,
                f"PySide6 {version} detected (expected prefix {expected_version}).",
            )
        )

    if runtime_ready:
        try:
            platform_name = _probe_qt_runtime(expected_platform)
        except QtRuntimeUnavailableError as exc:
            results.append(ProbeResult(False, str(exc), fatal=exc.fatal))
            runtime_ready = False
        except ProbeError as exc:
            results.append(ProbeResult(False, str(exc)))
            runtime_ready = False
        else:
            results.append(
                ProbeResult(True, f"Qt platform plugin '{platform_name}' initialised.")
            )

    if runtime_ready:
        for var_name in ("QT_PLUGIN_PATH", "QML2_IMPORT_PATH"):
            try:
                _check_environment_paths(var_name)
            except ProbeError as exc:
                results.append(ProbeResult(False, str(exc)))
            else:
                results.append(
                    ProbeResult(True, f"{var_name} directories are present.")
                )

        try:
            plugins_dir = _check_qlibraryinfo()
        except ProbeError as exc:
            results.append(ProbeResult(False, str(exc)))
        else:
            results.append(
                ProbeResult(
                    True, f"QLibraryInfo reports plugin directory at {plugins_dir}."
                )
            )

    try:
        platform_name = _probe_qt_runtime(expected_platform)
    except MissingSystemLibraryError as exc:
        return _handle_missing_system_library(
            results, exc, expected_version, expected_platform, report_dir
        )
    except ProbeError as exc:
        results.append(ProbeResult(False, str(exc)))
    else:
        results.append(
            ProbeResult(
                False,
                "Skipping remaining Qt environment probes because prerequisite checks failed.",
                fatal=False,
            )
        )

    successes, warnings, failures = _format_results(results)
    exit_code = 0 if not failures else 1

    if report_dir is not None:
        try:
            report_path = _write_report(
                report_dir,
                expected_version,
                expected_platform,
                successes,
                warnings,
                failures,
                exit_code,
            )
        except OSError as exc:
            failures.append(f"[FAIL] Unable to write environment report: {exc}")
            exit_code = 1
        else:
            successes.append(f"[OK] Environment report saved to {report_path}.")

    for line in successes + warnings + failures:
        print(line)

    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify Qt Quick 3D runtime availability for PneumoStabSim"
    )
    parser.add_argument(
        "--expected-version",
        default="6.10",
        help="Expected PySide6 version prefix (default: 6.10)",
    )
    parser.add_argument(
        "--expected-platform",
        default=None,
        help="Optional Qt platform plugin name (e.g. offscreen)",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports/environment"),
        help="Directory where the verification report should be written.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    exit_code = run_smoke_check(
        args.expected_version, args.expected_platform, args.report_dir
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
