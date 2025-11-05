#!/usr/bin/env bash
set -euo pipefail

# Load .env or .env.cipilot into current shell
ENV_FILE="${1:-.env.cipilot}"

load_env_file() {
  local file="$1"
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    if [[ "$line" =~ ^(export[[:space:]]+)?([^=[:space:]]+)=(.*)$ ]]; then
      local name="${BASH_REMATCH[2]}"
      local value="${BASH_REMATCH[3]}"
      value="${value%$'\r'}"
      value="${value%$'\n'}"
      eval "export ${name}=${value}"
    fi
  done < "$file"
  echo "[env] Loaded $file"
}

if [[ -f "$ENV_FILE" ]]; then
  load_env_file "$ENV_FILE"
elif [[ -f ".env" ]]; then
  load_env_file ".env"
else
  echo "[env] No env file found (.env.cipilot or .env)"
fi

# Populate Qt related environment variables if missing
if [[ -z "${QT_PLUGIN_PATH:-}" ]]; then
  plugin_path=$(python - <<'PY' || true
from PySide6.QtCore import QLibraryInfo as Q
print(Q.path(Q.LibraryPath.PluginsPath))
PY
  )
  if [[ -n "${plugin_path}" ]]; then
    export QT_PLUGIN_PATH="${plugin_path}"
    echo "[env] QT_PLUGIN_PATH=${QT_PLUGIN_PATH}"
  fi
fi

if [[ -z "${QML2_IMPORT_PATH:-}" ]]; then
  qml_import_path=$(python - <<'PY' || true
from PySide6.QtCore import QLibraryInfo as Q
print(Q.path(Q.LibraryPath.QmlImportsPath))
PY
  )
  paths=()
  if [[ -d "assets/qml" ]]; then
    assets_qml=$(python - <<'PY' || true
from pathlib import Path
print(Path('assets/qml').resolve())
PY
    )
    if [[ -n "${assets_qml}" ]]; then
      paths+=("${assets_qml}")
    fi
  fi
  if [[ -n "${qml_import_path}" ]]; then
    paths+=("${qml_import_path}")
  fi
  if (( ${#paths[@]} > 0 )); then
    old_ifs="$IFS"
    IFS=':'
    QML2_IMPORT_PATH="${paths[*]}"
    IFS="$old_ifs"
    export QML2_IMPORT_PATH
    echo "[env] QML2_IMPORT_PATH=${QML2_IMPORT_PATH}"
  fi
fi

# Run environment verifications
if [[ -f "tools/environment/verify_qt_setup.py" ]]; then
  python tools/environment/verify_qt_setup.py
fi

report_path="reports/quality/environment_setup_report.md"
mkdir -p "$(dirname "${report_path}")"
python app.py --env-report "${report_path}" --env-check
printf '[env] Environment report written to %s\n' "${report_path}"

