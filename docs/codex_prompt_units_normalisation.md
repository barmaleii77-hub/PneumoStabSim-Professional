# Codex Prompt • Pneumatic Unit Normalisation

You are Codex (gpt-5-codex) working on the PneumoStabSim Professional project.
Ensure the pneumatic configuration pipeline stores and consumes values in SI
units (metres, Pascals, Kelvin, kilograms). User-facing widgets may expose
millimetres and bar, but persisted JSON and physics models must remain SI.

When applying changes:

1. Audit every path where pneumatic parameters travel between UI, settings
   storage, and the physics runtime. Verify that conversions between bar↔Pa and
   mm↔m are symmetrical and occur exactly once per boundary crossing.
2. Update helper classes so `collect_state()` or similar persistence entry
   points return SI payloads ready for `SettingsManager.set_category`.
3. Introduce migration-safe readers that detect legacy payloads saved in UI
   units and normalise them before validation or simulation use.
4. Cover the conversions with unit tests that exercise both SI and legacy
   values to guard against regressions.
5. Keep logging and error messages consistent with the existing Russian UI
   terminology and the renovation programme documentation.

Follow the Renovation Master Plan and phase playbooks referenced in `AGENTS.MD`
for coding standards, testing requirements, and documentation updates. Run
`make check` before committing.
