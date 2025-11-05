#!/usr/bin/env python
"""Install Qt toolchain with module fallback support."""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
from typing import Sequence, Set, Tuple

QT_ROOT = pathlib.Path(os.environ.get("QT_ROOT", "/opt/Qt")).resolve()
QT_ROOT.mkdir(parents=True, exist_ok=True)

QT_ARCH = os.environ.get("QT_ARCH", "gcc_64")

DEFAULT_VERSIONS = "6.10.0,6.9.0,6.8.2"
QT_VERSIONS = [
    ver.strip()
    for ver in os.environ.get("QT_VERSIONS", DEFAULT_VERSIONS).split(",")
    if ver.strip()
]

DEFAULT_MODULES = "qtdeclarative,qtquick3d,qttools,qtshadertools,qtimageformats"
QT_MODULES = [
    module.strip()
    for module in os.environ.get("QT_MODULES", DEFAULT_MODULES).split(",")
    if module.strip()
]

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


def _install(version: str, modules: Sequence[str]) -> None:
    cmd = AQT_BASE_CMD + ["install-qt", "linux", "desktop", version, QT_ARCH]
    if modules:
        cmd += ["-m", *modules]
    cmd += ["-O", str(QT_ROOT)]
    print(f"[qt] Installing Qt {version} ({QT_ARCH}) with modules: {modules or ['qtbase']}")
    subprocess.check_call(cmd)


def _select_version() -> Tuple[str, Sequence[str], Sequence[str]]:
    """Pick the best Qt version and module set available."""
    module_catalogue = {}
    for version in QT_VERSIONS:
        available = _list_available_modules(version)
        module_catalogue[version] = available
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
    present = [m for m in QT_MODULES if m.lower() in available]
    missing = [m for m in QT_MODULES if m.lower() not in available]
    print(
        f"[qt] Proceeding with partial module set for {preferred}; missing: {missing}",
        file=sys.stderr,
    )
    return preferred, present, missing


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
