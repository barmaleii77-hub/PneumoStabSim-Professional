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
import platform
import shutil
from pathlib import Path
from typing import Callable, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QT_VERSION = "6.10.0"
DEFAULT_MODULES = ("qtbase", "qtdeclarative", "qtshadertools", "qtquick3d")
DEFAULT_OUTPUT_DIR = REPO_ROOT / "Qt"
DEFAULT_ARCHIVES_DIR = REPO_ROOT / ".qt" / "archives"


def _ensure_aqt() -> Callable[[Sequence[str]], int | None]:
    """Return the aqt CLI entrypoint, raising if it is missing."""

    spec = importlib.util.find_spec("aqt")
    if spec is None:  # pragma: no cover - executed only on missing dependency
        raise SystemExit(
            "aqtinstall is required. Install it via 'uv pip install aqtinstall' "
            "inside the repository environment."
        )
    from aqt.main import main as aqt_main

    return aqt_main


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
        "--archives",
        str(archives_dir),
    ]
    if prune_archives:
        args.append("--noarchives")
    if modules:
        args.extend(["--modules", ",".join(sorted(set(modules)))])
    if base_url:
        args.extend(["--baseurl", base_url])
    return args


def _remove_existing_installation(install_dir: Path) -> None:
    if install_dir.exists():
        shutil.rmtree(install_dir)


def _default_install_root(output_dir: Path, version: str, arch: str) -> Path:
    return output_dir / version / arch


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision Qt SDK using aqtinstall")
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

    args = parser.parse_args()

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
    if install_dir.exists() and not args.force:
        print(
            f"Qt {args.qt_version} ({arch}) already present at {install_dir}. Use --force to reinstall."
        )
        if args.checksum_manifest:
            _verify_archives(archives_dir, args.checksum_manifest)
        return
    if args.force and install_dir.exists():
        if not install_dir.is_relative_to(output_dir):  # type: ignore[attr-defined]
            raise SystemExit(
                f"Refusing to remove install directory outside {output_dir}"
            )
        _remove_existing_installation(install_dir)

    aqt_args = _build_aqt_arguments(
        host=host,
        target=args.target,
        arch=arch,
        version=args.qt_version,
        modules=modules,
        output_dir=output_dir,
        archives_dir=archives_dir,
        base_url=args.base_url,
        prune_archives=args.prune_archives,
    )

    print("Executing aqtinstall with arguments:\n  python -m aqt " + " ".join(aqt_args))
    if args.dry_run:
        return

    aqt_main = _ensure_aqt()
    exit_code = aqt_main(aqt_args)
    if exit_code not in (None, 0):
        raise SystemExit(exit_code)

    if args.checksum_manifest:
        _verify_archives(archives_dir, args.checksum_manifest)
    print(f"Qt {args.qt_version} installation completed at {install_dir}")


if __name__ == "__main__":
    main()
