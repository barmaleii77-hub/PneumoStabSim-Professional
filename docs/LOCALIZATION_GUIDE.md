# Localization Guide

This guide explains how to add new user-facing text to the QML interface and keep the translation catalogues in `assets/i18n/` up to date.

## File layout

- **QML sources**: `assets/qml/` contains all user-facing strings. Use `qsTr("…")` or `qsTrId("…")` for any text that appears on screen.
- **Translation catalogues**: `assets/i18n/` stores the Qt Linguist `.ts` files per locale (`graphics_en.ts`, `graphics_ru.ts`). Compiled `.qm` artefacts (when needed) and JSON summaries are produced under `reports/localization/` but are ignored by Git.
- **Reports**: `reports/localization/` is a scratch directory. Each invocation of the maintenance script regenerates the inventory and status summaries for local inspection only. Do not commit these artefacts.

## Adding a new string

1. Wrap the new text in `qsTr("…")` (or `qsTrId("…")` when using structured identifiers) inside the QML file.
2. Run the translation maintenance script to refresh the catalogues:

   ```bash
   python tools/update_translations.py
   ```

   The script executes `lupdate` to extract strings, `lrelease` to build `.qm` files, and regenerates the reports in `reports/localization/`. The generated files stay untracked—delete them if you need a clean workspace.
3. Open the updated `.ts` files in Qt Linguist (or edit them manually) and provide translations for every new source string.
4. Re-run the script to ensure all entries are translated. The command will fail if any `qsTr`/`qsTrId` usages are missing from the catalogues or if translations remain unfinished.

## CI validation

The `make check` aggregate target now calls:

```bash
python tools/update_translations.py --check
```

This mode skips the `lupdate`/`lrelease` steps and verifies that every `qsTr`/`qsTrId` usage has an entry in the `.ts` files. Pass `--fail-on-unfinished` locally if you also want the command to fail when translations are still marked as unfinished. The same check runs in GitHub Actions (`.github/workflows/ci.yml`) so pushes and pull requests cannot regress localization coverage.

## Troubleshooting

- **Missing Qt tools**: If the script cannot locate `lupdate`/`lrelease`, install the Qt Linguist tools or point to custom binaries using `--lupdate` / `--lrelease`.
- **Reports differ locally vs CI**: Delete the contents of `reports/localization/` and re-run the script without `--check` to rebuild them. Generated artefacts should never be committed.
- **Strings not detected**: Ensure the text is wrapped in `qsTr`/`qsTrId` without dynamic concatenation that hides the literal at parse time.

By following this workflow the translation files stay synchronized with the QML UI and automated checks prevent regressions.
