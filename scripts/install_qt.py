#!/usr/bin/env python
"""Install Qt toolchain with module fallback support."""

from __future__ import annotations

import os
import pathlib
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable, Sequence

QT_ROOT = pathlib.Path(os.environ.get("QT_ROOT", "/opt/Qt")).resolve()
QT_ROOT.mkdir(parents=True, exist_ok=True)

DEFAULT_ARCH_CANDIDATES = ["gcc_64", "linux_gcc_64"]

_env_arches = [
    arch.strip()
    for arch in os.environ.get("QT_ARCHES", "").split(",")
    if arch.strip()
]

if not _env_arches:
    single_arch = os.environ.get("QT_ARCH", "")
    if single_arch:
        _env_arches = [single_arch]

QT_ARCH_CANDIDATES = []
for candidate in _env_arches + DEFAULT_ARCH_CANDIDATES:
    key = candidate.strip()
    if key and key not in QT_ARCH_CANDIDATES:
        QT_ARCH_CANDIDATES.append(key)

AQT_BASE_URL = os.environ.get("AQT_BASE")

DEFAULT_VERSIONS = "6.10.0"
MINIMUM_QT_VERSION = (6, 10, 0)
QT_VERSIONS = [
    ver.strip()
    for ver in os.environ.get("QT_VERSIONS", DEFAULT_VERSIONS).split(",")
    if ver.strip()
]

DEFAULT_MODULES = "qtbase,qtdeclarative,qtquick3d,qttools,qtshadertools,qtimageformats"
QT_MODULES = [
    module.strip()
    for module in os.environ.get("QT_MODULES", DEFAULT_MODULES).split(",")
    if module.strip()
]

QT_BASE_MODULE = "qtbase"

AQT_BASE_CMD = [sys.executable, "-m", "aqt"]


def _aqt_install_args() -> list[str]:
    """Return shared aqt arguments for the configured repository base."""

    if AQT_BASE_URL:
        return ["-b", AQT_BASE_URL]
    return []


_arch_cache: dict[str, list[str]] = {}


