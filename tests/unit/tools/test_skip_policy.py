from __future__ import annotations

import os
from pathlib import Path

from tools.quality import skip_policy


def _build_context(
    tmp_path: Path, *, allow: bool = False, reason: str = ""
) -> skip_policy.SkipPolicyContext:
    env = os.environ.copy()
    env.update(
        {
            "CI": "1",
            "PSS_ALLOW_SKIPPED_TESTS": "1" if allow else "0",
            "CI_SKIP_REASON": reason,
        }
    )
    return skip_policy.resolve_skip_policy_context(
        env=env, summary_path=tmp_path / "skipped.md", project_root=tmp_path
    )


def test_skip_policy_flags_unexpected(tmp_path: Path) -> None:
    entries = [
        skip_policy.SkippedTestCase(
            suite="unit",
            case="tests.test_example::test_case",
            message="missing dependency",
            source=tmp_path / "junit.xml",
        )
    ]
    summary = skip_policy.write_skipped_summary(
        entries, summary_path=tmp_path / "skipped.md", project_root=tmp_path
    )
    context = _build_context(tmp_path)

    violation = skip_policy.evaluate_skip_policy(
        entries, context=context, summary_path=summary
    )

    assert violation is not None
    assert "PSS_ALLOW_SKIPPED_TESTS" in violation


def test_skip_policy_allows_acknowledged_skips(tmp_path: Path) -> None:
    entries = [
        skip_policy.SkippedTestCase(
            suite="ui",
            case="tests.test_example::test_case",
            message=f"blocked driver {skip_policy.EXPECTED_SKIP_TOKEN}",
            source=tmp_path / "junit.xml",
        )
    ]
    summary = skip_policy.write_skipped_summary(
        entries, summary_path=tmp_path / "skipped.md", project_root=tmp_path
    )
    context = _build_context(tmp_path, allow=True, reason="Windows GPU maintenance")

    violation = skip_policy.evaluate_skip_policy(
        entries, context=context, summary_path=summary
    )

    assert violation is None
    assert summary is not None and summary.exists()
