#!/usr/bin/env python
"""Collect logs and reports into a timestamped artifact directory."""

import os
import pathlib
import shutil
import sys
import time
from collections.abc import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOG_SOURCES: Iterable[pathlib.Path] = (ROOT / "logs", ROOT / "reports")
ARTIFACT_DIR = ROOT / "reports"


def ensure_destination() -> pathlib.Path:
    dest = ARTIFACT_DIR / f"artifact_{int(time.time())}"
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def copy_tree(
    src: pathlib.Path, dest: pathlib.Path, *, skip_root: pathlib.Path | None = None
) -> None:
    """Copy files from *src* into *dest* while guarding against recursion."""

    if not src.exists():
        return

    resolved_skip = skip_root.resolve() if skip_root else None

    for root, dirs, files in os.walk(src):
        root_path = pathlib.Path(root)

        if resolved_skip is not None:
            # Prevent ``os.walk`` from descending into the destination directory we
            # are creating (e.g. reports/artifact_*/...). Without this guard the
            # walk would recurse into the freshly copied structure indefinitely.
            dirs[:] = [
                name
                for name in dirs
                if not (
                    resolved_skip == (root_path / name).resolve()
                    or resolved_skip in (root_path / name).resolve().parents
                )
            ]

        for filename in files:
            file_path = root_path / filename
            if resolved_skip is not None:
                resolved_file = file_path.resolve()
                if (
                    resolved_file == resolved_skip
                    or resolved_skip in resolved_file.parents
                ):
                    continue

            relative = file_path.relative_to(ROOT)
            target = dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target)


def tail(path: pathlib.Path, lines: int = 200) -> str:
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return "\n".join(content[-lines:])


def write_summary(dest: pathlib.Path) -> None:
    summary = dest / "SUMMARY.md"
    run_log = ROOT / "logs" / "run.log"
    with summary.open("w", encoding="utf-8") as handle:
        handle.write("# Run summary\n\n")
        if run_log.exists():
            handle.write("## tail logs/run.log\n\n```\n")
            handle.write(tail(run_log, 300))
            handle.write("\n```\n")
        else:
            handle.write("_no run.log_\n")


def main() -> int:
    destination = ensure_destination()
    for source in LOG_SOURCES:
        copy_tree(source, destination, skip_root=destination)
    write_summary(destination)
    print(f"[collect-logs] saved to {destination.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
