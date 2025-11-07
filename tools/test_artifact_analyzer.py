"""Post-test artifact analyzer.

This module scans JSON log and metric artifacts produced by the test and
quality gates.  It flags execution errors, warnings, physical constraint
violations and performance regressions, then exports a consolidated summary
as both JSON and Markdown.

The script is intentionally defensive: it tolerates missing inputs and
unstructured payloads so it can run in CI after ``make check`` without
requiring additional configuration.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from collections.abc import Iterable


ERROR_LEVELS = {"error", "errors", "fail", "failed", "failure", "fatal", "critical"}
WARNING_LEVELS = {"warn", "warning", "warnings"}
PASS_LEVELS = {"ok", "pass", "passed", "success", "succeeded"}


@dataclass
class Issue:
    """Represents a single detected issue."""

    category: str
    message: str
    artifact: str
    context: str | None = None

    def to_dict(self) -> dict[str, str]:
        payload = {
            "category": self.category,
            "message": self.message,
            "artifact": self.artifact,
        }
        if self.context:
            payload["context"] = self.context
        return payload


@dataclass
class AnalysisResult:
    """Aggregated results for all processed artifacts."""

    analyzed_files: list[str] = field(default_factory=list)
    parse_errors: list[Issue] = field(default_factory=list)
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    constraint_violations: list[Issue] = field(default_factory=list)
    performance_regressions: list[Issue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analyzed_files": self.analyzed_files,
            "issues": {
                "errors": [issue.to_dict() for issue in self.errors],
                "warnings": [issue.to_dict() for issue in self.warnings],
                "constraint_violations": [
                    issue.to_dict() for issue in self.constraint_violations
                ],
                "performance_regressions": [
                    issue.to_dict() for issue in self.performance_regressions
                ],
            },
            "parse_errors": [issue.to_dict() for issue in self.parse_errors],
        }


def _as_relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _gather_inputs(
    inputs: Iterable[Path], *, excludes: set[Path] | None = None
) -> list[Path]:
    seen: set[Path] = set()
    discovered: list[Path] = []
    resolved_excludes: set[Path] = {path.resolve() for path in excludes or set()}
    for path in inputs:
        if not path.exists():
            continue
        if path.is_dir():
            for candidate in sorted(path.rglob("*.json")):
                resolved = candidate.resolve()
                if resolved in resolved_excludes or candidate in seen:
                    continue
                seen.add(candidate)
                discovered.append(candidate)
        elif path.suffix.lower() == ".json":
            resolved = path.resolve()
            if resolved in resolved_excludes or path in seen:
                continue
            seen.add(path)
            discovered.append(path)
    return discovered


def _normalise_level(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "pass" if value else "fail"
    text = str(value).strip().lower()
    return text or None


def _extract_message(record: dict[str, Any]) -> str | None:
    for key in ("message", "msg", "detail", "details", "description", "error"):
        candidate = record.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def _context_from_trail(trail: list[str]) -> str | None:
    if not trail:
        return None
    return " > ".join(trail)


def _is_performance_context(trail: list[str], file_path: Path) -> bool:
    keywords = (
        "performance",
        "frame",
        "fps",
        "latency",
        "throughput",
        "profile",
    )
    lower_path = str(file_path).lower()
    if any(word in lower_path for word in keywords):
        return True
    return any(any(word in segment.lower() for word in keywords) for segment in trail)


def _is_constraint_context(trail: list[str], message: str | None) -> bool:
    keywords = (
        "constraint",
        "limit",
        "violation",
        "pressure",
        "force",
        "torque",
        "stroke",
    )
    if message and any(word in message.lower() for word in keywords):
        return True
    return any(any(word in segment.lower() for word in keywords) for segment in trail)


def _collect_issues(
    data: Any,
    *,
    trail: list[str],
    file_path: Path,
    result: AnalysisResult,
    artifact: str,
) -> None:
    if isinstance(data, dict):
        level = None
        for key in ("level", "severity", "status", "state", "result"):
            if key in data:
                level = _normalise_level(data.get(key))
                if level:
                    break

        message = _extract_message(data)
        context = _context_from_trail(trail)

        passed_flag = data.get("passed")
        if isinstance(passed_flag, bool) and not passed_flag:
            entry_message = message or "Check reported failure"
            if _is_performance_context(trail, file_path):
                result.performance_regressions.append(
                    Issue("performance", entry_message, artifact, context)
                )
            elif _is_constraint_context(trail, entry_message):
                result.constraint_violations.append(
                    Issue("constraint", entry_message, artifact, context)
                )
            else:
                result.errors.append(Issue("error", entry_message, artifact, context))

        if level:
            if level in ERROR_LEVELS:
                entry_message = message or f"{level.upper()} detected"
                result.errors.append(Issue("error", entry_message, artifact, context))
            elif level in WARNING_LEVELS:
                entry_message = message or f"{level.upper()} detected"
                result.warnings.append(
                    Issue("warning", entry_message, artifact, context)
                )

        if _is_constraint_context(trail, message):
            # Capture explicit constraint flags such as numeric violation counts.
            for key, value in data.items():
                if value in (None, "", [], {}, 0, 0.0):
                    continue
                if isinstance(value, (int, float)) and value <= 0:
                    continue
                if isinstance(value, str) and value.lower() in PASS_LEVELS:
                    continue
                lower_key = key.lower()
                if any(
                    term in lower_key for term in ("violation", "constraint", "limit")
                ):
                    human_value = value if isinstance(value, str) else str(value)
                    result.constraint_violations.append(
                        Issue(
                            "constraint",
                            f"{key}: {human_value}",
                            artifact,
                            context,
                        )
                    )

        # Nested structures
        for nested_key, nested_value in data.items():
            _collect_issues(
                nested_value,
                trail=[*trail, str(nested_key)],
                file_path=file_path,
                result=result,
                artifact=artifact,
            )
    elif isinstance(data, list):
        for index, item in enumerate(data):
            _collect_issues(
                item,
                trail=[*trail, f"[{index}]"],
                file_path=file_path,
                result=result,
                artifact=artifact,
            )


def _analyze_file(path: Path, *, root: Path, result: AnalysisResult) -> None:
    artifact = _as_relative(path, root)
    result.analyzed_files.append(artifact)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        message = f"Failed to parse JSON: {exc}"
        result.parse_errors.append(Issue("parse", message, artifact))
        return
    except OSError as exc:
        message = f"Failed to read file: {exc}"
        result.parse_errors.append(Issue("io", message, artifact))
        return

    _collect_issues(
        payload,
        trail=[],
        file_path=path,
        result=result,
        artifact=artifact,
    )


def _render_markdown(result: AnalysisResult) -> str:
    def _format_section(title: str, issues: list[Issue]) -> str:
        if not issues:
            return f"### {title}\n\n- ✅ No issues detected\n"
        lines = [f"### {title}"]
        for issue in issues:
            context = f" — {issue.context}" if issue.context else ""
            lines.append(
                f"- ❌ [{issue.artifact}]({issue.artifact}){context}: {issue.message}"
            )
        return "\n".join(lines) + "\n"

    sections = ["## Post-test Analysis Report"]
    sections.append(f"Analyzed **{len(result.analyzed_files)}** JSON artifact(s).")
    sections.append("")
    sections.append(_format_section("Errors", result.errors))
    sections.append(_format_section("Warnings", result.warnings))
    sections.append(
        _format_section("Physical Constraint Violations", result.constraint_violations)
    )
    sections.append(
        _format_section("Performance Regressions", result.performance_regressions)
    )
    if result.parse_errors:
        sections.append("### Parse Errors")
        for issue in result.parse_errors:
            context = f" — {issue.context}" if issue.context else ""
            sections.append(
                f"- ⚠️ [{issue.artifact}]({issue.artifact}){context}: {issue.message}"
            )
    else:
        sections.append("### Parse Errors\n\n- ✅ No parse issues detected")
    return "\n".join(sections).strip() + "\n"


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze JSON log and metric artifacts produced by tests."
    )
    parser.add_argument(
        "--input",
        dest="inputs",
        action="append",
        default=[],
        help="Path to a JSON file or directory containing JSON artifacts. "
        "The option can be provided multiple times.",
    )
    parser.add_argument(
        "--artifact-root",
        default=".",
        help="Base path used when generating relative artifact links.",
    )
    parser.add_argument(
        "--output-json",
        default="reports/tests/test_analysis_summary.json",
        help="Location of the JSON summary report.",
    )
    parser.add_argument(
        "--output-markdown",
        default="reports/tests/test_analysis_summary.md",
        help="Location of the Markdown summary report.",
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Return a non-zero exit status if any issues are detected.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_arguments(argv)
    print(
        f"[test-artifact-analyzer] Detected platform: {platform.system()} {platform.release()}"
    )

    input_paths = [Path(path) for path in args.inputs]
    if not input_paths:
        # Default to the common artifact directories when no explicit inputs are provided.
        input_paths = [
            Path("reports/tests"),
            Path("reports/quality"),
            Path("reports/performance"),
            Path("logs"),
        ]

    json_output = Path(args.output_json)
    markdown_output = Path(args.output_markdown)

    excludes = {json_output.resolve()}
    gathered_files = _gather_inputs(input_paths, excludes=excludes)
    if not gathered_files:
        print(
            "[test-artifact-analyzer] No JSON artifacts discovered; nothing to analyze."
        )
        gathered_files = []

    root = Path(args.artifact_root).resolve()
    result = AnalysisResult()

    for file_path in gathered_files:
        _analyze_file(file_path, root=root, result=result)

    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[test-artifact-analyzer] JSON summary written to {json_output}")

    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(
        _render_markdown(result),
        encoding="utf-8",
    )
    print(f"[test-artifact-analyzer] Markdown summary written to {markdown_output}")

    if args.fail_on_issues and (
        result.errors
        or result.constraint_violations
        or result.performance_regressions
        or result.parse_errors
    ):
        print("[test-artifact-analyzer] Issues detected; failing execution.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
