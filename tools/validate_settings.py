"""CLI utility for validating application settings against the JSON schema.

The validator is lightweight and intended to run in headless CI environments
as well as during application bootstrap. It performs the following steps:

* load the target settings file and the schema (UTF-8 encoded JSON);
* validate the payload using the Draft 2020-12 specification;
* print a concise success or failure report and exit with an appropriate code.

Exit codes
==========
0
    Validation succeeded.
1
    Validation failed because of schema violations, unreadable files or an
    invalid schema definition.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "app_settings.json"
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "config" / "app_settings.schema.json"


def _load_json(path: Path) -> Any:
    """Load a JSON document from *path* using UTF-8 encoding."""

    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def _collect_schema_errors(payload: Any, schema: Any) -> list[str]:
    """Return a sorted list of human-readable schema validation errors."""

    validator = Draft202012Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(payload), key=lambda err: err.path):
        location = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{location}: {error.message}")
    return errors


def _print_error(message: str) -> None:
    print(message, file=sys.stderr)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--settings-file",
        type=Path,
        default=DEFAULT_SETTINGS_PATH,
        help="Path to the application settings JSON file (default: config/app_settings.json)",
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help="Path to the JSON schema file (default: config/app_settings.schema.json)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress success output. Errors are always printed to stderr.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the validator and return the process exit code."""

    args = parse_args(argv)

    try:
        settings_payload = _load_json(args.settings_file)
    except (FileNotFoundError, ValueError) as exc:
        _print_error(str(exc))
        return 1

    try:
        schema_payload = _load_json(args.schema_file)
    except (FileNotFoundError, ValueError) as exc:
        _print_error(str(exc))
        return 1

    try:
        errors = _collect_schema_errors(settings_payload, schema_payload)
    except SchemaError as exc:
        _print_error(f"Invalid schema: {exc}")
        return 1

    if errors:
        _print_error("Settings validation failed:")
        for issue in errors:
            _print_error(f" - {issue}")
        return 1

    if not args.quiet:
        print(
            f"Validation OK: {args.settings_file.resolve()} conforms to {args.schema_file.resolve()}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
