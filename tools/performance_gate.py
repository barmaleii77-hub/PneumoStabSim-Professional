#!/usr/bin/env python3
"""CI gate for performance regression detection."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class MetricOutcome:
    """Result for a single metric evaluation."""

    name: str
    actual: Optional[float]
    passed: bool
    messages: List[str]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_averages(report_payload: Dict[str, Any]) -> Dict[str, float]:
    extra = report_payload.get("extra") or {}
    averages = extra.get("averages") or {}
    if not averages:
        metadata = report_payload.get("metadata") or {}
        averages = metadata.get("averages") or {}
    if not isinstance(averages, dict):
        return {}
    numeric: Dict[str, float] = {}
    for key, value in averages.items():
        if isinstance(value, (int, float)):
            numeric[key] = float(value)
    return numeric


def _evaluate_metric(
    name: str,
    config: Dict[str, Any],
    actual: Optional[float],
    *,
    fail_on_missing: bool = True,
) -> MetricOutcome:
    messages: List[str] = []
    optional = bool(config.get("optional"))
    if actual is None:
        if fail_on_missing and not optional:
            messages.append("metric missing from report")
            passed = False
        else:
            passed = True
        return MetricOutcome(name=name, actual=None, passed=passed, messages=messages)

    max_value = config.get("max")
    min_value = config.get("min")
    reference = config.get("reference")
    tolerance = config.get("tolerance_percent")

    passed = True
    if isinstance(max_value, (int, float)) and actual > float(max_value):
        passed = False
        messages.append(f"{actual:.3f} > max {float(max_value):.3f}")
    if isinstance(min_value, (int, float)) and actual < float(min_value):
        passed = False
        messages.append(f"{actual:.3f} < min {float(min_value):.3f}")

    if isinstance(reference, (int, float)) and isinstance(tolerance, (int, float)):
        reference = float(reference)
        tolerance = float(tolerance) / 100.0
        lower_bound = reference * (1.0 - tolerance)
        upper_bound = reference * (1.0 + tolerance)
        if actual < lower_bound or actual > upper_bound:
            passed = False
            messages.append(
                f"{actual:.3f} outside tolerance [{lower_bound:.3f}, {upper_bound:.3f}]"
            )

    return MetricOutcome(name=name, actual=actual, passed=passed, messages=messages)


def _format_outcome(outcome: MetricOutcome) -> str:
    if outcome.actual is None:
        actual_repr = "n/a"
    else:
        actual_repr = f"{outcome.actual:.3f}"
    status = "PASS" if outcome.passed else "FAIL"
    suffix = "" if not outcome.messages else " | " + "; ".join(outcome.messages)
    return f"[{status}] {outcome.name}: {actual_repr}{suffix}"


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Qt Quick performance metrics against baseline thresholds",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "report", type=Path, help="Path to the freshly generated JSON report."
    )
    parser.add_argument(
        "baseline",
        type=Path,
        help="Path to the baseline threshold file (JSON).",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=None,
        help="Optional path where a machine-readable summary (JSON) will be written.",
    )
    parser.add_argument(
        "--allow-missing-metrics",
        action="store_true",
        help="Do not fail if a metric is missing from the report.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_argument_parser()
    args = parser.parse_args(argv)

    report_data = _load_json(args.report)
    baseline_data = _load_json(args.baseline)

    baseline_metrics = baseline_data.get("metrics")
    if not isinstance(baseline_metrics, dict):
        parser.error(
            "Baseline file must contain a 'metrics' object with threshold definitions."
        )

    report_averages = _extract_averages(report_data)

    outcomes: List[MetricOutcome] = []
    for metric_name, config in baseline_metrics.items():
        if not isinstance(config, dict):
            parser.error(
                f"Invalid configuration for metric '{metric_name}'. Expected object."
            )
        outcome = _evaluate_metric(
            metric_name,
            config,
            report_averages.get(metric_name),
            fail_on_missing=not args.allow_missing_metrics,
        )
        outcomes.append(outcome)

    for outcome in outcomes:
        print(_format_outcome(outcome))

    if args.summary_output:
        summary_payload = {
            "report": str(args.report),
            "baseline": str(args.baseline),
            "outcomes": [
                {
                    "name": outcome.name,
                    "actual": outcome.actual,
                    "passed": outcome.passed,
                    "messages": outcome.messages,
                }
                for outcome in outcomes
            ],
        }
        args.summary_output.parent.mkdir(parents=True, exist_ok=True)
        with args.summary_output.open("w", encoding="utf-8") as handle:
            json.dump(summary_payload, handle, indent=2, ensure_ascii=False)

    return 0 if all(outcome.passed for outcome in outcomes) else 1


if __name__ == "__main__":
    sys.exit(main())
