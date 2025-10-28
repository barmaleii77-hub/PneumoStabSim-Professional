#!/usr/bin/env bash
# PneumoStabSim Professional - shell activation helper (Linux/macOS)

set -Eeuo pipefail

# Ensure predictable UTF-8 locale for Qt tooling and Python logging output.
export LANG="${LANG:-C.UTF-8}"
export LC_ALL="${LC_ALL:-C.UTF-8}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

function log() { printf '[env] %s\n' "$1"; }

trap 'log "Environment activation failed (exit code $?)"' ERR

if [[ ! -f "$ENV_FILE" ]]; then
  log ".env not found – run ./setup_environment.py first"
  return 1 2>/dev/null || exit 1
fi

# shellcheck disable=SC2046
export $(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$ENV_FILE" | tr -d '\r')

log "Environment variables loaded from .env"
log "PROJECT_ROOT=$PROJECT_ROOT"

if [[ ! -d "$PROJECT_ROOT/.venv" ]]; then
  log "Virtual environment missing – bootstrapping via uv"
  if command -v uv >/dev/null 2>&1; then
    (cd "$PROJECT_ROOT" && uv sync)
  else
    log "uv is not available, falling back to python -m venv"
    python3 -m venv "$PROJECT_ROOT/.venv"
    if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
      pip_args=("install")
      if [[ $(id -u) -eq 0 ]]; then
        pip_args+=("--root-user-action=ignore")
      fi
      pip_args+=("-r" "$PROJECT_ROOT/requirements.txt")
      "$PROJECT_ROOT/.venv/bin/python" -m pip "${pip_args[@]}"
    fi
  fi
fi

if [[ -d "$PROJECT_ROOT/.venv" ]]; then
  if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    log "Virtual environment already active: $VIRTUAL_ENV"
  elif [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
    # shellcheck source=/dev/null
    source "$PROJECT_ROOT/.venv/bin/activate"
    log "Activated virtual environment (.venv)"
  else
    log "Virtual environment found but activate script is missing"
  fi
else
  log "Virtual environment setup failed"
fi

log "Qt backend: ${QSG_RHI_BACKEND:-n/a} (Qt ${QT_VERSION:-unknown})"

trap - ERR
