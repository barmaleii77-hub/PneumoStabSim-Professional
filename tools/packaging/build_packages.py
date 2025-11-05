"""Unified packaging entry point for PneumoStabSim Professional releases."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

LOGGER = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIST_DIR = REPO_ROOT / "dist" / "packages"
PLATFORM_ALIASES = {
    "linux": {"linux", "linux2"},
    "windows": {"win32"},
    "macos": {"darwin"},
}
DEFAULT_RESOURCES = ("assets", "config", "docs", "LICENSE")


@dataclass(frozen=True)
class PackageTarget:
    """Configuration describing a single packaging target."""

    name: str
    platform: str
    builder: str
    entry_point: Path
    app_name: str
    archive_format: str = "zip"
    resources: Sequence[str] = field(default_factory=lambda: DEFAULT_RESOURCES)
    extra_args: Sequence[str] = field(default_factory=tuple)

    def supports_host(self) -> bool:
        """Return ``True`` if this target is buildable on the current host."""

        aliases = PLATFORM_ALIASES.get(self.platform, {self.platform})
        return sys.platform in aliases or any(
            sys.platform.startswith(alias) for alias in aliases
        )

    @property
    def output_basename(self) -> str:
        """Base filename used for generated archives."""

        return f"PneumoStabSim-Professional-{self.name}"

    @property
    def build_id(self) -> str:
        """Unique identifier for manifests and logs."""

        return f"{self.builder}:{self.name}"


DEFAULT_TARGETS: tuple[PackageTarget, ...] = (
    PackageTarget(
        name="linux-x86_64",
        platform="linux",
        builder="pyinstaller",
        entry_point=REPO_ROOT / "app.py",
        app_name="PneumoStabSim",
        archive_format="gztar",
        extra_args=("--onedir", "--windowed"),
    ),
    PackageTarget(
        name="windows-x86_64",
        platform="windows",
        builder="pyinstaller",
        entry_point=REPO_ROOT / "app.py",
        app_name="PneumoStabSim",
        archive_format="zip",
        extra_args=("--onedir", "--windowed"),
    ),
    PackageTarget(
        name="macos-universal2",
        platform="macos",
        builder="cx_freeze",
        entry_point=REPO_ROOT / "app.py",
        app_name="PneumoStabSim",
        archive_format="zip",
        extra_args=(),
    ),
)


def _ensure_clean_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _build_with_pyinstaller(target: PackageTarget, output_dir: Path) -> Path:
    """Invoke PyInstaller for the provided target."""

    work_root = output_dir / target.name / "pyinstaller"
    dist_dir = work_root / "dist"
    build_dir = work_root / "build"
    spec_dir = work_root / "spec"
    for directory in (dist_dir, build_dir, spec_dir):
        directory.mkdir(parents=True, exist_ok=True)

    add_data_args: list[str] = []
    for resource in target.resources:
        resource_path = REPO_ROOT / resource
        if not resource_path.exists():
            LOGGER.debug("Resource '%s' does not exist, skipping", resource)
            continue
        destination = resource_path.name
        add_data_args.extend(
            [
                "--add-data",
                f"{resource_path.resolve()}{os.pathsep}{destination}",
            ]
        )

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(target.entry_point),
        "--noconfirm",
        "--clean",
        "--name",
        target.app_name,
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
        "--specpath",
        str(spec_dir),
        "--paths",
        str(REPO_ROOT),
        "--paths",
        str(REPO_ROOT / "src"),
        *target.extra_args,
        *add_data_args,
    ]

    LOGGER.info("Building target %s via PyInstaller", target.build_id)
    LOGGER.debug("Running command: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)

    return dist_dir / target.app_name


def _build_with_cx_freeze(target: PackageTarget, output_dir: Path) -> Path:
    """Invoke cx_Freeze for the provided target."""

    build_root = output_dir / target.name / "cx_freeze"
    target_dir = build_root / "dist"
    target_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "cx_Freeze",
        str(target.entry_point),
        "--target-dir",
        str(target_dir),
        "--target-name",
        target.app_name,
        *target.extra_args,
    ]

    for resource in target.resources:
        resource_path = REPO_ROOT / resource
        if resource_path.exists():
            cmd.extend(
                ["--include-files", f"{resource_path}{os.pathsep}{resource_path.name}"]
            )

    LOGGER.info("Building target %s via cx_Freeze", target.build_id)
    LOGGER.debug("Running command: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)

    return target_dir


def _create_archive(source_dir: Path, target: PackageTarget, output_dir: Path) -> Path:
    bundle_dir = output_dir / target.output_basename
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    for item in source_dir.iterdir():
        destination = bundle_dir / item.name
        if item.is_dir():
            shutil.copytree(item, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(item, destination)

    license_path = REPO_ROOT / "LICENSE"
    if license_path.exists():
        shutil.copy2(license_path, bundle_dir / license_path.name)

    readme_path = REPO_ROOT / "README.md"
    if readme_path.exists():
        shutil.copy2(readme_path, bundle_dir / readme_path.name)

    archive_base = output_dir / target.output_basename
    if archive_base.exists():
        if archive_base.is_dir():
            shutil.rmtree(archive_base)
        else:
            archive_base.unlink()

    archive_path = Path(
        shutil.make_archive(
            base_name=str(archive_base),
            format=target.archive_format,
            root_dir=output_dir,
            base_dir=bundle_dir.name,
        )
    )

    LOGGER.info("Created archive %s", archive_path)
    return archive_path


def _write_checksum(archive_path: Path) -> Path:
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    checksum_path = Path(f"{archive_path}.sha256")
    checksum_path.write_text(f"{digest}  {archive_path.name}\n", encoding="utf-8")
    LOGGER.info("Generated checksum %s", checksum_path)
    return checksum_path


def _write_manifest(
    target: PackageTarget,
    archive_path: Path,
    checksum_path: Path,
    output_dir: Path,
) -> Path:
    manifest = {
        "target": target.name,
        "builder": target.builder,
        "platform": target.platform,
        "archive": archive_path.name,
        "checksum": checksum_path.name,
        "python": sys.version,
        "resources": [res for res in target.resources if (REPO_ROOT / res).exists()],
    }
    manifest_path = output_dir / f"{target.output_basename}.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    LOGGER.info("Wrote manifest %s", manifest_path)
    return manifest_path


def build_packages(
    targets: Iterable[PackageTarget],
    output_dir: Path,
    clean: bool = False,
) -> list[Path]:
    if clean:
        _ensure_clean_directory(output_dir)
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    artifacts: list[Path] = []
    for target in targets:
        if not target.supports_host():
            LOGGER.info("Skipping target %s: incompatible host", target.build_id)
            continue

        if target.builder == "pyinstaller":
            build_dir = _build_with_pyinstaller(target, output_dir)
        elif target.builder == "cx_freeze":
            build_dir = _build_with_cx_freeze(target, output_dir)
        else:
            raise ValueError(f"Unsupported builder: {target.builder}")

        archive_path = _create_archive(build_dir, target, output_dir)
        checksum_path = _write_checksum(archive_path)
        manifest_path = _write_manifest(target, archive_path, checksum_path, output_dir)
        artifacts.extend([archive_path, checksum_path, manifest_path])

    if not artifacts:
        LOGGER.warning("No packaging targets were built on this host")

    return artifacts


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build distributable archives for all supported platforms",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_DIST_DIR),
        help="Directory where packaged archives will be written",
    )
    parser.add_argument(
        "--target",
        action="append",
        dest="targets",
        help="Limit the build to the specified packaging target",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not remove previous artifacts before building",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    output_dir = Path(args.output_dir).resolve()
    selected_targets = [
        target
        for target in DEFAULT_TARGETS
        if args.targets is None or target.name in args.targets
    ]

    LOGGER.debug("Selected targets: %s", ", ".join(t.name for t in selected_targets))

    build_packages(
        targets=selected_targets,
        output_dir=output_dir,
        clean=not args.no_clean,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
