#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${UV_PROJECT_DIR:-.}"
UV_BIN="${UV:-uv}"
PYTHON_BIN="${PYTHON:-python3}"
RUN_ARGS="${UV_RUN_ARGS:- --locked}"
REPORT_DIR="reports/environment"
SCRIPT="tools/environment/verify_qt_setup.py"
ARGS=("${SCRIPT}" --report-dir "${REPORT_DIR}" --allow-missing-runtime)

VENV_PY="${PROJECT_ROOT}/.venv/bin/python"

if [ -f "${PROJECT_ROOT}/activate_environment.sh" ]; then
    # shellcheck disable=SC1090
    PSS_SKIP_ENV_BOOTSTRAP=1 source "${PROJECT_ROOT}/activate_environment.sh" >/dev/null 2>&1 || true
fi

if [ -x "${VENV_PY}" ]; then
    (cd "${PROJECT_ROOT}" && "${VENV_PY}" "${ARGS[@]}")
    exit 0
fi

if command -v "${UV_BIN}" >/dev/null 2>&1; then
    if (cd "${PROJECT_ROOT}" && "${UV_BIN}" run ${RUN_ARGS} -- python "${ARGS[@]}"); then
        exit 0
    fi
    echo "Warning: '${UV_BIN}' execution failed; falling back to '${PYTHON_BIN}'." >&2
    (cd "${PROJECT_ROOT}" && "${PYTHON_BIN}" "${ARGS[@]}")
    exit 0
fi

(cd "${PROJECT_ROOT}" && "${PYTHON_BIN}" "${ARGS[@]}")
