# Contributing to PneumoStabSim Professional

Thank you for helping modernise PneumoStabSim Professional. This guide distils
the expectations laid out in the [renovation master plan](../docs/RENOVATION_MASTER_PLAN.md)
and phase playbooks so contributors can stay aligned with the roadmap.

## Branch workflow

We use a short-lived branch model to keep `develop` healthy and `main` ready
for releases:

- **`main`** — release branch. Only tagged, production-ready snapshots are
  merged here after validation on `develop`.
- **`develop`** — integration branch. All feature and fix branches rebase onto
  `develop` before merging. Keep `develop` green by running the full quality
  gate before every push.
- **Feature / fix branches** — create from `develop`, use descriptive names
  (e.g. `feature/settings-manager-refactor`). Keep lifetime under two weeks.
  Rebase frequently to avoid drift and squash commits if necessary to maintain
  a clean history.
- **Hotfix branches** — if a critical production issue is found, branch from
  `main`, apply the fix, and merge back into both `main` and `develop`.

## Commit conventions

- Follow [Conventional Commits](https://www.conventionalcommits.org/) with the
  most specific scope you can derive from the modified modules
  (e.g. `feat(ui-graphics): add orbit inertia slider`).
- Reference the relevant checklist item or phase document in the commit body so
  stakeholders can trace progress against the master plan.

## Quality gates

Before opening a pull request or merging into `develop`:

1. Run `make check` to execute linters (`ruff`, `mypy`, `qmllint`) and the test
   suite (`pytest`).
2. Attach relevant artefacts (test logs, profiling reports) to the PR or
   reference them in the `docs/` reports when they impact performance or
   rendering fidelity.
3. Update documentation (master plan, phase plan, or change log) whenever the
   architecture, tooling, or workflows change.

## Opening a pull request

- Use the provided PR template and describe how the change advances the
  renovation pillars (performance, rendering fidelity, configuration
  determinism, automated quality gates, documentation parity).
- Request review from maintainers responsible for the affected subsystem (UI,
  simulation, tooling). Mention any follow-up tasks that should be tracked
  separately.

Thank you for contributing responsibly and helping keep the modernisation
project on schedule.
