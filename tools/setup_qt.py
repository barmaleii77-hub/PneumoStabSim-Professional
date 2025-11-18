"""Provision the Qt SDK using the aqtinstall toolkit.

The script wraps ``python -m aqt`` with sensible defaults tailored for the
renovation master plan: downloads are cached under ``.qt/archives`` and the
installed toolchain lands in ``Qt/<version>/<arch>`` relative to the repository
root. Developers and CI agents can override the defaults via CLI options while
still benefiting from checksum verification hooks.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from collections.abc import Callable
from collections.abc import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QT_VERSION = "6.10.0"
MINIMUM_QT_VERSION = (6, 10, 0)
DEFAULT_MODULES = ("qtquick3d", "qtshadertools", "qtimageformats")
DEFAULT_OUTPUT_DIR = REPO_ROOT / "Qt"
DEFAULT_ARCHIVES_DIR = REPO_ROOT / ".qt" / "archives"
DEFAULT_ENV_FILE = REPO_ROOT / ".qt" / "qt.env"


def _unique_path_entries(entries: Iterable[str]) -> str:
    """Return a deduplicated path list joined with ``os.pathsep``."""

    segments: list[str] = []
    for entry in entries:
        for candidate in entry.split(os.pathsep):
            if candidate and candidate not in segments:
                segments.append(candidate)
    return os.pathsep.join(segments)


def _gather_qt_environment(project_root: Path) -> dict[str, str]:
    """Build cross-platform Qt environment values from the active PySide6."""

    from PySide6.QtCore import QLibraryInfo

    qml_import_dir = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
    plugins_dir = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
    qml_roots = [project_root / "assets" / "qml"]
    qml_roots.extend(
        path
        for path in (
            project_root / "assets" / "qml" / "components",
            project_root / "assets" / "qml" / "scene",
        )
    )
    qml_paths = [qml_import_dir, *(str(path) for path in qml_roots if path.exists())]
    merged_qml_paths = _unique_path_entries(qml_paths)

    return {
        "QT_PLUGIN_PATH": plugins_dir,
        "QML2_IMPORT_PATH": merged_qml_paths,
        "QML_IMPORT_PATH": merged_qml_paths,
        "QT_QML_IMPORT_PATH": merged_qml_paths,
        "QT_QUICK_CONTROLS_STYLE": "Basic",
    }


def _write_env_file(env_file: Path, values: dict[str, str]) -> None:
    env_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={value}" for key, value in values.items()]
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[setup_qt] Wrote Qt environment exports to {env_file}")


def _apply_qt_environment(values: dict[str, str], env_file: Path | None) -> None:
    system = platform.system()
    print(f"[setup_qt] Detected platform: {system}")
    print("[setup_qt] Applying Qt environment variables:")
    for key, value in values.items():
        os.environ[key] = value
        print(f"  {key}={value}")
    if env_file is not None:
        _write_env_file(env_file, values)


def _ensure_aqt() -> Callable[[Sequence[str]], int | None]:
    """Return the aqt CLI entrypoint, raising if it is missing."""

    spec = importlib.util.find_spec("aqt")
    if spec is None:  # pragma: no cover - executed only on missing dependency
        raise SystemExit(
            "aqtinstall is required. Install it via 'uv pip install aqtinstall' "
            "inside the repository environment."
        )
    main_spec = importlib.util.find_spec("aqt.main")
    if main_spec is not None:
        from aqt.main import main as aqt_main  # type: ignore[import-not-found]

        return aqt_main

    alt_spec = importlib.util.find_spec("aqt.__main__")
    if alt_spec is None:
        raise SystemExit(
            "aqtinstall is present but does not expose a CLI entrypoint. Install "
            "a release that ships either 'aqt.main' or 'aqt.__main__'."
        )

    from aqt.__main__ import main as aqt_entry  # type: ignore[import-not-found]

    def _wrapper(arguments: Sequence[str]) -> int | None:
        import sys

        original_argv = sys.argv[:]  # type: ignore[attr-defined]
        sys.argv = ["aqt", *arguments]
        try:
            result = aqt_entry()
        finally:
            sys.argv = original_argv
        return result

    return _wrapper


def _detect_host(default_arch: str | None = None) -> tuple[str, str]:
    """Infer host platform and Qt architecture."""

    system = platform.system().lower()
    if system == "windows":
        return "windows", default_arch or "win64_msvc2019_64"
    if system == "linux":
        return "linux", default_arch or "gcc_64"
    if system == "darwin":
        return "mac", default_arch or "clang_64"
    raise SystemExit(
        f"Unsupported platform '{system}'. Specify --host-platform and --arch explicitly."
    )


def _parse_modules(raw: Iterable[str]) -> list[str]:
    modules: list[str] = []
    for value in raw:
        for candidate in value.split(","):
            module = candidate.strip()
            if module:
                modules.append(module)
    return modules


def _collect_archives(archives_dir: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    if not archives_dir.exists():
        return files
    for path in archives_dir.rglob("*"):
        if path.is_file():
            files[path.relative_to(archives_dir).as_posix()] = path
    return files


def _parse_semver(version: str) -> tuple[int, int, int]:
    """Return a comparable semantic version tuple from a user-supplied string."""

    digits = [int(token) for token in re.findall(r"\d+", version)]
    while len(digits) < 3:
        digits.append(0)
    return tuple(digits[:3])  # type: ignore[return-value]


def _ensure_minimum_version(version: str) -> None:
    """Raise ``SystemExit`` when *version* is older than the supported baseline."""

    parsed = _parse_semver(version)
    if parsed < MINIMUM_QT_VERSION:
        minimum = ".".join(str(part) for part in MINIMUM_QT_VERSION)
        raise SystemExit(
            "Qt {version} is not supported; PneumoStabSim requires Qt {minimum} or newer.".format(
                version=version, minimum=minimum
            )
        )


def _verify_archives(archives_dir: Path, manifest: Path) -> None:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    archives = _collect_archives(archives_dir)
    missing: list[str] = []
    mismatched: list[str] = []

    for rel_path, expected_hash in data.items():
        candidate = archives.get(rel_path)
        if candidate is None:
            # fall back to lookup by file name only
            for _, path in archives.items():
                if path.name == Path(rel_path).name:
                    candidate = path
                    break
        if candidate is None:
            missing.append(rel_path)
            continue
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if digest.lower() != expected_hash.lower():
            mismatched.append(f"{rel_path} (expected {expected_hash}, got {digest})")

    if missing or mismatched:
        lines: list[str] = ["Qt archive verification failed:"]
        if missing:
            lines.append("  Missing archives:")
            lines.extend(f"    - {item}" for item in missing)
        if mismatched:
            lines.append("  Hash mismatches:")
            lines.extend(f"    - {item}" for item in mismatched)
        raise SystemExit("\n".join(lines))


def _export_requirements_with_uv(project_root: Path) -> None:
    uv_executable = shutil.which("uv")
    if uv_executable is None:
        raise SystemExit(
            "uv executable was not found. Run 'python scripts/bootstrap_uv.py --sync' "
            "before using --refresh-requirements."
        )
    lock_command = [uv_executable, "lock"]
    print(f"Running {' '.join(lock_command)}", flush=True)
    lock_result = subprocess.run(lock_command, cwd=project_root, check=False)
    if lock_result.returncode != 0:
        raise SystemExit(
            f"Command '{' '.join(lock_command)}' failed with exit code {lock_result.returncode}."
        )
    lockfile = project_root / "uv.lock"
    if not lockfile.exists():
        raise SystemExit(
            f"Lockfile '{lockfile}' is required before exporting requirements. Run 'uv lock'."
        )
    commands = [
        [
            "export",
            "--format",
            "requirements.txt",
            "--output-file",
            "requirements.txt",
            "--no-dev",
            "--locked",
            "--no-emit-project",
        ],
        [
            "export",
            "--format",
            "requirements.txt",
            "--output-file",
            "requirements-dev.txt",
            "--extra",
            "dev",
            "--locked",
            "--no-emit-project",
        ],
        [
            "export",
            "--format",
            "requirements.txt",
            "--output-file",
            "requirements-compatible.txt",
            "--no-dev",
            "--locked",
            "--no-emit-project",
            "--no-annotate",
            "--no-hashes",
        ],
    ]
    for command in commands:
        full_command = [uv_executable, *command]
        print(f"Running {' '.join(full_command)}", flush=True)
        result = subprocess.run(full_command, cwd=project_root, check=False)
        if result.returncode != 0:
            raise SystemExit(
                f"Command '{' '.join(full_command)}' failed with exit code {result.returncode}."
            )


def _import_pyside6() -> tuple[str, str]:
    """Return the PySide6 and Qt versions currently importable."""

    import PySide6  # type: ignore
    from PySide6 import QtCore  # type: ignore

    return PySide6.__version__, QtCore.qVersion()


def _check_installation(
    install_dir: Path,
    qt_version: str,
    archives_dir: Path,
    checksum_manifest: Path | None,
    importer: Callable[[], tuple[str, str]] = _import_pyside6,
) -> int:
    """Validate that the Qt SDK and Python bindings are ready for use."""

    print(f"Verifying Qt installation at {install_dir}")
    success = True

    if not install_dir.exists():
        print(
            f"[!] Qt {qt_version} toolchain not found. Expected directory: {install_dir}"
        )
        success = False
    else:
        required = ("bin", "lib", "qml", "plugins")
        missing = [part for part in required if not (install_dir / part).exists()]
        if missing:
            success = False
            for part in missing:
                print(f"[!] Missing required Qt subdirectory: {install_dir / part}")
        else:
            for part in required:
                print(f"[✓] Found Qt component: {install_dir / part}")

    try:
        pyside_version, detected_qt_version = importer()
    except Exception as exc:  # pragma: no cover - requires missing dependency
        print(f"[!] Failed to import PySide6: {exc}")
        success = False
    else:
        print(
            f"[✓] PySide6 {pyside_version} is available (Qt runtime {detected_qt_version})"
        )
        if detected_qt_version != qt_version:
            print(
                "[!] Qt runtime version mismatch: expected {expected}, detected {detected}".format(
                    expected=qt_version, detected=detected_qt_version
                )
            )
            success = False

    if checksum_manifest:
        try:
            _verify_archives(archives_dir, checksum_manifest)
        except SystemExit as exc:
            print(str(exc))
            success = False
        else:
            print(f"[✓] Archive checksums verified using {checksum_manifest}")

    return 0 if success else 1


HOST_REPO_SEGMENTS: dict[str, str] = {
    "linux": "linux_x64",
    "windows": "windows_x86",
    "mac": "mac_x64",
}


def _version_token(version: str) -> str:
    parts = version.split(".")
    while len(parts) < 3:
        parts.append("0")
    return "".join(str(int(part)) for part in parts[:3])


def _default_base_url(host: str, target: str, version: str) -> str | None:
    """Return the canonical mirror URL for the given host/target/version."""

    repo_segment = HOST_REPO_SEGMENTS.get(host)
    if not repo_segment:
        return None
    token = _version_token(version)
    return (
        "https://download.qt.io/online/qtsdkrepository/"
        f"{repo_segment}/{target}/qt6_{token}/qt6_{token}"
    )


def _build_aqt_arguments(
    *,
    host: str,
    target: str,
    arch: str,
    version: str,
    modules: Sequence[str],
    output_dir: Path,
    archives_dir: Path,
    base_url: str | None,
    prune_archives: bool,
) -> list[str]:
    args = [
        "install-qt",
        host,
        target,
        version,
        arch,
        "--outputdir",
        str(output_dir),
    ]
    if not prune_archives:
        args.extend(["--archives", str(archives_dir)])
    if prune_archives:
        args.append("--noarchives")
    if modules:
        args.extend(["--modules", ",".join(sorted(set(modules)))])
    if base_url:
        args.extend(["--base", base_url])
    return args


def _remove_existing_installation(install_dir: Path) -> None:
    if install_dir.exists():
        shutil.rmtree(install_dir)


def _default_install_root(output_dir: Path, version: str, arch: str) -> Path:
    return output_dir / version / arch


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Provision Qt SDK using aqtinstall",
        allow_abbrev=False,
    )
    parser.add_argument("--qt-version", default=DEFAULT_QT_VERSION)
    parser.add_argument("--modules", nargs="*", default=list(DEFAULT_MODULES))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--archives-dir", type=Path, default=DEFAULT_ARCHIVES_DIR)
    parser.add_argument(
        "--host-platform", choices=["windows", "linux", "mac"], default=None
    )
    parser.add_argument("--target", default="desktop")
    parser.add_argument("--arch", default=None)
    parser.add_argument("--base-url", dest="base_url", default=None)
    parser.add_argument("--checksum-manifest", type=Path, default=None)
    parser.add_argument(
        "--force", action="store_true", help="Reinstall even if Qt is already present"
    )
    parser.add_argument(
        "--prune-archives",
        action="store_true",
        help="Delete downloaded archives after installation (default keeps a local cache)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print the aqt command without executing"
    )
    parser.add_argument(
        "--refresh-requirements",
        action="store_true",
        help=(
            "After provisioning Qt, regenerate requirements exports using the uv lockfile. "
            "Useful for release automation."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that the Qt toolchain and PySide6 runtime are available.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=DEFAULT_ENV_FILE,
        help="Optional path to write Qt environment exports in KEY=VALUE format.",
    )
    parser.add_argument(
        "--skip-env-export",
        action="store_true",
        help="Skip writing and applying Qt environment variables (not recommended).",
    )
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Only export environment variables without invoking aqtinstall.",
    )

    args = parser.parse_args()

    _ensure_minimum_version(args.qt_version)

    export_env = not args.skip_env_export

    modules = _parse_modules(args.modules)
    host, default_arch = _detect_host(args.arch)
    if args.host_platform:
        host = args.host_platform
    arch = args.arch or default_arch

    output_dir = args.output_dir
    archives_dir = args.archives_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    archives_dir.mkdir(parents=True, exist_ok=True)

    install_dir = _default_install_root(output_dir, args.qt_version, arch)
    env_exported = False

    def _export_env() -> None:
        nonlocal env_exported
        if env_exported or not export_env:
            return
        env_values = _gather_qt_environment(REPO_ROOT)
        _apply_qt_environment(env_values, args.env_file)
        env_exported = True

    if args.export_only:
        _export_env()
        return
    if args.check:
        status = _check_installation(
            install_dir=install_dir,
            qt_version=args.qt_version,
            archives_dir=archives_dir,
            checksum_manifest=args.checksum_manifest,
        )
        _export_env()
        raise SystemExit(status)
    if install_dir.exists() and not args.force:
        print(
            f"Qt {args.qt_version} ({arch}) already present at {install_dir}. Use --force to reinstall."
        )
        if args.checksum_manifest:
            _verify_archives(archives_dir, args.checksum_manifest)
        if args.refresh_requirements:
            _export_requirements_with_uv(REPO_ROOT)
        _export_env()
        return
    if args.force and install_dir.exists():
        if not install_dir.is_relative_to(output_dir):  # type: ignore[attr-defined]
            raise SystemExit(
                f"Refusing to remove install directory outside {output_dir}"
            )
        _remove_existing_installation(install_dir)

    base_url = args.base_url or _default_base_url(host, args.target, args.qt_version)

    aqt_args = _build_aqt_arguments(
        host=host,
        target=args.target,
        arch=arch,
        version=args.qt_version,
        modules=modules,
        output_dir=output_dir,
        archives_dir=archives_dir,
        base_url=base_url,
        prune_archives=args.prune_archives,
    )

    print("Executing aqtinstall with arguments:\n  python -m aqt " + " ".join(aqt_args))
    if args.dry_run:
        if args.refresh_requirements:
            print("Skipping requirements export because --dry-run was requested.")
        return

    aqt_main = _ensure_aqt()
    exit_code = aqt_main(aqt_args)
    if exit_code not in (None, 0):
        raise SystemExit(exit_code)

    if args.checksum_manifest:
        _verify_archives(archives_dir, args.checksum_manifest)
    if args.refresh_requirements:
        _export_requirements_with_uv(REPO_ROOT)
    _export_env()
    print(f"Qt {args.qt_version} installation completed at {install_dir}")


if __name__ == "__main__":
    main()
