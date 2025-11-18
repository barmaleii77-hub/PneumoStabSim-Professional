from __future__ import annotations

from pathlib import Path

import pytest

from tools.quality import skip_policy


def _junit_report(tmp_path: Path, message: str) -> Path:
    xml = tmp_path / "report.xml"
    xml.write_text(
        """
        <testsuites>
          <testsuite name="sample" tests="1">
            <testcase classname="demo" name="test_example">
              <skipped message="{message}" />
            </testcase>
          </testsuite>
        </testsuites>
        """.format(message=message),
        encoding="utf-8",
    )
    return xml


def test_collect_skipped_tests_extracts_reason(tmp_path: Path) -> None:
    xml = _junit_report(tmp_path, "missing display backend")

    entries = skip_policy.collect_skipped_tests([xml], project_root=tmp_path)

    assert len(entries) == 1
    assert entries[0].case == "demo.test_example"
    assert entries[0].message == "missing display backend"


def test_partition_skipped_tests_respects_expected_token(tmp_path: Path) -> None:
    xml = _junit_report(tmp_path, "manual preview [pytest-skip-ok]")
    cases = skip_policy.collect_skipped_tests([xml], project_root=tmp_path)

    acknowledged, unexpected = skip_policy.partition_skipped_tests(cases)

    assert [case.case for case in acknowledged] == ["demo.test_example"]
    assert not unexpected


def test_evaluate_skip_policy_blocks_unjustified_skips(tmp_path: Path) -> None:
    xml = _junit_report(tmp_path, "missing runtime")
    entries = skip_policy.collect_skipped_tests([xml], project_root=tmp_path)
    context = skip_policy.SkipPolicyContext(
        running_in_ci=True,
        allow_skips=False,
        justification="",
        summary_path=None,
        step_summary_path=None,
        project_root=tmp_path,
    )

    violation = skip_policy.evaluate_skip_policy(entries, context=context)

    assert violation is not None
    assert "skipped test" in violation


def test_main_exits_on_unexpected_skips(tmp_path: Path) -> None:
    xml = _junit_report(tmp_path, "undocumented skip")
    summary = tmp_path / "skipped.md"

    with pytest.raises(SystemExit):
        skip_policy.main(
            [
                "--ci",
                "--junitxml",
                str(xml),
                "--summary",
                str(summary),
            ]
        )

    assert summary.exists()
