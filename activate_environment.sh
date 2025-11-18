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

ensure_path_variable() {
  local dir="$1"
  local var_name="$2"
  [[ -d "$dir" ]] || return

  local current="${!var_name:-}"
  local separator="${PATH_SEPARATOR:-}"

  if [[ -z "$separator" ]]; then
    if [[ "$current" == *";"* && "$current" != *":"* ]]; then
      separator=';'
    else
      separator=':'
    fi
  fi

  if [[ -z "$current" ]]; then
    printf -v "$var_name" '%s' "$dir"
    export "$var_name"
    log "$var_name initialised with $dir"
    return
  fi

  local IFS="$separator"
  read -r -a parts <<< "$current"
  for existing in "${parts[@]}"; do
    if [[ "$existing" == "$dir" ]]; then
      return
    fi
  done

  parts+=("$dir")
  local new_value="$(printf '%s' "${parts[0]}")"
  for ((i = 1; i < ${#parts[@]}; ++i)); do
    new_value+="$separator${parts[$i]}"
  done
  printf -v "$var_name" '%s' "$new_value"
  export "$var_name"
  log "$var_name extended with $dir"
}

ensure_qml_path() {
  ensure_path_variable "$1" "${2:-QML2_IMPORT_PATH}"
}

ensure_plugin_path() {
  ensure_path_variable "$1" "${2:-QT_PLUGIN_PATH}"
}

ensure_qml_path "$PROJECT_ROOT/assets/qml" "QML2_IMPORT_PATH"
ensure_qml_path "$PROJECT_ROOT/assets/qml/scene" "QML2_IMPORT_PATH"
ensure_qml_path "$PROJECT_ROOT/assets/qml" "QML_IMPORT_PATH"
ensure_qml_path "$PROJECT_ROOT/assets/qml/scene" "QML_IMPORT_PATH"
ensure_qml_path "$PROJECT_ROOT/assets/qml" "QT_QML_IMPORT_PATH"
ensure_qml_path "$PROJECT_ROOT/assets/qml/scene" "QT_QML_IMPORT_PATH"

inject_qt_runtime_paths() {
  local python_bin="${PYTHON:-python}"
  local qt_paths

  if ! qt_paths=$("$python_bin" - <<'PY'
import sys

try:
    from PySide6 import QtCore  # type: ignore
except Exception:
    sys.exit(1)

library_path = getattr(QtCore.QLibraryInfo.LibraryPath, "QmlImportsPath", QtCore.QLibraryInfo.LibraryPath.Qml2ImportsPath)
print(QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.PluginsPath))
print(QtCore.QLibraryInfo.path(library_path))
PY
  ); then
    log "PySide6 not available; skipping Qt path export"
    return
  fi

  local qt_plugin_path
  local qt_qml_import_path
  qt_plugin_path=$(printf '%s\n' "$qt_paths" | sed -n '1p')
  qt_qml_import_path=$(printf '%s\n' "$qt_paths" | sed -n '2p')

  if [[ -n "$qt_plugin_path" && -d "$qt_plugin_path" ]]; then
    ensure_plugin_path "$qt_plugin_path" "QT_PLUGIN_PATH"
  else
    log "Qt plugin path unavailable or missing: $qt_plugin_path"
  fi

  if [[ -n "$qt_qml_import_path" && -d "$qt_qml_import_path" ]]; then
    ensure_qml_path "$qt_qml_import_path" "QML2_IMPORT_PATH"
    ensure_qml_path "$qt_qml_import_path" "QML_IMPORT_PATH"
    ensure_qml_path "$qt_qml_import_path" "QT_QML_IMPORT_PATH"
  else
    log "Qt QML import path unavailable or missing: $qt_qml_import_path"
  fi

  if [[ -z "${QT_QUICK_CONTROLS_STYLE:-}" ]]; then
    export QT_QUICK_CONTROLS_STYLE="Basic"
    log "QT_QUICK_CONTROLS_STYLE set to Basic"
  fi
}

if [[ ! -d "$PROJECT_ROOT/.venv" ]]; then
  if [[ "${PSS_SKIP_ENV_BOOTSTRAP:-0}" == "1" ]]; then
    log "Virtual environment missing – bootstrap skipped (PSS_SKIP_ENV_BOOTSTRAP=1)"
  else
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

inject_qt_runtime_paths

log "Qt backend: ${QSG_RHI_BACKEND:-n/a} (Qt ${QT_VERSION:-unknown})"

trap - ERR
