# Governance Calendar and Operating Rituals

This document codifies the recurring coordination rhythm for the PneumoStabSim Professional renovation programme.
It fulfills section 13 of the master plan by defining the meetings, owners, and expected artefacts that keep the
multidisciplinary team aligned.

## Calendar Overview

| Cadence | Meeting | Participants | Primary Goals | Outputs |
| --- | --- | --- | --- | --- |
| Weekly (Tuesday 15:00 UTC) | Architecture Sync | Architecture working group, service owners, diagnostics lead | Review design proposals, unblock cross-team dependencies, capture decisions requiring documentation. | Updated action items, ADR candidates, notes appended to `docs/DECISIONS_LOG.md`. |
| Bi-weekly (Thursday 10:00 UTC, odd weeks) | Sprint Review & Readiness Check | Engineering manager, product manager, QA lead, release engineer | Track sprint burndown, validate acceptance criteria, surface release blockers, align on demo narrative. | Refreshed status in master plan sections 5–7, sprint notes stored under `reports/governance/`. |
| Monthly (First Monday 16:00 UTC) | Release Readiness Board | Engineering leadership, support lead, SRE, documentation owner | Confirm packaging status, dependency updates, telemetry coverage, and support handoff materials. | Minutes uploaded to `docs/operations/release_notes_drafts/`, go/no-go decision, action register updates. |
| Quarterly (Final week) | Risk Review & Strategy Retro | Executive sponsor, engineering manager, architecture lead, QA representative | Evaluate systemic risks, review mitigation progress, adjust roadmap priorities, capture lessons learned. | Updated `docs/operations/risk_register.md`, retro summary in `reports/governance/quarterly-retro-<YYYY>-Q<q>.md`. |

## Roles and Responsibilities

- **Facilitator** – Rotates quarterly between architecture and product leads; prepares agendas and moderates discussions.
- **Scribe** – Assigned per meeting from QA or release engineering; ensures notes and follow-up items are recorded within 24 hours.
- **Timekeeper** – Delegated to the diagnostics lead to enforce agenda timing and flag overflow topics.

## Agenda Templates

### Architecture Sync
1. Hot issues review (5 minutes)
2. Design RFC walkthroughs (15 minutes)
3. Cross-team dependency board (10 minutes)
4. Action item review & decision log updates (5 minutes)

### Sprint Review & Readiness Check
1. Demo of completed work and verification evidence
2. Status of quality gates (`make check`, CI pipelines)
3. Outstanding risks or blocked stories
4. Upcoming sprint objectives and capacity adjustments

### Release Readiness Board
1. Packaging artifact status (MSI/AppImage) and checksum verification
2. Dependency review outcomes (security, compatibility)
3. Telemetry and on-call readiness (dashboards, runbooks)
4. Communication plan (release notes, stakeholder briefing)

### Risk Review & Strategy Retro
1. Review top risks from the register and mitigation effectiveness
2. New risks identified during the quarter
3. Strategic adjustments (roadmap, staffing, tooling)
4. Key learnings and action plan for next quarter

## Artefact Management

- Store raw meeting notes in `reports/governance/` with ISO date filenames.
- Summaries that influence architecture or process decisions must be reflected in the master plan and decision log within two business days.
- Action items require explicit owners and target dates; track them in the shared issue tracker and reference ticket numbers in follow-up notes.

## Escalation Path

1. Meeting facilitator escalates unresolved blockers to the engineering manager within 24 hours.
2. Engineering manager informs executive sponsor for cross-organisational issues exceeding a one-week resolution window.
3. Critical release risks trigger an immediate ad-hoc readiness huddle involving release engineering, SRE, and product leadership.
