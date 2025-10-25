# Decisions Log

Keep this log current for all architectural, infrastructure, and delivery process decisions. Each entry should be appended chronologically with the newest items at the top.

| Date (YYYY-MM-DD) | Stakeholders | Context / Problem | Decision | Alternatives Considered | Follow-up Actions |
|-------------------|--------------|-------------------|----------|-------------------------|-------------------|
| 2025-07-02 | Architecture WG, Core Platform | Module-level singletons (`get_settings_service`) complicated testing and prevented deterministic wiring between CLI tools and the Qt bootstrap. | Adopted a process-wide `ServiceContainer` (`src/infrastructure/container.py`) with typed tokens and override support; registered the default `SettingsService` factory during import. | Continue using module-level globals with monkeypatching in tests; adopt a third-party DI framework with heavier runtime requirements. | Wire logging, event bus, and simulation services into the container; update architecture diagrams to include token ownership. |
| 2025-02-15        | Tech Leads, DevOps, QA | Align coordination cadence with readiness tracking for cross-team blocks. | Introduced weekly readiness syncs with block scoring, GitHub Projects board with epics per readiness stream, and mandated decision log upkeep. | Maintain ad-hoc updates without structured sync; monthly steering only. | Pilot the new sync starting Sprint 18, audit board usage after two iterations. |

> **How to update:** copy the template row, adjust the fields, and ensure follow-ups are reflected in upcoming sync agendas.
