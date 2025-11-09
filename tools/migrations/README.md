# Settings migration helpers

The renovation tooling expects contributors to stage backwards-compatible
changes to `config/app_settings.json` as explicit JSON migrations.  The
canonical runner lives in `src.tools.settings_migrate`, but this directory hosts
thin wrappers and documentation to make migrations easier to discover from the
`tools/` namespace.

## Running migrations locally

```bash
make uv-run CMD="python tools/migrations/apply.py --settings config/app_settings.json --migrations config/migrations --in-place --verbose"
```

The helper mirrors the command line options of
`python -m src.tools.settings_migrate`.  Prefer invoking it through
`make uv-run` so the virtual environment is prepared automatically.

## Adding a new migration

1. Create a new JSON descriptor in `config/migrations/` following the naming
   convention `NNNN_description.json`.
2. Define the migration metadata and operations as described in
   `docs/SETTINGS_ARCHITECTURE.md`.
3. Execute the command above to apply the migration to your working copy of
   `config/app_settings.json`.
4. Run `make check` to confirm schema validation and regression tests pass.
