#!/usr/bin/env python3
"""Utilities for maintaining QML translation catalogues.

This script wraps Qt's lupdate/lrelease tooling and performs static checks
against the QML sources to ensure no strings are missing from the translation
catalogues. It also generates machine readable reports under
``reports/localization`` that CI can upload or inspect.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections.abc import Sequence

from defusedxml import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[1]
QML_ROOT = REPO_ROOT / "assets" / "qml"
I18N_ROOT = REPO_ROOT / "assets" / "i18n"
REPORT_ROOT = REPO_ROOT / "reports" / "localization"

# Regex patterns for qsTr/qsTrId lookups.
_QSTR_DOUBLE_RE = re.compile(r"qsTr\s*\(\s*\"((?:[^\\\"]|\\.)*)\"\s*\)")
_QSTR_SINGLE_RE = re.compile(r"qsTr\s*\(\s*'((?:[^\\']|\\.)*)'\s*\)")
_QSTRID_RE = re.compile(r"qsTrId\s*\(\s*\"([^)\"]+)\"\s*\)")


class LocalizationError(Exception):
    """Raised when mandatory localization checks fail."""


def _decode_escaped(text: str) -> str:
    """Convert escape sequences from QML strings into real characters."""

    import ast

    literal = '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return ast.literal_eval(literal)


def gather_qml_catalogue(
    qml_root: Path,
) -> tuple[dict[str, dict[str, list[str]]], set[str], set[str]]:
    """Scan QML files for ``qsTr`` and ``qsTrId`` usages.

    Returns a tuple consisting of a per-file inventory, the union of all
    ``qsTr`` source strings, and the union of all ``qsTrId`` identifiers.
    """

    per_file: dict[str, dict[str, list[str]]] = {}
    all_sources: set[str] = set()
    all_ids: set[str] = set()

    for qml_path in sorted(qml_root.rglob("*.qml")):
        try:
            content = qml_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = qml_path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                try:
                    content = qml_path.read_text(encoding="cp1251")
                except UnicodeDecodeError as exc:  # pragma: no cover - defensive guard
                    raise LocalizationError(
                        f"Failed to decode {qml_path}: {exc}"
                    ) from exc

        sources: set[str] = set()
        ids: set[str] = set()

        for pattern in (_QSTR_DOUBLE_RE, _QSTR_SINGLE_RE):
            for match in pattern.finditer(content):
                decoded = _decode_escaped(match.group(1))
                sources.add(decoded)

        for match in _QSTRID_RE.finditer(content):
            ids.add(match.group(1).strip())

        rel_path = str(qml_path.relative_to(REPO_ROOT))
        per_file[rel_path] = {
            "sources": sorted(sources),
            "ids": sorted(ids),
        }

        all_sources.update(sources)
        all_ids.update(ids)

    return per_file, all_sources, all_ids


def parse_ts_file(ts_path: Path) -> dict[str, object]:
    """Extract metadata and message information from a Qt ``.ts`` file."""

    tree = ET.parse(ts_path)
    root = tree.getroot()

    language = root.attrib.get("language") or ""
    contexts = []
    sources: set[str] = set()
    ids: set[str] = set()
    unfinished: list[dict[str, str]] = []

    for context_elem in root.findall("context"):
        context_name = context_elem.findtext("name", default="")
        messages = []
        for message in context_elem.findall("message"):
            source_text = message.findtext("source", default="")
            message_id = message.attrib.get("id", "")
            translation_elem = message.find("translation")
            translation_text = (
                translation_elem.text if translation_elem is not None else ""
            )
            translation_type = (
                translation_elem.attrib.get("type")
                if translation_elem is not None
                else ""
            )

            if source_text:
                sources.add(source_text)
            if message_id:
                ids.add(message_id)
            if translation_type == "unfinished":
                unfinished.append(
                    {
                        "context": context_name,
                        "source": source_text,
                        "id": message_id,
                    }
                )

            messages.append(
                {
                    "source": source_text,
                    "id": message_id,
                    "translation": translation_text or "",
                    "unfinished": translation_type == "unfinished",
                }
            )

        contexts.append(
            {
                "name": context_name,
                "message_count": len(messages),
            }
        )

    return {
        "file": str(ts_path.relative_to(REPO_ROOT)),
        "language": language,
        "contexts": contexts,
        "sources": sources,
        "ids": ids,
        "unfinished": unfinished,
    }


def run_command(command: Sequence[str], cwd: Path | None = None) -> None:
    """Execute a subprocess and propagate failures with readable output."""

    try:
        subprocess.run(command, cwd=cwd, check=True)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - integration path
        cmd_display = " ".join(command)
        raise LocalizationError(
            f"Command failed: {cmd_display}\nReturn code: {exc.returncode}"
        ) from exc


def resolve_command(candidates: Sequence[str]) -> str | None:
    """Return the first available command from ``candidates``."""

    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def ensure_tools(
    lupdate_override: str | None, lrelease_override: str | None
) -> tuple[str, str]:
    """Locate lupdate and lrelease executables."""

    if lupdate_override:
        lupdate = lupdate_override
    else:
        lupdate = resolve_command(["pyside6-lupdate", "lupdate", "pylupdate6"])
    if not lupdate:
        raise LocalizationError(
            "Unable to locate lupdate. Install Qt Linguist tools or provide --lupdate path."
        )

    if lrelease_override:
        lrelease = lrelease_override
    else:
        lrelease = resolve_command(["pyside6-lrelease", "lrelease"])
    if not lrelease:
        raise LocalizationError(
            "Unable to locate lrelease. Install Qt Linguist tools or provide --lrelease path."
        )

    return lupdate, lrelease


def update_catalogues(lupdate: str, lrelease: str, ts_files: Sequence[Path]) -> None:
    """Invoke ``lupdate`` followed by ``lrelease`` for the supplied ``.ts`` files."""

    if not ts_files:
        print("No translation sources detected; skipping lupdate/lrelease.")
        return

    ts_args = [str(path) for path in ts_files]
    command = [lupdate, str(QML_ROOT)] + ["-ts", *ts_args]
    print(f"Running {' '.join(command)}")
    run_command(command, cwd=REPO_ROOT)

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    for ts_path in ts_files:
        qm_name = ts_path.with_suffix(".qm").name
        qm_output = REPORT_ROOT / qm_name
        command = [lrelease, str(ts_path), "-qm", str(qm_output)]
        print(f"Running {' '.join(command)}")
        run_command(command, cwd=REPO_ROOT)


def build_reports(qml_catalogue, qml_sources, qml_ids, translation_summaries):
    """Persist machine readable localization reports."""

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)

    inventory_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qml": {
            "total_files": len(qml_catalogue),
            "total_qsTr_strings": len(qml_sources),
            "total_qsTrId_strings": len(qml_ids),
            "files": qml_catalogue,
        },
        "translations": translation_summaries,
    }

    inventory_path = REPORT_ROOT / "inventory.json"
    inventory_path.write_text(
        json.dumps(inventory_payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    status_payload = {
        "generated_at": inventory_payload["generated_at"],
        "summary": {
            ts_name: {
                "missing_sources": sorted(summary.get("missing_sources", [])),
                "missing_ids": sorted(summary.get("missing_ids", [])),
                "unused_sources": sorted(summary.get("unused_sources", [])),
                "unused_ids": sorted(summary.get("unused_ids", [])),
                "unfinished": summary.get("unfinished", []),
            }
            for ts_name, summary in translation_summaries.items()
        },
    }

    status_path = REPORT_ROOT / "status.json"
    status_path.write_text(
        json.dumps(status_payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    summary_lines = [
        "# Localization Summary",
        "",
        f"Generated at: {inventory_payload['generated_at']}",
        "",
        "## Catalogue overview",
        f"- QML files scanned: {len(qml_catalogue)}",
        f"- Unique qsTr strings: {len(qml_sources)}",
        f"- Unique qsTrId identifiers: {len(qml_ids)}",
        "",
        "## Translation coverage",
        "| Catalogue | Language | qsTr | qsTrId | Missing qsTr | Missing qsTrId | Unfinished | Unused qsTr | Unused qsTrId |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for ts_name, summary in sorted(translation_summaries.items()):
        summary_lines.append(
            "| {name} | {language} | {sources} | {ids} | {missing_sources} | {missing_ids} | {unfinished} | {unused_sources} | {unused_ids} |".format(
                name=ts_name,
                language=summary.get("language", ""),
                sources=len(summary.get("sources", [])),
                ids=len(summary.get("ids", [])),
                missing_sources=len(summary.get("missing_sources", [])),
                missing_ids=len(summary.get("missing_ids", [])),
                unfinished=len(summary.get("unfinished", [])),
                unused_sources=len(summary.get("unused_sources", [])),
                unused_ids=len(summary.get("unused_ids", [])),
            )
        )

    summary_lines.extend(["", "## QML string hotspots"])

    qml_rows = []
    for path, inventory in qml_catalogue.items():
        sources = inventory.get("sources", [])
        ids = inventory.get("ids", [])
        total = len(sources) + len(ids)
        qml_rows.append(
            (
                total,
                len(sources),
                len(ids),
                path,
            )
        )

    qml_rows.sort(reverse=True)
    if qml_rows:
        summary_lines.append("| QML file | qsTr strings | qsTrId identifiers | Total |")
        summary_lines.append("| --- | ---: | ---: | ---: |")
        max_rows = min(len(qml_rows), 20)
        for total, source_count, id_count, path in qml_rows[:max_rows]:
            summary_lines.append(f"| {path} | {source_count} | {id_count} | {total} |")
        if len(qml_rows) > max_rows:
            summary_lines.extend(
                [
                    "",
                    f"_Only the top {max_rows} of {len(qml_rows)} QML files are shown. Use `inventory.json` for the complete catalogue._",
                ]
            )
    else:
        summary_lines.append("No QML files detected.")

    summary_lines.extend(
        [
            "",
            "## Usage",
            "Inspect `inventory.json` for the per-file catalogue and `status.json` for validation results. This summary is regenerated each time `tools/update_translations.py` runs.",
        ]
    )

    summary_path = REPORT_ROOT / "summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")


def compute_translation_deltas(
    translation_data: dict[str, object],
    qml_sources: set[str],
    qml_ids: set[str],
) -> dict[str, object]:
    """Calculate missing/unused translation keys against the QML inventory."""

    sources_set = set(translation_data["sources"])  # type: ignore[index]
    ids_set = set(translation_data["ids"])  # type: ignore[index]

    missing_sources = sorted(qml_sources - sources_set)
    unused_sources = sorted(sources_set - qml_sources)
    missing_ids = sorted(qml_ids - ids_set)
    unused_ids = sorted(ids_set - qml_ids)

    result = dict(translation_data)
    result.update(
        {
            "sources": sorted(sources_set),
            "ids": sorted(ids_set),
            "missing_sources": missing_sources,
            "unused_sources": unused_sources,
            "missing_ids": missing_ids,
            "unused_ids": unused_ids,
        }
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run validation without invoking lupdate/lrelease.",
    )
    parser.add_argument("--lupdate", help="Override lupdate executable path.")
    parser.add_argument("--lrelease", help="Override lrelease executable path.")
    parser.add_argument(
        "--fail-on-unfinished",
        action="store_true",
        help="Treat unfinished translations as errors during validation.",
    )
    args = parser.parse_args(argv)

    if not QML_ROOT.exists():
        raise LocalizationError(f"QML directory not found: {QML_ROOT}")
    if not I18N_ROOT.exists():
        raise LocalizationError(f"Translation directory not found: {I18N_ROOT}")

    ts_files = sorted(I18N_ROOT.glob("*.ts"))

    if not args.check:
        lupdate_cmd, lrelease_cmd = ensure_tools(args.lupdate, args.lrelease)
        update_catalogues(lupdate_cmd, lrelease_cmd, ts_files)

    qml_catalogue, qml_sources, qml_ids = gather_qml_catalogue(QML_ROOT)

    translation_summaries: dict[str, dict[str, object]] = {}
    for ts_path in ts_files:
        translation_info = parse_ts_file(ts_path)
        summary = compute_translation_deltas(translation_info, qml_sources, qml_ids)
        key = Path(translation_info["file"]).name  # type: ignore[index]
        translation_summaries[key] = summary

    build_reports(qml_catalogue, qml_sources, qml_ids, translation_summaries)

    failures: list[str] = []
    for name, summary in translation_summaries.items():
        missing_sources = summary["missing_sources"]  # type: ignore[index]
        missing_ids = summary["missing_ids"]  # type: ignore[index]
        unfinished = summary["unfinished"]  # type: ignore[index]

        if missing_sources:
            failures.append(f"{name}: {len(missing_sources)} missing qsTr strings")
        if missing_ids:
            failures.append(f"{name}: {len(missing_ids)} missing qsTrId identifiers")
        if unfinished and args.fail_on_unfinished:
            failures.append(f"{name}: {len(unfinished)} unfinished translations")

        print(f"Translation summary for {name}:")
        print(f"  Total qsTr strings: {len(summary['sources'])}")
        print(f"  Total qsTrId entries: {len(summary['ids'])}")
        print(f"  Missing qsTr strings: {len(missing_sources)}")
        print(f"  Missing qsTrId entries: {len(missing_ids)}")
        print(f"  Unfinished translations: {len(unfinished)}")
        print(f"  Unused qsTr strings: {len(summary['unused_sources'])}")
        print(f"  Unused qsTrId entries: {len(summary['unused_ids'])}")

    if failures:
        failure_text = "; ".join(failures)
        if args.check:
            print(f"Localization validation failed: {failure_text}", file=sys.stderr)
        raise LocalizationError(failure_text)

    print("Localization validation succeeded.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    try:
        raise SystemExit(main())
    except LocalizationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
