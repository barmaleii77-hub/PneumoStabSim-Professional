# Settings audit – sample report

This sample illustrates the output of `python -m src.tools.settings_audit` when
comparing a runtime configuration against the repository baseline.

## Summary

| Change | Count |
| --- | ---: |
| Added | 2 |
| Removed | 1 |
| Changed | 3 |
| Type | 0 |

## Details

- **Changed** `metadata.version`: `"1.0"` → `"1.1"`
- **Changed** `current.graphics.exposure`: `0.5` → `0.7`
- **Added** `current.graphics.profiles[2]` = `"studio-night"`
- **Added** `current.pneumatic.receiver_pressure_kpa` = `480`
- **Removed** `current.simulation.debug_mode` (was `false`)
