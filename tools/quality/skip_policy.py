from __future__ import annotations

import argparse
import os
import sys
from defusedxml import ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

_TRUTHY = {"1", "true", "yes", "on"}


@dataclass(slots=True)
class SkippedTestCase:
    """Representation of a skipped pytest test case."""

    suite: str
    case: str
    message: str
    source: Path


@dataclass(slots=True)
class SkipPolicyContext:
    """Configuration collected from the current CI/local environment."""

    running_in_ci: bool
    allow_skips: bool
    justification: str
    summary_path: Path | None
    step_summary_path: Path | None
    project_root: Path


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in _TRUTHY


def _relative_display(path: Path, project_root: Path | None) -> str:
    if project_root is None:
        return str(path)
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def resolve_skip_policy_context(
    *,
    env: os._Environ[str] | None = None,
    summary_path: Path | None = None,
    project_root: Path | None = None,
) -> SkipPolicyContext:
    environment = os.environ if env is None else env
    cwd_root = project_root or Path.cwd()
    return SkipPolicyContext(
        running_in_ci=_is_truthy(environment.get("CI"))
        or bool(environment.get("GITHUB_ACTIONS")),
        allow_skips=_is_truthy(environment.get("PSS_ALLOW_SKIPPED_TESTS"))
        or _is_truthy(environment.get("CI_ALLOW_SKIPS")),
        justification=(environment.get("CI_SKIP_REASON") or "").strip(),
        summary_path=summary_path,
        step_summary_path=Path(environment["GITHUB_STEP_SUMMARY"]).resolve()
        if environment.get("GITHUB_STEP_SUMMARY")
        else None,
        project_root=cwd_root,
    )


def collect_skipped_tests(
    xml_paths: Iterable[Path], *, project_root: Path | None = None
) -> list[SkippedTestCase]:
    skipped: list[SkippedTestCase] = []
    for xml_file in xml_paths:
        try:
            tree = ET.parse(xml_file)
        except (ET.ParseError, FileNotFoundError):
            print(
                "[skip-policy] Unable to parse JUnit report while scanning skips: "
                f"{_relative_display(xml_file, project_root)}"
            )
            continue
        root = tree.getroot()
        for testcase in root.iterfind(".//testcase"):
            skipped_nodes = list(testcase.findall("skipped"))
            if not skipped_nodes:
                continue
            classname = testcase.attrib.get("classname", "")
            name = testcase.attrib.get("name", "")
            test_id = (
                f"{classname}.{name}"
                if classname and name
                else (name or classname or "<unknown>")
            )
            for node in skipped_nodes:
                message = (node.attrib.get("message") or node.text or "").strip()
                skipped.append(
                    SkippedTestCase(
                        suite=xml_file.stem,
                        case=test_id,
                        message=message,
                        source=xml_file,
                    )
                )
    return skipped


def write_skipped_summary(
    entries: Sequence[SkippedTestCase],
    *,
    summary_path: Path,
    step_summary_path: Path | None = None,
    project_root: Path | None = None,
) -> Path | None:
    if not entries:
        if summary_path.exists():
            try:
                summary_path.unlink()
            except OSError:
                pass
        return None

    lines = [
        "# Skipped pytest tests",
        "",
        "| Suite | Test | Reason |",
        "| --- | --- | --- |",
    ]
    for entry in entries:
        reason = (entry.message or "—").replace("|", "\\|")
        lines.append(f"| {entry.suite} | `{entry.case}` | {reason} |")

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if step_summary_path:
        try:
            with step_summary_path.open("a", encoding="utf-8") as handle:
                handle.write("## Skipped pytest tests\n\n")
                handle.write(summary_path.read_text(encoding="utf-8"))
                handle.write("\n")
        except OSError:
            pass

    return summary_path


def evaluate_skip_policy(
    entries: Sequence[SkippedTestCase],
    *,
    context: SkipPolicyContext,
    summary_path: Path | None = None,
) -> str | None:
    if not entries or not context.running_in_ci:
        return None

    count = len(entries)
    plural = "s" if count != 1 else ""
    location_hint = ""
    if summary_path:
        location_hint = (
            f" See {_relative_display(summary_path, context.project_root)} for details."
        )

    base_message = (
        f"{count} skipped test{plural} detected across pytest suites." + location_hint
    )

    if not context.allow_skips:
        return (
            base_message
            + " Re-run the job with PSS_ALLOW_SKIPPED_TESTS=1 and provide CI_SKIP_REASON to acknowledge intentional skips."
        )

    if not context.justification:
        return (
            base_message
            + " CI_SKIP_REASON must describe why skips are accepted when PSS_ALLOW_SKIPPED_TESTS=1 is set."
        )

    print(f"[skip-policy] Skipped tests acknowledged: {context.justification}")
    return None


def _default_junit_paths(summary_path: Path | None) -> list[Path]:
    base_dir = summary_path.parent if summary_path else Path("reports/tests")
    return sorted(base_dir.glob("*.xml"))


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Enforce pytest skip policy using JUnit XML reports."
    )
    parser.add_argument(
        "--junitxml",
        action="append",
        dest="junitxml",
        help="Path to a JUnit XML report (can be provided multiple times). Defaults to reports/tests/*.xml",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("reports/tests/skipped_tests_summary.md"),
        help="Path to write the skipped-tests markdown summary.",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Force CI mode even when CI environment variables are absent.",
    )
    parser.add_argument(
        "--allow-skips",
        action="store_true",
        help="Permit skips (still requires CI_SKIP_REASON when running in CI mode).",
    )

    args = parser.parse_args(argv)

    junit_paths = (
        [Path(p) for p in args.junitxml]
        if args.junitxml
        else _default_junit_paths(args.summary)
    )

    context = resolve_skip_policy_context(summary_path=args.summary)
    if args.ci:
        context.running_in_ci = True
    if args.allow_skips:
        context.allow_skips = True

    skipped_cases = collect_skipped_tests(
        junit_paths, project_root=context.project_root
    )
    summary_path = write_skipped_summary(
        skipped_cases,
        summary_path=args.summary,
        step_summary_path=context.step_summary_path,
        project_root=context.project_root,
    )
    violation = evaluate_skip_policy(
        skipped_cases, context=context, summary_path=summary_path
    )
    if violation:
        print(f"[skip-policy] {violation}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
