"""Verify that all GitHub Actions workflows pin actions to commit SHAs.

This guard prevents accidentally upgrading shared Actions by tag, which would
reintroduce the security concern highlighted in PR #922.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1] / ".github" / "workflows"

_USES_PATTERN = re.compile(r"uses:\s*(?P<action>[^\s@]+)@(?P<ref>[^\s]+)")
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def _is_local_reference(action: str, ref: str) -> bool:
    """Return True for references that are exempt from pinning requirements."""

    if action.startswith("./"):
        return True
    if action.startswith("docker://"):
        return True
    if ref.startswith("${{"):
        # GitHub currently disallows expressions in `uses`, but tolerate them in
        # case a composite action forwards a reference via an environment value.
        return True
    return False


def check_workflow(path: Path) -> list[str]:
    """Return a list of human-readable error descriptions for ``path``."""

    errors: list[str] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        match = _USES_PATTERN.search(line)
        if not match:
            continue
        action = match.group("action")
        ref = match.group("ref")
        if _is_local_reference(action, ref):
            continue
        if _COMMIT_PATTERN.fullmatch(ref):
            continue
        relative_path = path.relative_to(WORKFLOW_ROOT.parent)
        errors.append(f"{relative_path}:{line_number}: {action}@{ref}")
    return errors


def main() -> int:
    if not WORKFLOW_ROOT.exists():
        print("Workflow directory not found; skipping action pinning check.")
        return 0

    failures: list[str] = []
    for workflow in sorted(WORKFLOW_ROOT.glob("*.yml")) + sorted(
        WORKFLOW_ROOT.glob("*.yaml")
    ):
        failures.extend(check_workflow(workflow))

    if failures:
        print(
            "All GitHub Actions must be pinned to full-length commit SHAs. "
            "Update the following references:",
            file=sys.stderr,
        )
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print("All GitHub Actions workflows use commit SHA pins.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
