"""Settings migration runner.

This module implements a lightweight migration pipeline described in the
renovation master plan.  Migration descriptors are stored as JSON documents in
``config/migrations`` and contain a deterministic list of operations that can be
applied to a settings payload.  The runner keeps track of executed migrations in
``metadata.migrations`` so upgrades are idempotent.

Extended: записывает jsonl лог событий миграции в
``reports/settings/migrations.jsonl`` для трассируемости.

Example usage::

    python -m src.tools.settings_migrate --settings config/app_settings.json \
        --migrations config/migrations --in-place --verbose
"""
from __future__ import annotations

import argparse
import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from datetime import datetime, timezone
from collections.abc import Iterable, Sequence

SETTINGS_REPORT_ROOT = Path("reports") / "settings"  # default root; can be overridden by CLI
MIGRATIONS_LOG_PATH = SETTINGS_REPORT_ROOT / "migrations.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _payload_hash(payload: dict[str, Any]) -> str:
    try:
        dumped = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    except Exception:  # pragma: no cover
        dumped = "{}"
    return hashlib.sha256(dumped.encode("utf-8", "replace")).hexdigest()


def _append_migration_event(event: dict[str, Any], *, log_root: Path | None = None) -> None:
    root = log_root or SETTINGS_REPORT_ROOT
    path = root / "migrations.jsonl"
    try:
        root.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:  # pragma: no cover
        pass


def _deep_copy(value: Any) -> Any:
    """Return a JSON-compatible deep copy of *value*."""
    return json.loads(json.dumps(value))


def _split_path(path: str) -> list[str]:
    if not path:
        raise ValueError("Path must be a non-empty string")
    parts = [segment.strip() for segment in path.split(".") if segment.strip()]
    if not parts:
        raise ValueError("Path must contain at least one key")
    return parts


def _ensure_parent(
    root: dict[str, Any], parts: Sequence[str], create: bool
) -> dict[str, Any] | None:
    node: Any = root
    for part in parts:
        current = node.get(part)
        if current is None:
            if not create:
                return None
            current = {}
            node[part] = current
        elif not isinstance(current, dict):
            if not create:
                return None
            current = {}
            node[part] = current
        node = current
    if not isinstance(node, dict):
        return None
    return node


def _get_parent(
    root: dict[str, Any], parts: Sequence[str], create: bool
) -> tuple[dict[str, Any], str] | None:
    if not parts:
        raise ValueError("Path must contain at least one component")
    *parents, leaf = parts
    node = root
    if parents:
        parent_node = _ensure_parent(node, parents, create=create)
        if parent_node is None:
            return None
        node = parent_node
    return node, leaf


def _ensure_value(root: dict[str, Any], path: str, value: Any) -> bool:
    parts = _split_path(path)
    parent_info = _get_parent(root, parts, create=True)
    if parent_info is None:
        return False
    node, leaf = parent_info
    if leaf in node:
        return False
    node[leaf] = _deep_copy(value)
    return True


def _set_value(root: dict[str, Any], path: str, value: Any) -> bool:
    parts = _split_path(path)
    parent_info = _get_parent(root, parts, create=True)
    if parent_info is None:
        return False
    node, leaf = parent_info
    existing = node.get(leaf)
    new_value = _deep_copy(value)
    node[leaf] = new_value
    return existing != new_value


def _rename_key(root: dict[str, Any], path: str, new_name: str) -> bool:
    if not new_name:
        raise ValueError("new_name must be provided")
    parts = _split_path(path)
    parent_info = _get_parent(root, parts, create=False)
    if parent_info is None:
        return False
    node, leaf = parent_info
    if leaf not in node or new_name in node:
        return False
    node[new_name] = node.pop(leaf)
    return True


def _delete_key(root: dict[str, Any], path: str) -> bool:
    parts = _split_path(path)
    parent_info = _get_parent(root, parts, create=False)
    if parent_info is None:
        return False
    node, leaf = parent_info
    if leaf not in node:
        return False
    del node[leaf]
    return True


def _apply_operation(settings: dict[str, Any], operation: dict[str, Any]) -> bool:
    op_type = operation.get("op")
    if op_type == "ensure":
        return _ensure_value(settings, operation["path"], operation["value"])
    if op_type == "set":
        return _set_value(settings, operation["path"], operation["value"])
    if op_type == "rename":
        return _rename_key(settings, operation["path"], operation["new_name"])
    if op_type == "delete":
        return _delete_key(settings, operation["path"])
    raise ValueError(f"Unsupported operation type: {op_type!r}")


