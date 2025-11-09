"""Validate HDR skybox orientation metadata and reports.

This script enforces the expectations documented in the Phase 3
renovation plan: the authoritative list of skyboxes lives in
``config/baseline/materials.json`` and the rendered validation report is
published to ``reports/performance/hdr_orientation.md``.  CI runs this
script through ``make check`` so that stale or inconsistent metadata
surfaces immediately.
"""
from __future__ import annotations

import argparse
import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("config/baseline/materials.json")
DEFAULT_REPORT_PATH = Path("reports/performance/hdr_orientation.md")

ALLOWED_ORIENTATIONS = {"z-up", "y-up", "x-up"}
ALLOWED_STATUS = {"ok", "warning", "failed"}


@dataclass(frozen=True)
class Skybox:
    """Normalized representation of a skybox metadata entry."""

    identifier: str
    label: str
    file: str
    orientation: str
    rotation: float
    status: str
    notes: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "Skybox":
        try:
            identifier = str(payload["id"])
            label = str(payload["label"])
            file_name = str(payload["file"])
            orientation = str(payload.get("orientation", "")).strip().lower()
            rotation = float(payload.get("rotation", 0.0))
            status = str(payload.get("status", "")).strip().lower()
            notes = str(payload.get("notes", "")).strip()
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Invalid skybox payload: {payload!r}") from error

        return cls(
            identifier=identifier,
            label=label,
            file=file_name,
            orientation=orientation,
            rotation=rotation,
            status=status,
            notes=notes,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to materials configuration JSON containing skybox entries",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Path to the generated HDR orientation markdown report",
    )
    return parser.parse_args()


def load_skyboxes(config_path: Path) -> list[Skybox]:
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Skybox config not found: {config_path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {config_path}: {error}") from error

    skyboxes_raw = payload.get("skyboxes")
    if not isinstance(skyboxes_raw, list) or not skyboxes_raw:
        raise ValueError("Configuration must define a non-empty 'skyboxes' array")

    return [Skybox.from_mapping(entry) for entry in skyboxes_raw]


@dataclass(frozen=True)
class ReportRow:
    label: str
    file: str
    orientation: str
    rotation: float
    status: str
    notes: str


def parse_report(report_path: Path) -> Mapping[str, ReportRow]:
    try:
        lines = report_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as error:
        raise FileNotFoundError(f"HDR orientation report not found: {report_path}") from error

    table_start = None
    for index, line in enumerate(lines):
        if line.strip().startswith("|") and "Skybox" in line and "File" in line:
            table_start = index
            break
    if table_start is None or table_start + 2 >= len(lines):
        raise ValueError(
            "HDR orientation report does not contain the expected markdown table header"
        )

    header_separator_index = table_start + 1
    if not set(lines[header_separator_index].strip()) <= {"|", "-", " "}:
        raise ValueError("HDR orientation report table missing separator row")

    rows: dict[str, ReportRow] = {}
    for raw in lines[header_separator_index + 1 :]:
        stripped = raw.strip()
        if not stripped:
            break
        if not stripped.startswith("|"):
            break
        columns = [segment.strip() for segment in stripped.strip("|").split("|")]
        if len(columns) < 6:
            raise ValueError(f"Malformed row in HDR orientation report: {raw!r}")
        label, file_name, orientation, rotation_str, status, notes = columns[:6]
        rotation_value = _parse_rotation(rotation_str)
        rows[label] = ReportRow(
            label=label,
            file=file_name,
            orientation=orientation.lower(),
            rotation=rotation_value,
            status=_normalize_status(status),
            notes=notes,
        )
    if not rows:
        raise ValueError("HDR orientation report did not yield any rows")
    return rows


def _parse_rotation(value: str) -> float:
    stripped = value.strip().rstrip("°")
    try:
        return float(stripped)
    except ValueError as error:
        raise ValueError(f"Unable to parse rotation value: {value!r}") from error


def _normalize_status(value: str) -> str:
    trimmed = value.strip()
    if not trimmed:
        return ""
    emoji_map = {
        "✅": "ok",
        "⚠️": "warning",
        "❌": "failed",
    }
    if trimmed in emoji_map:
        return emoji_map[trimmed]
    for emoji, status in emoji_map.items():
        if trimmed.startswith(emoji):
            return status
    return trimmed.lower()


def validate_orientation(
    skyboxes: Iterable[Skybox], report_rows: Mapping[str, ReportRow]
) -> list[str]:
    entries = list(skyboxes)
    errors: list[str] = []

    for skybox in entries:
        if skybox.orientation not in ALLOWED_ORIENTATIONS:
            errors.append(
                f"Skybox '{skybox.label}' has unsupported orientation '{skybox.orientation}'"
            )
        if not math.isfinite(skybox.rotation):
            errors.append(
                f"Skybox '{skybox.label}' rotation must be finite, received {skybox.rotation!r}"
            )
        elif abs(skybox.rotation) > 360:
            errors.append(
                f"Skybox '{skybox.label}' rotation must be within ±360°, received {skybox.rotation}"
            )
        if skybox.status not in ALLOWED_STATUS:
            errors.append(
                f"Skybox '{skybox.label}' uses unsupported status '{skybox.status}'"
            )
        if not skybox.file.lower().endswith(".hdr"):
            errors.append(
                f"Skybox '{skybox.label}' references non-HDR file '{skybox.file}'"
            )
        if not skybox.notes:
            errors.append(f"Skybox '{skybox.label}' is missing descriptive notes")

        report_row = report_rows.get(skybox.label)
        if report_row is None:
            errors.append(
                f"Skybox '{skybox.label}' missing from HDR orientation report"
            )
            continue
        if report_row.file != skybox.file:
            errors.append(
                f"Skybox '{skybox.label}' file mismatch: config '{skybox.file}' vs report '{report_row.file}'"
            )
        if report_row.orientation != skybox.orientation:
            errors.append(
                f"Skybox '{skybox.label}' orientation mismatch: config '{skybox.orientation}' vs report '{report_row.orientation}'"
            )
        if not _rotation_matches(skybox.rotation, report_row.rotation):
            errors.append(
                f"Skybox '{skybox.label}' rotation mismatch: config {skybox.rotation} vs report {report_row.rotation}"
            )
        if report_row.status not in ALLOWED_STATUS:
            errors.append(
                f"Skybox '{skybox.label}' report uses unsupported status '{report_row.status}'"
            )
    report_labels = set(report_rows.keys())
    missing_from_config = report_labels.difference({skybox.label for skybox in entries})
    if missing_from_config:
        formatted = ", ".join(sorted(missing_from_config))
        errors.append(
            f"Report contains entries not present in configuration: {formatted}"
        )
    return errors


def _rotation_matches(expected: float, reported: float, tolerance: float = 1e-2) -> bool:
    return abs(expected - reported) <= tolerance


def main() -> int:
    args = parse_args()
    try:
        skyboxes = load_skyboxes(args.config)
        report_rows = parse_report(args.report)
        errors = validate_orientation(skyboxes, report_rows)
    except Exception as error:  # noqa: BLE001 - surface full error context to CI
        print(f"ERROR: {error}")
        return 1

    if errors:
        print("HDR orientation validation failed:")
        for issue in errors:
            print(f" - {issue}")
        return 1

    print(
        f"Validated {len(skyboxes)} skybox entries against {len(report_rows)} report rows — all checks passed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
