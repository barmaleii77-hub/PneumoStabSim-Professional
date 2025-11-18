#!/usr/bin/env bash
set -euo pipefail

export PATH="${QT_HOME:-/opt/Qt/current/gcc_64}/bin:${PATH}"
export PYTHONUNBUFFERED=1
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
export QT_QUICK_BACKEND="${QT_QUICK_BACKEND:-software}"
export LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-1}"
export MESA_GL_VERSION_OVERRIDE="${MESA_GL_VERSION_OVERRIDE:-4.1}"
export MESA_GLSL_VERSION_OVERRIDE="${MESA_GLSL_VERSION_OVERRIDE:-410}"

mkdir -p reports reports/quality reports/tests
warnings_log="reports/warnings.log"
: > "${warnings_log}"

append_warning_block() {
  local header="$1"
  shift || true
  local lines=("$@")

  if ((${#lines[@]} == 0)); then
    return 0
  fi

  {
    if [[ -s "${warnings_log}" ]]; then
      printf '\n'
    fi
    printf '# %s\n' "$header"
    printf '%s\n' "${lines[@]}"
  } >>"${warnings_log}"
}

run_with_warnings_capture() {
  local header="$1"
  shift
  local tmp
  tmp=$(mktemp)

  set +e
  "$@" 2>&1 | tee "${tmp}"
  local status=${PIPESTATUS[0]}
  set -e

  if [[ -s "${tmp}" ]]; then
    mapfile -t warning_lines < <(grep -iE '\bwarn(ing)?\b' "${tmp}") || true
    append_warning_block "${header}" "${warning_lines[@]}"
  fi

  rm -f "${tmp}"
  return "${status}"
}

echo "== Lint =="
run_with_warnings_capture "ruff" ruff check .
run_with_warnings_capture "mypy" mypy --ignore-missing-imports .

echo "== QML lint =="
if command -v qmllint >/dev/null 2>&1; then
  run_with_warnings_capture "qmllint" qmllint -I assets/qml assets/qml || true
else
  echo "qmllint not available"
fi

echo "== Shader sanity =="
run_with_warnings_capture "shader_sanity" python /usr/local/bin/shader_sanity.py

echo "== Shader validation =="
run_with_warnings_capture "validate_shaders" python tools/validate_shaders.py

echo "== Shader log audit =="
run_with_warnings_capture \
  "check_shader_logs" \
  python tools/check_shader_logs.py reports/shaders --recursive --expect-fallback

python - <<'PY'
"""Aggregate shader warnings into reports/warnings.log for CI publication."""

from __future__ import annotations

import json
from pathlib import Path


def _append_block(destination: Path, header: str, lines: list[str]) -> int:
    """Append ``lines`` to ``destination`` with a header if content exists."""

    if not lines:
        return 0

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.touch(exist_ok=True)

    prefix = "" if destination.stat().st_size == 0 else "\n"
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(f"{prefix}# {header}\n")
        for entry in lines:
            handle.write(f"{entry}\n")

    return len(lines)


summary_path = Path("reports/tests/shader_logs_summary.json")
warnings_log = Path("reports/warnings.log")

entries: list[str] = []
if summary_path.exists():
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        entries.append(
            f"{summary_path} - Failed to parse shader logs summary: {exc}"
        )
    else:
        for item in summary:
            source = item.get("source", "<unknown>")
            for warning in item.get("warnings", []) or []:
                line = warning.get("line")
                message = warning.get("message", "")
                location = f"{source}:{line}" if line not in (None, 0) else source
                entries.append(f"{location} - {message}".rstrip())

count = _append_block(warnings_log, "Shader warnings", entries)
if count == 0:
    warnings_log.parent.mkdir(parents=True, exist_ok=True)
    warnings_log.touch(exist_ok=True)
    print(
        "[run_all] No shader warnings detected; summary stored at {destination}".format(
            destination=warnings_log,
        )
    )
else:
    print("[run_all] Shader warnings detected:")
    for entry in entries:
        print(f"  - {entry}")
    print(
        "[run_all] Shader warnings captured: {count} -> {destination}".format(
            count=count,
            destination=warnings_log,
        )
    )
PY

echo "== PyTest =="
pytest_report="reports/tests/container-pytest.xml"
set +e
run_with_warnings_capture \
  "pytest" \
  /usr/local/bin/xvfb_wrapper.sh pytest -q -n auto --maxfail=1 --cov=src \
    --junitxml="${pytest_report}"
pytest_status=$?
set -e

python -m tools.quality.skip_policy --ci --junitxml "${pytest_report}" \
  --summary reports/tests/skipped_container.md

if (( pytest_status != 0 )); then
  exit "${pytest_status}"
fi

echo "== Final readiness =="
/usr/local/bin/xvfb_wrapper.sh python final_readiness_test.py

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
