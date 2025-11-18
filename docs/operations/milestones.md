# Rolling Milestone Schedule

This document maintains the six-week outlook referenced in the master plan's
Execution Roadmap. It is reviewed during the weekly governance sync alongside
`docs/operations/phase_burndown.md` and the risk register to ensure priorities
stay aligned across teams.

## Update Cadence
- Refresh the table every Friday before the governance sync.
- Link each milestone to supporting evidence (PRs, reports, checklist updates).
- Note owners using role titles to keep responsibility clear even if personnel
  change.

## Six-Week Outlook (Weeks 47–52, 2025)

| Week | Dates (ISO) | Primary Focus | Key Deliverables | Owner | Dependencies | Evidence Links |
| --- | --- | --- | --- | --- | --- | --- |
| 47 | 2025-11-17 → 2025-11-23 | Finalise infrastructure container extensions | Simulation runner + logging factories registered; updated `docs/architecture/service_container.md` | Tech Lead | Phase 2 module boundaries stable; container tests green | [Phase 2 Plan](../RENOVATION_PHASE_2_ARCHITECTURE_AND_SETTINGS_PLAN.md) |
| 48 | 2025-11-24 → 2025-11-30 | GPU profiler overlay pilot | Profiler toggle integrated into diagnostics panel; baseline report `reports/performance/ui_phase3_profiler.md` | UI/Graphics Lead | Week 47 container updates; Qt 6.10 profiler tooling | [Phase 3 Plan](../RENOVATION_PHASE_3_UI_AND_GRAPHICS_PLAN.md) |
| 49 | 2025-12-01 → 2025-12-07 | Coverage gate rehearsal | Staging branch runs strict `make check`; coverage snapshot `reports/quality/coverage_phase4_pilot.json` | QA Automation Lead | Week 48 profiler check signed off; CI capacity reserved | [Phase 4 Plan](../RENOVATION_PHASE_4_TESTING_PACKAGING_CLEANUP_PLAN.md) |
| 50 | 2025-12-08 → 2025-12-14 | Packaging readiness alignment | Draft release checklist `docs/release/packaging_playbook.md` updated; packaging dry run artefacts reviewed | Release Engineer | Week 49 coverage rehearsal completed; Qt setup verified | [Phase 4 Plan](../RENOVATION_PHASE_4_TESTING_PACKAGING_CLEANUP_PLAN.md) |
| 51 | 2025-12-15 → 2025-12-21 | Repository cleanup wave | Archive report migration into `archive/2025-12/`; redundant scripts flagged for removal | Documentation Lead | Week 50 packaging notes; redundant files audit (2025-10-25) | [Cleanup Report](../../reports/cleanup/2025-10-25/) |
| 52 | 2025-12-22 → 2025-12-28 | Stabilization playbook rehearsal | On-call drill recorded in `docs/operations/oncall.md`; stability metrics snapshot shared | Release Manager | Week 51 cleanup status; telemetry pilot (2025-10-10) | [Phase 5 Plan](../RENOVATION_PHASE_5_STABILIZATION_PLAN.md) |
| 53 | 2025-12-29 → 2026-01-04 | Finalize release communications and backlog merge-down | Confirm upstream target for `work` branch, close out straggling Phase 3/4 items, publish release notes draft in `docs/release/` | Release Engineering | Upstream remote configured; Week 52 stabilization drill | [Governance](governance.md) |

## Notes
- If priorities change mid-sprint, record the decision in `docs/DECISIONS_LOG.md`
  and update this schedule immediately.
- Align milestone status updates with the governance agenda to keep stakeholders
  informed of trade-offs and risk adjustments.
- Confirm the upstream for `work` before Week 53 to avoid blocking merge-down
  and release packaging tasks.
