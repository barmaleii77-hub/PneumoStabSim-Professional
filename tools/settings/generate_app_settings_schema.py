#!/usr/bin/env python3
"""Generate the JSON Schema for :mod:`config/app_settings.json`.

The helper keeps the schema generation logic out of documentation snippets so
engineers can regenerate the canonical payload from any working directory.  It
is intentionally lightweight: import the Pydantic model definitions, normalise
the `$schema` metadata, and write the prettified document to the repository's
schema directory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.core.settings_models import AppSettings

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_PATH = REPO_ROOT / "schemas" / "settings" / "app_settings.schema.json"


def build_schema() -> dict[str, Any]:
    """Return the JSON Schema emitted by :class:`AppSettings`."""

    schema = AppSettings.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "App Settings"
    return schema


def write_schema(schema: dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate config/app_settings.json JSON Schema",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=(
            "Destination path for the generated schema. Defaults to"
            " schemas/settings/app_settings.schema.json relative to the"
            " repository root."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the confirmation message printed after generation.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    schema = build_schema()
    destination = (
        args.output if args.output.is_absolute() else (REPO_ROOT / args.output)
    )
    write_schema(schema, destination)
    if not args.quiet:
        print(f"[settings] Schema written to {destination.as_posix()}")


if __name__ == "__main__":
    main()