@dataclass(slots=True)
class MigrationDescriptor:
    """A single migration definition loaded from disk."""

    identifier: str
    description: str
    operations: list[dict[str, Any]]
    source: Path

    def apply(self, payload: dict[str, Any], *, log_root: Path | None = None) -> bool:
        """Apply the migration to *payload* with basic logging.

        Returns ``True`` if any operation mutated the payload.
        """
        changed = False
        op_results: list[dict[str, Any]] = []
        for operation in self.operations:
            mutated = _apply_operation(payload, operation)
            if mutated:
                changed = True
            op_type = operation.get("op", "<unknown>")
            path = operation.get("path")
            if path:
                print(f"[migration:{self.identifier}] {op_type} {path}")
            else:
                print(f"[migration:{self.identifier}] {op_type}")
            op_results.append({"op": op_type, "path": path, "changed": bool(mutated)})
        _append_migration_event({
            "timestamp": _utc_now(),
            "migration": self.identifier,
            "description": self.description,
            "source": str(self.source),
            "operations": op_results,
            "changed": changed,
        }, log_root=log_root)
        return changed


def _load_descriptor(path: Path) -> MigrationDescriptor:
    data = json.loads(path.read_text(encoding="utf-8"))
    identifier = data.get("id")
    description = data.get("description", "")
    operations = data.get("operations", [])
    if not identifier:
        raise ValueError(f"Migration file {path} is missing the 'id' field")
    if not isinstance(operations, list):
        raise ValueError(f"Migration file {path} must define a list of operations")
    return MigrationDescriptor(
        identifier=identifier,
        description=description,
        operations=operations,
        source=path,
    )


def load_migrations(directory: Path) -> list[MigrationDescriptor]:
    """Load migration descriptors from *directory* sorted by filename."""
    if not directory.exists():
        raise FileNotFoundError(f"Migrations directory does not exist: {directory}")
    descriptors: list[MigrationDescriptor] = []
    for path in sorted(directory.glob("*.json")):
        descriptors.append(_load_descriptor(path))
    return descriptors


def _ensure_metadata(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    metadata = payload.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("metadata section must be a JSON object")
    migrations = metadata.setdefault("migrations", [])
    if not isinstance(migrations, list):
        raise ValueError("metadata.migrations must be a list")
    return metadata, migrations


def apply_migrations(
    payload: dict[str, Any], migrations: Iterable[MigrationDescriptor], *, log_root: Path | None = None
) -> list[str]:
    """Apply *migrations* to *payload*.

    Returns the identifiers of migrations executed during this run."""
    _, applied = _ensure_metadata(payload)
    executed: list[str] = []
    for descriptor in migrations:
        if descriptor.identifier in applied:
            continue
        changed = descriptor.apply(payload, log_root=log_root)
        applied.append(descriptor.identifier)
        if changed:
            executed.append(descriptor.identifier)
    return executed


def _load_settings(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Settings file must contain a JSON object")
    return data


def _write_settings(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply JSON-based settings migrations")
    parser.add_argument(
        "--settings",
        type=Path,
        default=Path("config/app_settings.json"),
        help="Path to the settings JSON file",
    )
    parser.add_argument(
        "--migrations",
        type=Path,
        default=Path("config/migrations"),
        help="Directory containing migration descriptors",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write migrated settings to a different file",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Update the input file in place",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write any files; useful when combined with --verbose",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print applied migration identifiers",
    )
    parser.add_argument("--log-dir", type=Path, help="Override migration log directory (default: reports/settings)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    payload = _load_settings(args.settings)
    hash_before = _payload_hash(payload)
    migrations = load_migrations(args.migrations)
    log_root = args.log_dir if args.log_dir else SETTINGS_REPORT_ROOT

    executed = apply_migrations(payload, migrations, log_root=log_root)

    _append_migration_event({
        "timestamp": _utc_now(),
        "event": "migration-run-complete",
        "settings_file": str(args.settings),
        "migrations_dir": str(args.migrations),
        "executed": executed,
        "executed_count": len(executed),
        "payload_hash_before": hash_before,
        "payload_hash_after": _payload_hash(payload),
    }, log_root=log_root)

    if args.verbose:
        if executed:
            print("Applied migrations:", ", ".join(executed))
        else:
            print("No migrations executed")

    if args.dry_run:
        return 0

    target = (
        args.output
        if args.output
        else (args.settings if args.in_place or args.output is None else None)
    )
    if target is None:
        parser.error("Specify --in-place or --output when not using --dry-run")
    _write_settings(target, payload)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
