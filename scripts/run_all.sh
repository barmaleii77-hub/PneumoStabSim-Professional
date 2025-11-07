#!/usr/bin/env bash
set -euo pipefail

export PATH="${QT_HOME:-/opt/Qt/current/gcc_64}/bin:${PATH}"
export PYTHONUNBUFFERED=1
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
export QT_QUICK_BACKEND="${QT_QUICK_BACKEND:-software}"
export LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-1}"
export MESA_GL_VERSION_OVERRIDE="${MESA_GL_VERSION_OVERRIDE:-4.1}"
export MESA_GLSL_VERSION_OVERRIDE="${MESA_GLSL_VERSION_OVERRIDE:-410}"

mkdir -p reports

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
python tools/check_shader_logs.py reports/shaders --recursive --expect-fallback

python - <<'PY'
"""Aggregate shader warnings into reports/warnings.log for CI publication."""

from __future__ import annotations

import json
from pathlib import Path

summary_path = Path("reports/tests/shader_logs_summary.json")
warnings_log = Path("reports/warnings.log")
warnings_log.parent.mkdir(parents=True, exist_ok=True)

entries: list[str] = []
if summary_path.exists():
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        warnings_log.write_text(
            f"Failed to parse {summary_path}: {exc}\n", encoding="utf-8"
        )
    else:
        for item in summary:
            source = item.get("source", "<unknown>")
            for warning in item.get("warnings", []) or []:
                line = warning.get("line")
                message = warning.get("message", "")
                location = f"{source}:{line}" if line not in (None, 0) else source
                entries.append(f"{location} - {message}".strip())

        if entries:
            warnings_log.write_text("\n".join(entries) + "\n", encoding="utf-8")
        else:
            warnings_log.write_text("", encoding="utf-8")
else:
    warnings_log.write_text("", encoding="utf-8")

print(
    "[run_all] Shader warnings captured: {count} -> {destination}".format(
        count=len(entries), destination=warnings_log
    )
)
PY

echo "== PyTest =="
/usr/local/bin/xvfb_wrapper.sh pytest -q -n auto --maxfail=1 --disable-warnings --cov=src || true

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
