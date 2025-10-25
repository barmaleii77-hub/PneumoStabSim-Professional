# On-Call Runbook

## Purpose
Establish a predictable escalation path for Phase 5 stabilization efforts, ensuring telemetry alerts and user-reported
incidents receive timely attention.

## Rotation Structure
- **Primary responder:** Rotates weekly among support engineers; handoff occurs every Monday 09:00 UTC.
- **Secondary responder:** Senior engineer providing architectural support during escalations; rotates bi-weekly.
- **Manager on duty:** Engineering manager available for business-hour escalations and stakeholder communications.

## Escalation Workflow
1. Alert triggers via telemetry dashboard (`reports/operations/stability_metrics.csv`) or support ticket.
2. Primary responder triages within 15 minutes, acknowledging the incident in the shared channel.
3. If mitigation exceeds 30 minutes or production impact persists, escalate to secondary responder and manager on duty.
4. Record incident summary, resolution steps, and follow-up tasks in `docs/operations/incident_logs/` within 24 hours.

## Contact Matrix
| Role | Contact | Notes |
| --- | --- | --- |
| Primary responder | `oncall-primary@example.com` | Update weekly via automation script.
| Secondary responder | `oncall-secondary@example.com` | Provide architectural guidance and approve hotfixes.
| Manager on duty | `eng-manager@example.com` | Coordinate stakeholder updates.

## Handoff Checklist
- Review open incidents and outstanding follow-up tasks.
- Confirm telemetry dashboards and alerting endpoints are operational.
- Update contact matrix and escalation paths if staffing changes occurred.

## Continuous Improvement
- Schedule monthly retrospectives to adjust alert thresholds and tooling.
- Capture lessons learned in `docs/DECISIONS_LOG.md` or dedicated postmortems.
- Ensure dependency on-call scripts remain compatible with `tools/operations/` automation utilities.
