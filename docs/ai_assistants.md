# AI Assistant Usage Guide

This guide documents how to collaborate with AI coding assistants while working on **PneumoStabSim Professional**.
It aligns with the Renovation Master Plan objectives for tooling, privacy, and reproducibility.

## 1. Collaboration Principles
- Treat assistants as pair-programmers: keep tasks focused and provide clear context.
- Prefer incremental pull requests that keep tests and linters green.
- Use the Conventional Commits format when submitting automated patches.

## 2. Privacy & Security
- Never paste customer, license, or hardware identifiers into prompts.
- Avoid sharing internal access tokens. Store credentials exclusively in the `.env` file.
- Strip proprietary paths or filenames when discussing unreleased features outside this repository.

## 3. Environment Expectations
- Reference the canonical tooling stack: Python 3.13, Qt/PySide 6.10, Ruff, MyPy, and pytest.
- Mention the `activate_environment.(sh|ps1)` scripts to bootstrap locale-safe environments.
- When discussing dependencies, point to `pyproject.toml` and `requirements.txt` as the sources of truth.

## 4. Coding Standards
- Follow `docs/CODE_STYLE.md` and the linters enforced via `ruff.toml` and `mypy.ini`.
- Prefer explicit imports and typed interfaces; avoid wildcard imports in both Python and QML.
- Confirm UI-related changes in QML with screenshots or GIFs when feasible.

## 5. Logging & Diagnostics
- Encourage assistants to leverage `src/diagnostics` utilities for structured logging and warning capture.
- Highlight the requirement to keep `logs/` out of source control as per `.gitignore`.
- Mention the JSON settings schema under `config/app_settings.schema.json` when discussing configuration.

## 6. Testing Workflow
- Default recommendation: run `pytest` and `ruff` before finalizing any patch.
- For Qt integrations, suggest `pytest -m "not slow"` and targeted smoke tests located in `tests/ui`.
- Capture flaky test output into `reports/` for later triage rather than discarding logs.

## 7. Documentation Practices
- Update relevant guides (`START_HERE.txt`, `QUICKSTART.md`, etc.) when workflows change.
- Keep change logs in `docs/CHANGELOG_MODULAR.md` synchronized with shipped features.
- Link back to this document when onboarding new tooling or AI workflows.

Maintaining these practices ensures consistent, auditable collaboration across human and AI contributors.
