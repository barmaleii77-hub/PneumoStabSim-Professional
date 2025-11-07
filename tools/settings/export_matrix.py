#!/usr/bin/env python3
"""Generate the settings control matrix documentation.

The Renovation master plan requires a living document that maps every
persisted setting to its owning module, validation metadata, and the UI
surface that manipulates it.  This helper parses the canonical settings
schema, inspects the default payload, and looks for matching bindings in
the UI sources (Python panels and QML fragments).

The output is a Markdown file intended to live at
``docs/settings_control_matrix.md``.  The script is deterministic so the
document can be regenerated as part of CI or whenever settings change.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Any
from collections.abc import Iterable, Iterator, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = REPO_ROOT / "config" / "schemas" / "app_settings.schema.json"
DEFAULT_SETTINGS_PATH = REPO_ROOT / "config" / "app_settings.json"
DEFAULT_BASELINE_PATH = REPO_ROOT / "config" / "baseline" / "app_settings.json"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "docs" / "settings_control_matrix.md"
UI_SEARCH_ROOTS = [REPO_ROOT / "src" / "ui", REPO_ROOT / "assets" / "qml"]


@dataclass(slots=True)
class SettingRow:
    path: str
    module: str
    default: Any
    validation: str
    ui_bindings: list[str]

    def formatted_default(self) -> str:
        text = json.dumps(self.default, ensure_ascii=False)
        if len(text) > 60:
            return text[:57] + "…"
        return text

    def formatted_bindings(self) -> str:
        if not self.ui_bindings:
            return "—"
        return "<br>".join(self.ui_bindings)


def load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Expected JSON file at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def iter_leaf_items(
    mapping: Any, prefix: Sequence[str]
) -> Iterator[tuple[list[str], Any]]:
    """Yield ``(path, value)`` pairs for non-mapping leaf nodes."""

    if isinstance(mapping, Mapping):
        for key, value in mapping.items():
            yield from iter_leaf_items(value, [*prefix, str(key)])
        return

    if isinstance(mapping, list):
        # Treat lists as leaf values – consumers typically replace the full list
        # instead of addressing individual indices.
        yield list(prefix), mapping
        return

    yield list(prefix), mapping


def find_schema_node(
    schema: Mapping[str, Any], path: Sequence[str]
) -> Mapping[str, Any] | None:
    node: Mapping[str, Any] | None = schema
    for segment in path:
        if not isinstance(node, Mapping):
            return None
        props = node.get("properties")
        if isinstance(props, Mapping) and segment in props:
            candidate = props[segment]
            if isinstance(candidate, Mapping):
                node = candidate
                continue
            return None
        return None
    return node


_VALIDATION_KEYS = (
    "type",
    "enum",
    "const",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "pattern",
    "format",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
)


def summarise_validation(schema_node: Mapping[str, Any] | None, value: Any) -> str:
    if schema_node:
        parts: list[str] = []
        for key in _VALIDATION_KEYS:
            if key not in schema_node:
                continue
            payload = schema_node[key]
            if key == "type" and isinstance(payload, list):
                parts.append(f"type: {', '.join(str(p) for p in payload)}")
            elif key == "type":
                parts.append(f"type: {payload}")
            elif key == "enum":
                parts.append(
                    "enum: "
                    + ", ".join(
                        json.dumps(item, ensure_ascii=False) for item in payload
                    )
                )
            elif key == "pattern":
                parts.append(f"pattern: /{payload}/")
            else:
                parts.append(f"{key}: {payload}")
        if parts:
            return "; ".join(parts)
    # Fallback to inferred Python type when schema metadata is missing.
    inferred = type(value).__name__
    if inferred == "list":
        inferred = "array"
    elif inferred == "dict":
        inferred = "object"
    return f"type: {inferred}"


def build_source_index(paths: Iterable[Path]) -> dict[Path, list[str]]:
    index: dict[Path, list[str]] = {}
    for root in paths:
        if not root.exists():
            continue
        for file in root.rglob("*"):
            if file.suffix not in {".py", ".qml"}:
                continue
            try:
                content = file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = file.read_text(encoding="utf-8", errors="ignore")
            index[file] = content.splitlines()
    return index


_WIDGET_RE = re.compile(r"self\.(?P<name>\w+)\s*=\s*(?P<widget>\w+)\(")
_QML_ID_RE = re.compile(r"id\s*:\s*(?P<identifier>\w+)")


def summarise_binding(path: Path, line_no: int, lines: list[str]) -> str:
    widget: str | None = None
    # Look upwards for a widget assignment in Python panels.
    for offset in range(0, 5):
        idx = line_no - offset
        if idx < 0:
            break
        match = _WIDGET_RE.search(lines[idx])
        if match:
            widget = f"{match.group('widget')} {match.group('name')}"
            break
        qml_match = _QML_ID_RE.search(lines[idx])
        if qml_match:
            widget = f"id {qml_match.group('identifier')}"
            break
    rel_path = path.relative_to(REPO_ROOT)
    return f"{rel_path}:{line_no + 1}{f' ({widget})' if widget else ''}"


def find_ui_bindings(
    index: Mapping[Path, list[str]],
    module: str,
    key: str,
    full_path: str,
    *,
    max_matches: int = 3,
) -> list[str]:
    search_terms = {f'"{full_path}"', f'"{module}.{key}"', f'"{key}"'}
    matches: list[str] = []
    for path, lines in index.items():
        for line_no, line in enumerate(lines):
            if not any(term in line for term in search_terms):
                continue
            matches.append(summarise_binding(path, line_no, lines))
            break
        if len(matches) >= max_matches:
            break
    return matches


def build_rows(
    schema: Mapping[str, Any],
    defaults_snapshot: Mapping[str, Any],
    metadata: Mapping[str, Any],
    *,
    source_index: Mapping[Path, list[str]],
) -> list[SettingRow]:
    rows: list[SettingRow] = []
    for path, value in iter_leaf_items(defaults_snapshot, ["current"]):
        module = path[1] if len(path) > 1 else "current"
        key = path[-1]
        schema_node = find_schema_node(schema, path)
        validation = summarise_validation(schema_node, value)
        full_path = ".".join(path)
        bindings = find_ui_bindings(source_index, module, key, full_path)
        rows.append(
            SettingRow(
                path=full_path,
                module=module,
                default=value,
                validation=validation,
                ui_bindings=bindings,
            )
        )

    for path, value in iter_leaf_items(metadata, ["metadata"]):
        schema_node = find_schema_node(schema, path)
        validation = summarise_validation(schema_node, value)
        full_path = ".".join(path)
        bindings: list[str] = []
        rows.append(
            SettingRow(
                path=full_path,
                module="metadata",
                default=value,
                validation=validation,
                ui_bindings=bindings,
            )
        )

    rows.sort(key=lambda row: row.path)
    return rows


def render_markdown(rows: Sequence[SettingRow]) -> str:
    header = dedent(
        """
        # Settings Control Matrix

        _Generated by `tools/settings/export_matrix.py`. Do not edit manually._

        | Setting | Default | Validation | UI Bindings |
        | --- | --- | --- | --- |
        """
    ).strip()

    lines = [header]
    for row in rows:
        lines.append(
            "| ``{}`` | {} | {} | {} |".format(
                row.path,
                row.formatted_default(),
                row.validation.replace("|", r"\|") or "—",
                row.formatted_bindings(),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA_PATH)
    parser.add_argument("--settings", type=Path, default=DEFAULT_SETTINGS_PATH)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    schema = load_json(args.schema)
    settings = load_json(args.settings)
    baseline = load_json(args.baseline)

    defaults_snapshot = baseline.get("defaults_snapshot") or settings.get(
        "defaults_snapshot"
    )
    if not isinstance(defaults_snapshot, Mapping):
        raise RuntimeError("defaults_snapshot must be an object in settings payload")

    metadata = settings.get("metadata")
    if not isinstance(metadata, Mapping):
        metadata = {}

    source_index = build_source_index(UI_SEARCH_ROOTS)
    rows = build_rows(schema, defaults_snapshot, metadata, source_index=source_index)
    output = render_markdown(rows)
    args.output.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
