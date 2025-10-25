# Risk Register

This register tracks the key delivery and operational risks for PneumoStabSim Professional.
It complements the governance calendar by ensuring each risk has an owner, mitigation strategy,
and review cadence. Update this file during the quarterly risk review and whenever a high-impact
item is discovered.

## How to Use

1. Add new risks to the table below. Keep descriptions concise but actionable.
2. Update the *Status* column during governance touchpoints (weekly/bi-weekly/monthly/quarterly).
3. Reference related master plan sections, GitHub issues, or documentation anchors in the *Links* column.
4. Move retired risks to the archive section at the bottom to preserve historical context.

## Active Risks

| ID | Risk Description | Impact | Probability | Mitigation Strategy | Owner | Status | Links |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-001 | Dependency lockfile not yet produced; diverging `requirements*.txt` files can break reproducibility. | High | Medium | Finalise `uv lock` workflow, publish lockfile, document update cadence in `docs/ENVIRONMENT_SETUP.md`. | DevOps lead | Mitigation in progress | Master Plan §3.2, Issue #412 |
| R-002 | Graphics panel refactor relies on manual testing; regression bugs may slip without UI automation. | Medium | Medium | Expand `pytest-qt` coverage for graphics tabs, enable screenshot baselines, tie results into `make check`. | QA automation lead | Monitoring | Master Plan §7.1, Test Plan draft |
| R-003 | CI workflows absent; quality gates run manually causing inconsistent enforcement. | High | High | Implement GitHub Actions `ci.yml` and `nightly.yml`, gate merges on `make check`, store artefacts. | Engineering manager | High priority | Master Plan §7.2 |
| R-004 | Incident response process undocumented; on-call teams risk delayed mitigation. | Medium | Low | Complete telemetry dashboards, publish on-call runbook, rehearse escalation via tabletop exercise. | Support lead | Planned | Phase 5 plan §1 |
| R-005 | Legacy `.sln/.csproj` assets cause confusion about supported platforms. | Low | Medium | Confirm deprecation, archive or remove assets, document outcome in `docs/CHANGELOG_MODULAR.md`. | Architecture lead | Under review | Master Plan §9.2 |

## Risk Archive

| ID | Risk Description | Retirement Reason | Notes |
| --- | --- | --- | --- |
| – | – | – | Use this section to log resolved risks once mitigation holds for two review cycles. |
