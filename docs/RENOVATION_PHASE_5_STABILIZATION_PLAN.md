# Renovation Phase 5 – Stabilization Plan

## Objectives
- Maintain application quality post-release through monitoring, support, and continuous improvement.
- Institutionalize feedback loops from users, QA, and automated telemetry.
- Keep documentation, training, and maintenance workflows current.

## Entry Criteria
- Release candidate approved and deployed to target distribution channels.
- Support and operations teams onboarded with updated runbooks.
- Telemetry and logging infrastructure validated in staging/production.

## Work Breakdown Structure
1. **Monitoring & Telemetry**
   - Configure centralized log aggregation; define retention and access controls.
   - Set up dashboards tracking crash rates, frame time metrics, and feature usage.
   - Establish on-call rotation and escalation paths documented in `docs/operations/oncall.md`.
2. **Feedback Processing**
   - Run weekly triage sessions for bugs, UX issues, and performance regressions.
   - Maintain prioritized backlog with SLA targets for fixes.
   - Share insights with design/product for roadmap adjustments.
3. **Maintenance & Updates**
   - Schedule monthly dependency reviews (Python packages, Qt patches).
   - Automate security scanning (pip-audit, GitHub Dependabot) and integrate into CI.
   - Document patch release process, including branching strategy and release notes template.
4. **Knowledge Management**
   - Keep MkDocs site versioned; archive outdated guides with changelog references.
   - Host brown-bag sessions for new features and architectural deep dives.
   - Capture learnings in ADRs or postmortem templates stored under `docs/adr/`.

## Deliverables
- Operational dashboards and runbooks published.
- Monthly maintenance calendar with assigned owners.
- Feedback backlog curated and linked to roadmap tracker.

## Exit Criteria
- Incident response metrics (MTTA, MTTR) meeting defined targets for two consecutive months.
- No high-severity issues older than SLA window.
- Documentation and training materials reviewed and signed off quarterly.

## Milestones & Timeline
- **Sprint 23:** Stand up telemetry dashboards, define alert thresholds, and
  document on-call rotations.
- **Sprint 24:** Formalise feedback triage process, integrate with issue tracker,
  and publish SLA matrix.
- **Sprint 25:** Automate dependency/security reviews and capture maintenance
  calendar with owners.
- **Sprint 26+:** Conduct retrospectives, update ADRs, and hand off long-term
  stewardship materials.

## Dependencies
- Stable release artefacts and packaging process from Phase 4.
- Access to monitoring stack (log aggregation, metrics backend).
- Collaboration with support/product to align SLAs and communication cadence.

## Risk Register
| Risk | Impact | Probability | Mitigation |
| --- | --- | --- | --- |
| Telemetry tooling unavailable in production | High | Medium | Secure infrastructure commitment before release; provide fallback local collectors. |
| Feedback backlog grows without triage discipline | High | Medium | Schedule weekly triage with rotating facilitators and published action items. |
| Maintenance cadence slips due to resource constraints | Medium | Medium | Publish maintenance calendar with executive sponsorship; automate reminders. |

## Metrics & Evidence
- MTTA/MTTR dashboards exported monthly to `reports/operations/stability_metrics.csv`.
- Feedback backlog burndown tracked in `docs/operations/risk_register.md` with
  cross-links to issues.
- Dependency review logs stored under `reports/operations/dependency_audits/`.

## RACI Snapshot
- **Responsible:** Support lead, site reliability engineer.
- **Accountable:** Engineering manager.
- **Consulted:** Product manager, QA lead.
- **Informed:** Executive sponsor, design lead.

## Execution Log
Use this log for incident summaries, release retrospectives, and KPI snapshots.

### 2025-10-10 – Telemetry pilot and on-call readiness
- Deployed telemetry collectors to staging, forwarding structured logs to the shared `reports/operations/stability_metrics.csv`
  pipeline for MTTA/MTTR baselining.
- Drafted the first revision of `docs/operations/oncall.md`, including escalation matrix and contact rotations approved by the
  support lead.
