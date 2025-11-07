"""Utilities for auditing accessibility metadata in QML files.

The audit scans QML files for explicit accessibility metadata (Accessible
attached properties, descriptive context objects, and keyboard shortcut
hints) and outputs a Markdown summary that can be attached to reports.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable, Sequence

_ACCESSIBLE_PATTERN = re.compile(r"Accessible\\.")
_ACCESSIBILITY_DICT_PATTERN = re.compile(r"accessibility\s*:\s*[\{(]", re.IGNORECASE)
_SHORTCUT_PATTERN = re.compile(r'"sequence"\s*:\s*"([^"]+)"')
_ACCESSIBLE_NAME_PATTERN = re.compile(r'Accessible\\.name\s*:\s*"([^"]+)"')


@dataclass
class AccessibilityStat:
    """Summary of accessibility markers for a QML file."""

    path: Path
    has_accessibility: bool
    has_shortcut_hints: bool
    accessible_names: Sequence[str]
    shortcut_sequences: Sequence[str]


def _iter_qml_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.qml")):
        if path.is_file():
            yield path


def _analyse_file(path: Path) -> AccessibilityStat:
    text = path.read_text(encoding="utf-8", errors="ignore")
    has_accessibility = bool(
        _ACCESSIBLE_PATTERN.search(text) or _ACCESSIBILITY_DICT_PATTERN.search(text)
    )
    shortcut_sequences = _SHORTCUT_PATTERN.findall(text)
    accessible_names = _ACCESSIBLE_NAME_PATTERN.findall(text)
    has_shortcut_hints = bool(shortcut_sequences)
    return AccessibilityStat(
        path=path,
        has_accessibility=has_accessibility,
        has_shortcut_hints=has_shortcut_hints,
        accessible_names=accessible_names,
        shortcut_sequences=shortcut_sequences,
    )


def collect_qml_accessibility_stats(root: Path) -> list[AccessibilityStat]:
    """Collect accessibility stats for every QML file beneath *root*."""

    root = root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"QML root '{root}' does not exist")

    return [_analyse_file(path) for path in _iter_qml_files(root)]


def _render_markdown(stats: Sequence[AccessibilityStat], root: Path) -> str:
    accessible_total = sum(1 for stat in stats if stat.has_accessibility)
    shortcut_total = sum(1 for stat in stats if stat.has_shortcut_hints)
    total = len(stats)

    lines: list[str] = [
        "# QML Accessibility Audit",
        "",
        f"*Root:* `{root}`",
        f"*Files scanned:* {total}",
        f"*Files with explicit accessibility metadata:* {accessible_total}",
        f"*Files exposing keyboard shortcuts:* {shortcut_total}",
        "",
        "| File | Accessibility | Shortcuts | Accessible names | Shortcut sequences |",
        "| --- | --- | --- | --- | --- |",
    ]

    for stat in stats:
        relative = stat.path.relative_to(root)
        accessibility = "✅" if stat.has_accessibility else "⚠️"
        shortcuts = "✅" if stat.has_shortcut_hints else "⚠️"
        names = "<br/>".join(stat.accessible_names) or "—"
        sequences = "<br/>".join(stat.shortcut_sequences) or "—"
        lines.append(
            f"| `{relative}` | {accessibility} | {shortcuts} | {names} | {sequences} |"
        )

    return "\n".join(lines) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("assets/qml"),
        help="Root directory containing QML files (default: assets/qml)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional path to write the Markdown report",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    stats = collect_qml_accessibility_stats(args.root)
    report = _render_markdown(stats, args.root.resolve())

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
        print(f"Accessibility audit written to {args.report}")
    else:
        print(report)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
