"""CLI for auditing settings payloads against the repository baseline."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from collections.abc import Iterable, Sequence


ChangeType = Literal["added", "removed", "changed", "type"]


@dataclass(slots=True)
class DiffEntry:
    """Represents a single difference between two JSON payloads."""

    path: str
    change: ChangeType
    baseline: Any
    target: Any


def _normalise(value: Any) -> Any:
    """Return a JSON-compatible deep copy of *value*."""

    return json.loads(json.dumps(value))


def _build_path(root: str, segment: str) -> str:
    return f"{root}.{segment}" if root else segment


def _diff_dict(
    baseline: dict[str, Any],
    target: dict[str, Any],
    *,
    prefix: str,
    collector: list[DiffEntry],
) -> None:
    baseline_keys = set(baseline)
    target_keys = set(target)

    for key in sorted(baseline_keys - target_keys):
        collector.append(
            DiffEntry(
                path=_build_path(prefix, key),
                change="removed",
                baseline=_normalise(baseline[key]),
                target=None,
            )
        )

    for key in sorted(target_keys - baseline_keys):
        collector.append(
            DiffEntry(
                path=_build_path(prefix, key),
                change="added",
                baseline=None,
                target=_normalise(target[key]),
            )
        )

    for key in sorted(baseline_keys & target_keys):
        next_path = _build_path(prefix, key)
        _diff_values(
            baseline[key],
            target[key],
            prefix=next_path,
            collector=collector,
        )


def _diff_list(
    baseline: list[Any],
    target: list[Any],
    *,
    prefix: str,
    collector: list[DiffEntry],
) -> None:
    max_len = max(len(baseline), len(target))
    for index in range(max_len):
        path = f"{prefix}[{index}]"
        try:
            base_value = baseline[index]
            base_present = True
        except IndexError:
            base_value = None
            base_present = False
        try:
            target_value = target[index]
            target_present = True
        except IndexError:
            target_value = None
            target_present = False

        if base_present and not target_present:
            collector.append(
                DiffEntry(
                    path=path,
                    change="removed",
                    baseline=_normalise(base_value),
                    target=None,
                )
            )
            continue

        if target_present and not base_present:
            collector.append(
                DiffEntry(
                    path=path,
                    change="added",
                    baseline=None,
                    target=_normalise(target_value),
                )
            )
            continue

        _diff_values(base_value, target_value, prefix=path, collector=collector)


def _diff_values(
    baseline: Any,
    target: Any,
    *,
    prefix: str,
    collector: list[DiffEntry],
) -> None:
    if isinstance(baseline, dict) and isinstance(target, dict):
        _diff_dict(baseline, target, prefix=prefix, collector=collector)
        return

    if isinstance(baseline, list) and isinstance(target, list):
        _diff_list(baseline, target, prefix=prefix, collector=collector)
        return

    if type(baseline) is not type(target):
        collector.append(
            DiffEntry(
                path=prefix,
                change="type",
                baseline=type(baseline).__name__,
                target=type(target).__name__,
            )
        )
        collector.append(
            DiffEntry(
                path=prefix,
                change="changed",
                baseline=_normalise(baseline),
                target=_normalise(target),
            )
        )
        return

    if baseline != target:
        collector.append(
            DiffEntry(
                path=prefix,
                change="changed",
                baseline=_normalise(baseline),
                target=_normalise(target),
            )
        )


def diff_settings(
    baseline: dict[str, Any],
    target: dict[str, Any],
) -> list[DiffEntry]:
    """Return the list of differences between *baseline* and *target*."""

    collector: list[DiffEntry] = []
    _diff_values(baseline, target, prefix="", collector=collector)
    collector.sort(key=lambda entry: entry.path)
    return collector


def _format_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _format_summary(entries: Iterable[DiffEntry]) -> dict[str, int]:
    summary: dict[str, int] = {"added": 0, "removed": 0, "changed": 0, "type": 0}
    for entry in entries:
        summary[entry.change] += 1
    return summary


def _render_text(entries: list[DiffEntry]) -> str:
    if not entries:
        return "No differences detected."

    summary = _format_summary(entries)
    lines = [
        "Settings audit report",
        "---------------------",
        "Summary:",
        f"  ➕ добавлено: {summary['added']}",
        f"  ➖ удалено:   {summary['removed']}",
        f"  ~ изменено:  {summary['changed']}",
        f"  ❗ тип:       {summary['type']}",
        "",
        "Details:",
    ]

    for entry in entries:
        if entry.change == "added":
            lines.append(f"  ➕ {entry.path} = {_format_value(entry.target)}")
        elif entry.change == "removed":
            lines.append(f"  ➖ {entry.path} (было {_format_value(entry.baseline)})")
        elif entry.change == "type":
            lines.append(
                f"  ❗ {entry.path} тип изменён: {entry.baseline} -> {entry.target}"
            )
        else:
            lines.append(
                f"  ~ {entry.path}: {_format_value(entry.baseline)} ->"
                f" {_format_value(entry.target)}"
            )
    return "\n".join(lines)


def _render_markdown(entries: list[DiffEntry]) -> str:
    if not entries:
        return "# Settings audit\n\nNo differences detected.\n"

    summary = _format_summary(entries)
    lines = [
        "# Settings audit",
        "",
        "## Summary",
        "",
        "| Change | Count |",
        "| --- | ---: |",
        f"| Added | {summary['added']} |",
        f"| Removed | {summary['removed']} |",
        f"| Changed | {summary['changed']} |",
        f"| Type | {summary['type']} |",
        "",
        "## Details",
        "",
    ]

    for entry in entries:
        if entry.change == "added":
            lines.append(
                f"- **Added** `{entry.path}` = `{_format_value(entry.target)}`"
            )
        elif entry.change == "removed":
            lines.append(
                f"- **Removed** `{entry.path}` (was `{_format_value(entry.baseline)}`)"
            )
        elif entry.change == "type":
            lines.append(
                f"- **Type change** `{entry.path}`: `{entry.baseline}` → `{entry.target}`"
            )
        else:
            lines.append(
                "- **Changed** `{path}`: `{before}` → `{after}`".format(
                    path=entry.path,
                    before=_format_value(entry.baseline),
                    after=_format_value(entry.target),
                )
            )
    lines.append("")
    return "\n".join(lines)


def render_report(entries: list[DiffEntry], *, format: str) -> str:
    """Render *entries* using the requested *format*."""

    if format == "markdown":
        return _render_markdown(entries)
    if format == "text":
        return _render_text(entries)
    raise ValueError(f"Unsupported format: {format}")


def _load_settings(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Settings file must contain a JSON object: {path}")
    return payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare two settings payloads and highlight differences",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("config/app_settings.json"),
        help="Baseline settings file (defaults to repository config)",
    )
    parser.add_argument(
        "--target",
        type=Path,
        required=True,
        help="Runtime settings file to audit",
    )
    parser.add_argument(
        "--format",
        choices=("text", "markdown"),
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the report to this path instead of stdout",
    )
    parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        help="Return a non-zero exit code when differences are found",
    )
    return parser


def generate_report(
    baseline_path: Path,
    target_path: Path,
    *,
    output_format: str,
) -> tuple[list[DiffEntry], str]:
    baseline = _load_settings(baseline_path)
    target = _load_settings(target_path)
    entries = diff_settings(baseline, target)
    rendered = render_report(entries, format=output_format)
    return entries, rendered


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    entries, report = generate_report(
        args.baseline,
        args.target,
        output_format=args.format,
    )

    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report)

    if args.fail_on_diff and entries:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
