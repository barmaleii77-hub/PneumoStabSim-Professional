"""Command line interface for the backup service."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence as SequenceABC
from pathlib import Path
from typing import Sequence

from src.services import BackupService, discover_user_data_sources


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PneumoStabSim backup utility",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root containing configuration and report directories.",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="Directory where backup archives are stored (relative to root by default).",
    )
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        type=Path,
        help="Additional files or directories to include in backups (can be repeated).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    create_parser = sub.add_parser("create", help="Create a new backup archive.")
    create_parser.add_argument("--label", default=None, help="Optional label appended to the archive name.")
    create_parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help="Do not include a timestamp in the archive file name.",
    )

    list_parser = sub.add_parser("list", help="List available backup archives.")
    list_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of archives shown.",
    )

    restore_parser = sub.add_parser("restore", help="Restore data from an archive.")
    restore_parser.add_argument("archive", type=Path, help="Path to the archive to restore.")
    restore_parser.add_argument(
        "--target",
        type=Path,
        default=None,
        help="Destination directory for the restored files (defaults to project root).",
    )
    restore_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files instead of skipping them.",
    )

    inspect_parser = sub.add_parser("inspect", help="Display the manifest embedded in an archive.")
    inspect_parser.add_argument("archive", type=Path, help="Archive to inspect.")

    prune_parser = sub.add_parser("prune", help="Delete older backups, keeping the newest ones.")
    prune_parser.add_argument("keep", type=int, help="Number of recent backups to keep.")

    return parser


def _build_service(args: argparse.Namespace) -> BackupService:
    sources = None
    if args.sources:
        combined = list(discover_user_data_sources()) + [Path(src) for src in args.sources]
        sources = combined
    return BackupService(root=args.root, backup_dir=args.backup_dir, data_sources=sources)


def _cmd_create(service: BackupService, args: argparse.Namespace) -> int:
    report = service.create_backup(label=args.label, include_timestamp=not args.no_timestamp)
    print(f"Archive created: {report.archive_path}")
    if report.skipped:
        skipped = ", ".join(str(item) for item in report.skipped)
        print(f"Skipped sources: {skipped}")
    else:
        print("All configured sources included.")
    return 0


def _as_display_string(value: object, default: str = "unknown") -> str:
    if isinstance(value, str):
        return value
    return default


def _sequence_length(value: object) -> str:
    if isinstance(value, SequenceABC) and not isinstance(value, (str, bytes)):
        return str(len(value))
    return "-"


def _cmd_list(service: BackupService, args: argparse.Namespace) -> int:
    archives = service.list_archives()
    if args.limit is not None:
        archives = archives[: args.limit]
    if not archives:
        print(f"No backups found in {service.backup_dir}.")
        return 0

    print(f"Backups stored in {service.backup_dir}:")
    for archive in archives:
        created_display = "unknown"
        included_display = skipped_display = "-"
        try:
            manifest = service.inspect_backup(archive)
            created_display = _as_display_string(manifest.get("created_at"))
            included_display = _sequence_length(manifest.get("included"))
            skipped_display = _sequence_length(manifest.get("skipped"))
        except Exception:  # pragma: no cover - legacy archives without a manifest
            pass
        print(
            "  {name}\tcreated={created}\tincluded={included}\tskipped={skipped}".format(
                name=archive.name,
                created=created_display,
                included=included_display,
                skipped=skipped_display,
            )
        )
    return 0


def _cmd_restore(service: BackupService, args: argparse.Namespace) -> int:
    report = service.restore_backup(
        args.archive,
        target_root=args.target,
        overwrite=args.overwrite,
    )
    print(f"Restored {len(report.restored)} files into {report.target_root}.")
    if report.skipped:
        skipped = ", ".join(str(item) for item in report.skipped)
        print(f"Skipped existing files: {skipped}")
    return 0


def _cmd_inspect(service: BackupService, args: argparse.Namespace) -> int:
    manifest = service.inspect_backup(args.archive)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def _cmd_prune(service: BackupService, args: argparse.Namespace) -> int:
    removed = service.prune_backups(keep=args.keep)
    if not removed:
        print("No archives removed.")
    else:
        print("Removed archives:")
        for archive in removed:
            print(f"  {archive}")
    return 0


def run(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    service = _build_service(args)

    command = args.command
    if command == "create":
        return _cmd_create(service, args)
    if command == "list":
        return _cmd_list(service, args)
    if command == "restore":
        return _cmd_restore(service, args)
    if command == "inspect":
        return _cmd_inspect(service, args)
    if command == "prune":
        return _cmd_prune(service, args)
    parser.error(f"Unknown command: {command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run())
