# Visual Studio Insiders Setup

This document describes how the Visual Studio Insiders profile is provisioned for
PneumoStabSim Professional and which automation is executed when the solution is
opened.

## Overview

Opening `PneumoStabSim-Professional.Insiders.sln` or the corresponding `.pyproj`
triggers the custom MSBuild target `PrepareVisualStudioInsidersEnvironment`.
This target runs `tools/visualstudio/initialize_insiders_environment.ps1`, which
performs the following actions:

1. **Normalize terminal encoding** so Windows Terminal and Visual Studio's
   PowerShell consoles run in UTF-8 with correct handling of Russian text and
   multiline output.
2. **Validate Visual Studio components** using
   `tools/visualstudio/ensure_vs_components.ps1`. Missing workloads declared in
   `PneumoStabSim-Professional.insiders.vsconfig` are installed automatically
   (when the Visual Studio Installer is present) and an update check for the
   Insiders channel is issued.
3. **Bootstrap the Python toolchain** by creating `.venv` if necessary and
   upgrading `pip`, `setuptools`, and `wheel`. All dependency files (`requirements.txt`,
   `requirements-dev.txt`, `current_requirements.txt`) are installed eagerly.
4. **Provision Qt paths and simulator variables** into
   `.vs/insiders.environment.json` so every launch configuration inherits the
   same runtime environment.
5. **Regenerate launcher helpers** ensuring that manual execution through
   PowerShell uses the same environment variables and encoding safeguards.
6. **Run the PneumoStabSim quality gate** by invoking
   `python -m tools.ci_tasks verify` inside the freshly provisioned virtual
   environment. This mirrors `make check` (ruff, mypy, qmllint, pytest) so that
   any environment drift is caught as soon as the solution opens.
7. **Synchronise GitHub Copilot metadata** via
   `tools/visualstudio/sync_copilot_profile.ps1`, exposing a rich project
   description to Copilot for Visual Studio.

## Launch Profiles

Visual Studio reads `.vs/insiders.environment.json` and `Properties/launchSettings.json`
when starting the simulator, tests, or tooling commands. The environment file now
includes additional safeguards such as `PYTHONUTF8`, `PYTHONIOENCODING`, and
`LC_ALL` to guarantee deterministic encoding behaviour. PowerShell specific
hardening (`POWERSHELL_UPDATECHECK=Off`, `POWERSHELL_TELEMETRY_OPTOUT=1`) prevents
startup pauses or modal prompts in embedded terminals.

## Copilot Integration

The Copilot metadata is written to `%APPDATA%\GitHubCopilot\PneumoStabSim-Professional-insiders.json`.
A pointer to this file is also exposed through the `GITHUB_COPILOT_METADATA_PATH`
environment variable for Visual Studio sessions. The metadata file is generated
from `tools/visualstudio/copilot_insiders_profile.json` and summarises entry
points, documentation, and testing commands so Copilot has immediate context when
suggesting completions.

## Manual Invocation

Developers can prepare or refresh the environment without opening Visual Studio
by running:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/visualstudio/initialize_insiders_environment.ps1
```

To launch the simulator with the Insiders profile from the command line use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/visualstudio/launch_insiders.ps1
```

Both scripts enforce UTF-8 encoding, apply the QML/Qt runtime paths, and ensure
Copilot metadata is in sync.

## Runtime Guardrails

The WPF host now invokes `EnvironmentPreparationService` during startup. The service ensures
that the Insiders toolchain is provisioned even when the solution is launched outside the
PowerShell bootstrap scripts. It performs the following steps before the application window
appears:

1. Creates (or refreshes) the `.venv` interpreter using the most recent Python 3.13 installation.
2. Installs dependencies from `requirements.txt`, `requirements-dev.txt`, and `current_requirements.txt`
   only when their contents change.
3. Generates `.vs/insiders.environment.json` through `tools/visualstudio/generate_insiders_environment.py`
   and applies the resulting variables to the current process (including `QT_PLUGIN_PATH`,
   `QML2_IMPORT_PATH`, and `PNEUMOSTABSIM_PYTHON`).
4. Emits structured warnings or blocking errors to the Visual Studio Output window and an on-screen
   dialog if provisioning fails.

These checks make it safe to run the simulator from Visual Studio Insiders without manually running
the provisioning scripts beforehand.
