# Renovation Phase 0 – Discovery Plan

## Objectives
- Build a complete inventory of code, assets, and configuration entry points.
- Establish baseline metrics for performance, rendering quality, and simulation correctness.
- Surface blockers early (licensing, missing dependencies, tooling gaps) with proposed mitigations.

## Entry Criteria
- Core stakeholders (tech lead, QA lead, product representative) assigned.
- Access to existing documentation and prior test artifacts confirmed.
- Diagnostic tooling (scripts in `tools/` and `scripts/`) validated on local machine.

## Work Breakdown Structure
1. **Repository Mapping**
   - Run `scripts/cleanup_duplicates.py --audit` and export findings to `docs/audits/duplicates_phase0.csv`.
   - Generate dependency graph via `pipdeptree` and store snapshot in `docs/audits/python_dependencies_phase0.md`.
   - Document Qt/QML modules discovered by `qml_diagnostic.py` into `docs/audits/qml_inventory_phase0.md`.
2. **Runtime Profiling**
   - Execute `quick_performance_test.py` and capture GPU/CPU stats.
   - Record render outputs (screenshots, logs) for comparison in Phase 3.
3. **Stakeholder Interviews**
   - Collect pain points from designers, QA, support; summarize outcomes and priorities.
   - Align on modernization success criteria refinement.
4. **Risk & Constraint Register**
   - Draft initial risk matrix (technical, schedule, compliance) with severity and mitigation owners.
   - Identify external dependencies (hardware, licenses) and verify availability.

## Deliverables
- `docs/audits/` folder populated with inventories and dependency snapshots.
- Updated risk register entry in [Phase 0 plan log](#execution-log).
- Kickoff readout presented to stakeholders with action items for Phase 1.

## Exit Criteria
- All inventories reviewed and validated by tech lead.
- No high-severity unknowns remain; each risk has an assigned mitigation path.
- Baseline metrics recorded and approved as reference for future regression checks.

## RACI Snapshot
- **Responsible:** Modernization tech lead, diagnostics engineer.
- **Accountable:** Engineering manager.
- **Consulted:** QA lead, product representative.
- **Informed:** Executive sponsor, support lead.

## Execution Log
Maintain daily notes in this section. Use dated subheadings and include links to evidence artifacts.

### 2025-02-28 – Documentation alignment
- Renamed the root agent operations manual to `AGENTS.MD` to match repository conventions and ensure assistants can locate the canonical workflow guidance quickly.

### 2025-02-24 – Initial repository inventory
- Captured duplicate default configuration files flagged by `cleanup_duplicates.py` and recorded the status in [`docs/audits/duplicates_phase0.md`](audits/duplicates_phase0.md).
- Generated the Python dependency graph snapshot using `python -m pipdeptree`; archived analysis in [`docs/audits/python_dependencies_phase0.md`](audits/python_dependencies_phase0.md).
- Executed `python qml_diagnostic.py --help` to validate QML entrypoints and stored findings in [`docs/audits/qml_inventory_phase0.md`](audits/qml_inventory_phase0.md).
