#!/usr/bin/env bash
# PneumoStabSim Professional - environment bootstrap (Linux/macOS)
# Mirrors setup_environment.ps1 defaults while enforcing the OpenGL RHI backend.

set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

log() {
  printf '[setup] %s\n' "$1"
}

log "Configuring Qt RHI backend for OpenGL"
export QSG_RHI_BACKEND="opengl"
export QSG_OPENGL_VERSION="${QSG_OPENGL_VERSION:-4.5}"
export QT_OPENGL="${QT_OPENGL:-desktop}"

if [[ -z "${QT_LOGGING_RULES:-}" ]]; then
  export QT_LOGGING_RULES="js.debug=true;qt.qml.debug=true"
fi
if [[ -z "${QSG_INFO:-}" ]]; then
  export QSG_INFO="1"
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  log "Python executable '$PYTHON_BIN' not found; falling back to 'python'"
  PYTHON_BIN="python"
fi

log "Running setup_environment.py via $PYTHON_BIN"
"$PYTHON_BIN" "$PROJECT_ROOT/setup_environment.py" "$@"
