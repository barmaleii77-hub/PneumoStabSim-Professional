# Contributor checklist

This quick-reference guide complements [the full contribution guide](../.github/CONTRIBUTING.md)
and distils the non-negotiable steps every patch must follow.

## Environment preparation

- [ ] Run `make uv-sync` to materialise the Python 3.13 toolchain and ensure all
      project-specific dependencies are available.
- [ ] Run `make check` before every commit or pull request to execute the full
      quality gate (`ruff`, `mypy`, `pytest`, `qmllint`).

## Working with configuration

- [ ] Declare every new tunable value in `config/app_settings.json`; never hard
      code defaults in the Python or QML layers.
- [ ] Update the matching JSON Schema under
      `schemas/settings/app_settings.schema.json` so validation stays in lockstep
      with the configuration file.
- [ ] When modifying existing settings, stage the change as a migration by
      adding a descriptor to `config/migrations/` and applying it with
      `python tools/migrations/apply.py` (ideally via
      `make uv-run CMD="python tools/migrations/apply.py --in-place --verbose"`).

## Source control hygiene

- [ ] Format commit messages using the [Conventional Commits](https://www.conventionalcommits.org/)
      specification with the most specific scope you can justify.
- [ ] Install the repository's pre-commit hooks (`pre-commit install --hook-type
      pre-commit --hook-type pre-push --hook-type commit-msg`) so commit message
      and quality checks run automatically.
- [ ] Reference the relevant renovation plan item or checklist entry in the
      commit body to preserve traceability.
