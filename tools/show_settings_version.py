"""Utility script to display the settings metadata version.

This helper avoids platform-specific quoting pitfalls when users
need to quickly verify the metadata version contained in
``config/app_settings.json``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print the metadata.version field from a settings file."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/app_settings.json"),
        help="Path to the settings file (defaults to config/app_settings.json)",
    )
    return parser.parse_args()


def load_settings(path: Path) -> dict:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:  # pragma: no cover - runtime guard
        raise SystemExit(f"Settings file not found: {path}") from exc

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:  # pragma: no cover - runtime guard
        raise SystemExit(f"Failed to parse {path}: {exc}") from exc


def extract_version(data: dict) -> str:
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        raise SystemExit("Settings metadata section is missing or invalid")

    version = metadata.get("version")
    if not isinstance(version, str):
        raise SystemExit("Settings metadata version is missing or not a string")

    return version


def main() -> int:
    args = parse_args()
    data = load_settings(args.config)
    version = extract_version(data)
    print(f"Settings version: {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
