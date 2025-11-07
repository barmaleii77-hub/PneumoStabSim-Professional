#!/usr/bin/env bash
set -euo pipefail

export QT_HOME="${QT_HOME:-/opt/Qt/current/gcc_64}"
export PATH="${QT_HOME}/bin:${PATH}"
export QT_QPA_PLATFORM='offscreen'
export PYTHONUNBUFFERED=1

mkdir -p reports reports/quality
warnings_log="reports/warnings.log"
touch "${warnings_log}"
ln -sf "../warnings.log" "reports/quality/warnings.log"

echo "== Qt == "
if [[ -f "/opt/Qt/CURRENT_VERSION" ]]; then
  echo "Active Qt version: $(cat /opt/Qt/CURRENT_VERSION)"
fi
qmllint -v 2>/dev/null || true
qsb -h 2>/dev/null || true
echo "== GLX =="
if command -v glxinfo >/dev/null 2>&1; then
  glxinfo | grep -E 'OpenGL version|OpenGL renderer' || true
else
  echo "glxinfo not available"
fi
echo "== Vulkan =="
if command -v vulkaninfo >/dev/null 2>&1; then
  vulkaninfo | head -n 20 || true
else
  echo "vulkaninfo not available"
fi
echo "== Python =="
python -V

python /usr/local/bin/install_deps.py || true

exec "$@"
