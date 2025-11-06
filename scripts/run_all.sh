#!/usr/bin/env bash
set -euo pipefail

export PATH="${QT_HOME:-/opt/Qt/current/gcc_64}/bin:${PATH}"
export PYTHONUNBUFFERED=1
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
export QT_QUICK_BACKEND="${QT_QUICK_BACKEND:-software}"
export LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-1}"
export MESA_GL_VERSION_OVERRIDE="${MESA_GL_VERSION_OVERRIDE:-4.1}"
export MESA_GLSL_VERSION_OVERRIDE="${MESA_GLSL_VERSION_OVERRIDE:-410}"

echo "== Lint =="
ruff check .
mypy --ignore-missing-imports .

echo "== QML lint =="
if command -v qmllint >/dev/null 2>&1; then
  qmllint -I assets/qml assets/qml || true
else
  echo "qmllint not available"
fi

echo "== Shader sanity =="
python /usr/local/bin/shader_sanity.py

echo "== Shader validation =="
python tools/validate_shaders.py

echo "== Shader log audit =="
python tools/check_shader_logs.py reports/shaders --recursive --fail-on-warnings --expect-fallback

echo "== PyTest =="
/usr/local/bin/xvfb_wrapper.sh pytest -q -n auto --maxfail=1 --disable-warnings --cov=src || true

mkdir -p reports

echo "== Smoke OpenGL =="
/usr/local/bin/xvfb_wrapper.sh env QSG_RHI_BACKEND=opengl python app.py --test-mode || true

echo "== Smoke Vulkan =="
LVP_JSON=$(ls /usr/share/vulkan/icd.d/*lvp*.json 2>/dev/null | head -n 1 || true)
if [[ -f "$LVP_JSON" ]]; then
  /usr/local/bin/xvfb_wrapper.sh env QSG_RHI_BACKEND=vulkan VK_ICD_FILENAMES="$LVP_JSON" python app.py --test-mode || true
else
  echo "[warn] lavapipe ICD not found, skipping Vulkan smoke"
fi

echo "== Collect logs =="
python /usr/local/bin/collect_logs.py
