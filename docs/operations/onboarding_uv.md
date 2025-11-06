# Onboarding Transcript – uv Environment Bootstrap

This quick-reference transcript captures the canonical steps for preparing a
PneumoStabSim Professional development workstation using the uv toolchain. The
playbook covers Windows (PowerShell 7), Linux, and Windows Subsystem for Linux
(WSL) hosts. Share this document with new engineers and support staff so the
Phase 1 environment objectives remain reproducible.

## 1. Prerequisites

- Git 2.45 or newer with credential helper configured.
- Python 3.13 installed or accessible via `pyenv` / system package manager.
- PowerShell 7.4+ (for Windows instructions) or a modern Bash shell (Linux &
  WSL).
- Qt 6.10 prerequisites: ~10 GB of free disk space and network access to the Qt
  download CDN.

## 2. Repository Checkout

```bash
# Clone the repository with submodules (none required today, but future-proof).
git clone https://github.com/YourOrg/PneumoStabSim-Professional.git
cd PneumoStabSim-Professional
```

> ℹ️  If cloning inside corporate VPNs, ensure the GitHub Enterprise hostname is
> whitelisted; otherwise prefer SSH and personal access tokens.

## 3. Bootstrap uv

All platforms run the bootstrap helper once. The script installs uv if it is not
found on `PATH` and prepares the managed virtual environment directory.

```bash
python scripts/bootstrap_uv.py
```

- The helper will download uv from `astral-sh/uv` releases, verifying checksums
  before extraction.
- For Windows hosts using the Microsoft Store Python distribution, launch the
  command inside a PowerShell 7 terminal to avoid execution policy prompts.

## 4. Synchronise Dependencies

### PowerShell 7 (Windows)

```powershell
# Ensure execution policy permits running our helpers in the current session.
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Activate Qt-aware environment variables and install dependencies.
./activate_environment.ps1
# Ensure uv-run commands inherit the environment.
./scripts/load_cipilot_env.ps1
make uv-sync
```

> ℹ️ `scripts/load_cipilot_env.ps1` нужно запускать в каждой новой PowerShell
> сессии перед любыми `uv run` или `make uv-run` вызовами, чтобы дочерние
> процессы видели переменные окружения Qt и secret storage.

- `activate_environment.ps1` exports `QT_PLUGIN_PATH`, `QML2_IMPORT_PATH`, and
  related Qt variables. Leave the session open while working with Qt Designer or
  running the simulator.
- `make uv-sync` installs the exact dependency graph recorded in
  `requirements.lock`.

### Bash (Linux & WSL)

```bash
# Source the Qt environment and install dependencies.
source ./activate_environment.sh
make uv-sync
```

- The shell script writes the same Qt variables and ensures `uv` operates inside
  the project-managed cache under `.venv`.
- If WSL lacks a system Python 3.13 build, install it via `sudo apt install
  python3.13 python3.13-venv` prior to running the bootstrap helper.

## 5. Verify the Toolchain

Run the aggregated quality gate to confirm your workstation matches CI
expectations.

```bash
make check
```

This executes `ruff`, `mypy`, `pytest`, and `qmllint` using uv. A clean onboarding
ends with the quality gate reporting success.

## 6. Updating the Environment

When dependencies change, pull the latest commits and re-run `make uv-sync`. The
`uv` resolver applies only the delta, keeping the environment deterministic.

For Qt toolchain updates, invoke `python tools/setup_qt.py --force` to refresh
cached archives after bumping Qt versions in `pyproject.toml` or the master plan.

## 7. Troubleshooting Cheatsheet

| Symptom | Resolution |
| --- | --- |
| `uv: command not found` after bootstrap | Confirm `~/.local/bin` (Linux/WSL) or `%USERPROFILE%\AppData\Local\Microsoft\WindowsApps` (Windows) is on PATH, then rerun the bootstrap helper. |
| Qt plugins not discovered | Ensure you launched the terminal via the provided `activate_environment` script; verify the Qt installation exists under `.qt/6.10`. |
| `make check` fails because of PySide imports | Run `scripts/load_cipilot_env.ps1` in the current PowerShell session, then `make uv-run CMD="python tools/setup_qt.py"` to reinstall Qt components and rerun the checks. |
| Corporate proxy interrupts downloads | Set `HTTP_PROXY`/`HTTPS_PROXY` environment variables before running `scripts/bootstrap_uv.py` and `make uv-sync`. |

## 8. Next Steps

- Review `docs/ENVIRONMENT_SETUP.md` for deeper explanations of each command.
- Join the #dev-environment Slack channel and post the `make check` transcript
  when onboarding completes to confirm readiness for Phase 2 tasks.

