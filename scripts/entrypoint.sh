#!/usr/bin/env bash
set -euo pipefail

export QT_HOME="${QT_HOME:-/opt/Qt/6.10.0/gcc_64}"
export PATH="${QT_HOME}/bin:${PATH}"
export QT_QPA_PLATFORM='offscreen'
export PYTHONUNBUFFERED=1

echo "== Qt == "
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
