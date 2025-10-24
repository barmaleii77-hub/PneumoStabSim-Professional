#!/usr/bin/env bash
# PneumoStabSim Professional - shell activation helper (Linux/macOS)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

function log() { printf '[env] %s\n' "$1"; }

if [[ ! -f "$ENV_FILE" ]]; then
  log ".env not found – run ./setup_environment.py first"
  return 1 2>/dev/null || exit 1
fi

# shellcheck disable=SC2046
export $(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$ENV_FILE" | tr -d '\r')

log "Environment variables loaded from .env"
log "PROJECT_ROOT=$PROJECT_ROOT"

if [[ -d "$PROJECT_ROOT/.venv" ]]; then
  if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    log "Virtual environment already active: $VIRTUAL_ENV"
  else
    if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
      # shellcheck source=/dev/null
      source "$PROJECT_ROOT/.venv/bin/activate"
      log "Activated virtual environment (.venv)"
    fi
  fi
else
  log "Virtual environment missing – run ./setup_environment.py"
fi

log "Qt backend: ${QSG_RHI_BACKEND:-n/a} (Qt ${QT_VERSION:-unknown})"
