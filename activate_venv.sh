#!/usr/bin/env bash
set -euo pipefail

echo "=============================================="
echo " PneumoStabSim Professional - Python 3.13" 
echo "=============================================="

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
PYTHON_BIN=""
for candidate in python3.13 python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done
if [[ -z "$PYTHON_BIN" ]]; then
  echo "Python 3.13 interpreter not found" >&2
  exit 1
fi

if [[ ! -d "$VENV_PATH" ]]; then
  echo "Creating virtual environment at $VENV_PATH"
  "$PYTHON_BIN" -m venv "$VENV_PATH"
fi

# shellcheck source=/dev/null
source "$VENV_PATH/bin/activate"

python -m pip install --upgrade pip setuptools wheel
python -m pip install --require-hashes -r "$PROJECT_ROOT/requirements.txt" -c "$PROJECT_ROOT/requirements-compatible.txt"

if [[ -f "$PROJECT_ROOT/requirements-dev.txt" ]]; then
  python -m pip install --require-hashes -r "$PROJECT_ROOT/requirements-dev.txt" -c "$PROJECT_ROOT/requirements-compatible.txt"
fi

python "$PROJECT_ROOT/setup_environment.py"

echo "Environment ready. Run 'deactivate' to exit."
exec "$SHELL"
