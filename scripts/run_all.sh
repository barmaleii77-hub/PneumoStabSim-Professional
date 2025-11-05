#!/usr/bin/env bash
set -euo pipefail

export PATH="${QT_HOME:-/opt/Qt/current/gcc_64}/bin:${PATH}"
export PYTHONUNBUFFERED=1

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
