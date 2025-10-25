"""Generate the Visual Studio Insiders environment configuration as JSON."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional
import sys


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate PneumoStabSim Visual Studio Insiders environment",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Path to the PneumoStabSim project root",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to store the generated JSON",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Pretty-print JSON with the given indentation (default: 2)",
    )
    return parser.parse_args(argv)


def _load_builders(project_root: Path):
    resolved = project_root.resolve()
    project_root_str = str(resolved)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)

    from src.tools.visualstudio_insiders import (
        build_insiders_environment,
        dumps_environment,
    )

    return build_insiders_environment, dumps_environment


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    build_environment, dump_environment = _load_builders(args.project_root)
    environment = build_environment(args.project_root)
    json_payload = dump_environment(environment, indent=args.indent)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json_payload + "\n", encoding="utf-8")
    else:
        print(json_payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
