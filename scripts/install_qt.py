#!/usr/bin/env python
"""Install Qt toolchain with module fallback support."""

from __future__ import annotations

import os
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Iterable, List, Sequence, Set, Tuple

QT_ROOT = pathlib.Path(os.environ.get("QT_ROOT", "/opt/Qt")).resolve()
QT_ROOT.mkdir(parents=True, exist_ok=True)

QT_ARCH = os.environ.get("QT_ARCH", "gcc_64")

DEFAULT_VERSIONS = "6.10.0,6.9.0,6.8.2"
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


def _list_available_modules(version: str) -> Set[str]:
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
                QT_ARCH,
            ],
            text=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - diagnostic path
        print(
            f"[qt] Unable to list modules for {version}/{QT_ARCH}: {exc}",
            file=sys.stderr,
        )
        return set()

    available: Set[str] = set()
    for line in out.splitlines():
        token = line.strip().split()[0:1]
        if token:
            available.add(token[0].lower())
    return available


def _version_sort_key(version: str) -> Tuple[int, ...]:
    """Return a tuple suitable for sorting Qt semantic versions."""

    parts = [int(part) for part in re.findall(r"\d+", version)]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def _list_available_versions() -> Sequence[str]:
    """Return distinct Qt 6.x versions reported by aqt sorted newest first."""

    try:
        out = subprocess.check_output(
            AQT_BASE_CMD + ["list-qt", "linux", "desktop"], text=True
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - diagnostic path
        print(f"[qt] Unable to list available Qt versions: {exc}", file=sys.stderr)
        return []

    seen: Set[str] = set()
    versions: List[str] = []
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


def _normalise_modules(modules: Iterable[str]) -> List[str]:
    """Ensure the qtbase module is included and order is preserved."""

    normalised: List[str] = []
    seen: Set[str] = set()
    for module in modules:
        key = module.lower()
        if key in seen:
            continue
        seen.add(key)
        normalised.append(module)

    if QT_BASE_MODULE not in {m.lower() for m in normalised}:
        normalised.insert(0, QT_BASE_MODULE)

    return normalised


def _install(version: str, modules: Sequence[str]) -> None:
    base_cmd = AQT_BASE_CMD + [
        "install-qt",
        "linux",
        "desktop",
        version,
        QT_ARCH,
        "-O",
        str(QT_ROOT),
    ]

    modules = _normalise_modules(modules)

    primary_cmd = base_cmd[:-2] + ["-m", *modules] + base_cmd[-2:]
    print(f"[qt] Installing Qt {version} ({QT_ARCH}) with modules: {modules}")
    try:
        subprocess.check_call(primary_cmd)
        return
    except subprocess.CalledProcessError as exc:
        print(
            f"[qt] Install with requested modules failed for {version}/{QT_ARCH}: {exc}",
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


def _select_version() -> Tuple[str, Sequence[str], Sequence[str]]:
    """Pick the best Qt version and module set available."""
    module_catalogue = {}
    for version in QT_VERSIONS:
        available = _list_available_modules(version)
        module_catalogue[version] = available
        if not available:
            print(
                f"[qt] No module metadata available for {version}/{QT_ARCH}; will try next",
                file=sys.stderr,
            )
            continue
        if QT_BASE_MODULE not in available:
            print(
                f"[qt] Skipping {version}: required module '{QT_BASE_MODULE}' missing",
                file=sys.stderr,
            )
            continue
        missing = [m for m in QT_MODULES if m.lower() not in available]
        if not missing:
            return version, QT_MODULES, []
        print(
            f"[qt] {version} missing modules: {missing}; attempting fallback if available",
            file=sys.stderr,
        )

    preferred = QT_VERSIONS[0] if QT_VERSIONS else None
    if not preferred:
        raise RuntimeError("QT_VERSIONS is empty; cannot install Qt")

    available = module_catalogue.get(preferred) or _list_available_modules(preferred)
    if available and QT_BASE_MODULE in available:
        present = [m for m in QT_MODULES if m.lower() in available]
        missing = [m for m in QT_MODULES if m.lower() not in available]
        print(
            f"[qt] Proceeding with partial module set for {preferred}; missing: {missing}",
            file=sys.stderr,
        )
        return preferred, present or [QT_BASE_MODULE], missing
    if available and QT_BASE_MODULE not in available:
        print(
            f"[qt] Preferred version {preferred} lacks '{QT_BASE_MODULE}', skipping",
            file=sys.stderr,
        )

    print(
        f"[qt] Preferred version {preferred} unavailable; searching available versions",
        file=sys.stderr,
    )
    for candidate in _list_available_versions():
        available = _list_available_modules(candidate)
        if not available or QT_BASE_MODULE not in available:
            continue
        present = [m for m in QT_MODULES if m.lower() in available]
        missing = [m for m in QT_MODULES if m.lower() not in available]
        print(
            f"[qt] Falling back to {candidate}; missing modules: {missing}",
            file=sys.stderr,
        )
        return candidate, present or [QT_BASE_MODULE], missing

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
    version, modules, missing = _select_version()

    toolchain_path = QT_ROOT / version / QT_ARCH
    already_installed = toolchain_path.exists()
    if already_installed:
        print(f"[qt] Qt {version} already present; skipping installation")
    else:
        try:
            _install(version, modules)
        except subprocess.CalledProcessError as exc:
            raise SystemExit(f"[qt] Installation failed for {version}: {exc}") from exc

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
