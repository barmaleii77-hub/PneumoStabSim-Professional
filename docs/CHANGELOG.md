# 📦 Changelog

## [5.0.1] - 2026-12-06
### Changed
- Refreshed HDR documentation (`docs/README.md`, `assets/hdr/README.md`) with
  verified download examples, cache usage guidance, and updated references to
  the manifest-driven workflow.
- Clarified texture selection support in the documentation hub to avoid outdated
  "not supported" messaging and align instructions with the current
  `FileCyclerWidget` UX.

## [4.9.9] - 2026-06-18
### Added
- Expanded bloom controls with dedicated `HDR Maximum` and `HDR Scale` sliders so QA can tune the high dynamic range pipeline alongside the existing threshold slider; all three values persist through the graphics settings service.
- Environment panel now cycles HDR skyboxes through the reusable `FileCyclerWidget`, allows explicitly clearing the selection, and surfaces a warning badge plus tooltip when the chosen file is missing.
- Main window normalises HDR paths originating from QML, converting local file URLs and recording debug logs whenever a path cannot be resolved; this keeps the HDR asset workflow consistent across platforms.

### Notes
- The HDR feature set is delivered as part of the `hdr/bloom-tonemap` integration branch. See the documentation hub for validation checklists and troubleshooting guidance specific to the new controls.
