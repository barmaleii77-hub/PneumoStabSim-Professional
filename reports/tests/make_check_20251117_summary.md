# Make Check Run — 2025-11-17

- **Command:** `make check`
- **Outcome:** ❌ Failed at preflight stage.
- **Failure detail:** `uv run --locked` aborted because the existing `uv.lock` requires regeneration; the command terminated before executing linting or tests.
- **Relevant console excerpt:**
  - `error: The lockfile at uv.lock needs to be updated, but --locked was provided. To update the lockfile, run uv lock.`
- **Next steps:** regenerate `uv.lock` (`uv lock`) and rerun `make check` to capture lint, type-check, QML, and pytest results.