def _list_available_arches(version: str) -> list[str]:
    """Return the architectures published by aqt for a Qt version."""

    if version in _arch_cache:
        return _arch_cache[version]

    try:
        out = subprocess.check_output(
            AQT_BASE_CMD
            + ["list-qt", "linux", "desktop", "--arch", version],
            text=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - diagnostic path
        print(
            f"[qt] Unable to list architectures for {version}: {exc}",
            file=sys.stderr,
        )
        arches: list[str] = []
    else:
        arches = []
        seen: set[str] = set()
        for line in out.splitlines():
            token = line.strip().split()[0:1]
            if not token:
                continue
            arch = token[0]
            if arch in seen:
                continue
            seen.add(arch)
            arches.append(arch)

    _arch_cache[version] = arches
    return arches


def _candidate_arches(version: str) -> list[str]:
    """Return candidate architectures prioritising explicit configuration."""

    ordered: list[str] = []
    for arch in QT_ARCH_CANDIDATES + _list_available_arches(version):
        if arch not in ordered:
            ordered.append(arch)
    return ordered


def _list_available_modules(version: str, arch: str) -> set[str]:
    """Return a lower-case set of modules available for the version/arch."""
    try:
        out = subprocess.check_output(
            AQT_BASE_CMD
            + [
                "list-qt",
                "linux",
                "desktop",
                "--modules",
                version,
                arch,
            ],
            text=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - diagnostic path
        print(
            f"[qt] Unable to list modules for {version}/{arch}: {exc}",
            file=sys.stderr,
        )
        return set()

    available: set[str] = set()
    for line in out.splitlines():
        token = line.strip().split()[0:1]
        if token:
            available.add(token[0].lower())
    return available


def _version_sort_key(version: str) -> tuple[int, ...]:
    """Return a tuple suitable for sorting Qt semantic versions."""

    parts = [int(part) for part in re.findall(r"\d+", version)]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def _parse_version_tuple(version: str) -> tuple[int, int, int]:
    parts = [int(part) for part in re.findall(r"\d+", version)]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def _validate_versions(versions: Sequence[str]) -> None:
    minimum = ".".join(str(part) for part in MINIMUM_QT_VERSION)
    for version in versions:
        if _parse_version_tuple(version) < MINIMUM_QT_VERSION:
            raise RuntimeError(
                f"Qt version '{version}' is not supported. Minimum required: {minimum}"
            )


_validate_versions(QT_VERSIONS)


def _list_available_versions() -> Sequence[str]:
    """Return distinct Qt 6.x versions reported by aqt sorted newest first."""

    try:
        out = subprocess.check_output(
            AQT_BASE_CMD + ["list-qt", "linux", "desktop"], text=True
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - diagnostic path
        print(f"[qt] Unable to list available Qt versions: {exc}", file=sys.stderr)
        return []

    seen: set[str] = set()
    versions: list[str] = []
    for line in out.splitlines():
        token = line.strip().split()[0:1]
        if not token:
            continue
        version = token[0]
        if not version.startswith("6."):
            continue
        if version in seen:
            continue
        seen.add(version)
        versions.append(version)

    versions.sort(key=_version_sort_key, reverse=True)
    return versions


def _normalise_modules(modules: Iterable[str]) -> list[str]:
    """Ensure the qtbase module is included and order is preserved."""

    normalised: list[str] = []
    seen: set[str] = set()
    for module in modules:
        key = module.lower()
        if key in seen:
            continue
        seen.add(key)
        normalised.append(module)

    if QT_BASE_MODULE not in {m.lower() for m in normalised}:
        normalised.insert(0, QT_BASE_MODULE)

    return normalised


def _install(version: str, arch: str, modules: Sequence[str]) -> None:
    base_cmd = (
        AQT_BASE_CMD
        + [
            "install-qt",
            "linux",
            "desktop",
            version,
            arch,
        ]
        + _aqt_install_args()
        + ["-O", str(QT_ROOT)]
    )

    modules = _normalise_modules(modules)

    primary_cmd = base_cmd[:-2] + ["-m", *modules] + base_cmd[-2:]
    print(f"[qt] Installing Qt {version} ({arch}) with modules: {modules}")
    try:
        subprocess.check_call(primary_cmd)
        return
    except subprocess.CalledProcessError as exc:
        print(
            f"[qt] Install with requested modules failed for {version}/{arch}: {exc}",
            file=sys.stderr,
        )

    fallback_cmd = base_cmd[:-2] + ["-m", QT_BASE_MODULE] + base_cmd[-2:]
    try:
        print(f"[qt] Attempting fallback install with {QT_BASE_MODULE} only")
        subprocess.check_call(fallback_cmd)
        return
    except subprocess.CalledProcessError as exc:
        print(
            f"[qt] Fallback install with {QT_BASE_MODULE} failed: {exc}",
            file=sys.stderr,
        )

    print("[qt] Attempting bare install without explicit modules", file=sys.stderr)
    subprocess.check_call(base_cmd)


def _collect_module_catalogue(version: str) -> list[tuple[str, set[str]]]:
    """Return (arch, modules) pairs with available metadata for a version."""

    catalogue: list[tuple[str, set[str]]] = []
    for arch in _candidate_arches(version):
        available = _list_available_modules(version, arch)
        if not available:
            continue
        catalogue.append((arch, available))
    if not catalogue:
        print(
            f"[qt] No module metadata available for {version} with supported architectures",
            file=sys.stderr,
        )
    return catalogue


def _select_version() -> tuple[str, str, Sequence[str], Sequence[str]]:
    """Pick the best Qt version, architecture, and module set available."""

    module_catalogue: dict[str, list[tuple[str, set[str]]]] = {}
    for version in QT_VERSIONS:
        options = _collect_module_catalogue(version)
        module_catalogue[version] = options
        for arch, available in options:
            if QT_BASE_MODULE not in available:
                print(
                    f"[qt] Skipping {version}/{arch}: required module '{QT_BASE_MODULE}' missing",
                    file=sys.stderr,
                )
                continue
            missing = [m for m in QT_MODULES if m.lower() not in available]
            if not missing:
                return version, arch, QT_MODULES, []
            print(
                f"[qt] {version}/{arch} missing modules: {missing}; attempting fallback if available",
                file=sys.stderr,
            )

    preferred = QT_VERSIONS[0] if QT_VERSIONS else None
    if not preferred:
        raise RuntimeError("QT_VERSIONS is empty; cannot install Qt")

    preferred_options = module_catalogue.get(preferred) or _collect_module_catalogue(preferred)
    for arch, available in preferred_options:
        if QT_BASE_MODULE not in available:
            continue
        present = [m for m in QT_MODULES if m.lower() in available]
        missing = [m for m in QT_MODULES if m.lower() not in available]
        print(
            f"[qt] Proceeding with partial module set for {preferred}/{arch}; missing: {missing}",
            file=sys.stderr,
        )
        return preferred, arch, present or [QT_BASE_MODULE], missing
    if preferred_options:
        print(
            f"[qt] Preferred version {preferred} lacks '{QT_BASE_MODULE}' on all discovered architectures",
            file=sys.stderr,
        )

    print(
        f"[qt] Preferred version {preferred} unavailable; searching available versions",
        file=sys.stderr,
    )
    for candidate in _list_available_versions():
        options = _collect_module_catalogue(candidate)
        for arch, available in options:
            if QT_BASE_MODULE not in available:
                continue
            present = [m for m in QT_MODULES if m.lower() in available]
            missing = [m for m in QT_MODULES if m.lower() not in available]
            print(
                f"[qt] Falling back to {candidate}/{arch}; missing modules: {missing}",
                file=sys.stderr,
            )
            return candidate, arch, present or [QT_BASE_MODULE], missing

    raise RuntimeError("Unable to locate any Qt version with available modules via aqt")


def _update_symlink(version: str) -> None:
    target = (QT_ROOT / version).resolve()
    current = QT_ROOT / "current"
    if current.is_symlink() or current.exists():
        if current.is_dir() and not current.is_symlink():
            shutil.rmtree(current)
        else:
            current.unlink()
    current.symlink_to(target, target_is_directory=True)
    (QT_ROOT / "CURRENT_VERSION").write_text(version, encoding="utf-8")
    print(f"[qt] Active Qt version: {version} -> {target}")


def main() -> int:
    version, arch, modules, missing = _select_version()

    toolchain_path = QT_ROOT / version / arch
    already_installed = toolchain_path.exists()
    if already_installed:
        print(f"[qt] Qt {version} ({arch}) already present; skipping installation")
    else:
        try:
            _install(version, arch, modules)
        except subprocess.CalledProcessError as exc:
            raise SystemExit(f"[qt] Installation failed for {version}/{arch}: {exc}") from exc

    _update_symlink(version)

    if missing:
        print(
            "[qt] WARNING: some requested modules are unavailable: "
            + ", ".join(missing),
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
