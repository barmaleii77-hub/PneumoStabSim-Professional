#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[setup_linux] %s\n' "$1"
}

warn() {
  printf '[setup_linux][warn] %s\n' "$1" >&2
}

usage() {
  cat <<'USAGE'
Usage: scripts/setup_linux.sh [--skip-system] [--skip-python]

  --skip-system  Skip installation of system packages (apt).
  --skip-python  Skip synchronising Python dependencies.

The script installs Qt/graphics packages required by the test-suite and
ensures the PySide6 runtime is available. Environment variables for headless
runs are exported to \$GITHUB_ENV when present.
USAGE
}

skip_system=0
skip_python=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-system)
      skip_system=1
      shift
      ;;
    --skip-python)
      skip_python=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      warn "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

kernel=$(uname -s 2>/dev/null || echo "unknown")
log "Detected host kernel: ${kernel}"
if [[ ${kernel} != "Linux" ]]; then
  warn "This bootstrap script only supports Linux hosts."
  exit 1
fi

run_cmd() {
  if [[ $EUID -eq 0 ]]; then
    "$@"
  else
    if command -v sudo >/dev/null 2>&1; then
      sudo "$@"
    else
      warn "sudo is required to run '$*'"
      exit 1
    fi
  fi
}

if [[ ${skip_system} -eq 0 ]]; then
  if ! command -v apt-get >/dev/null 2>&1; then
    warn "apt-get not found; skipping system package installation"
  else
    log "Updating package index"
    run_cmd apt-get update

    packages=(
      build-essential
      git
      curl
      pkg-config
      xvfb
      xauth
      dbus-x11
      mesa-utils
      mesa-utils-extra
      libgl1
      libgl1-mesa-dri
      libglu1-mesa
      libglu1-mesa-dev
      libegl1
      libegl1-mesa-dev
      libgles2-mesa-dev
      libosmesa6
      libosmesa6-dev
      libgbm1
      libdrm2
      libxcb-xinerama0
      libxkbcommon0
      libxkbcommon-x11-0
      libxcb-keysyms1
      libxcb-image0
      libxcb-icccm4
      libxcb-render-util0
      libxcb-xfixes0
      libxcb-shape0
      libxcb-randr0
      libxcb-glx0
      libvulkan1
      mesa-vulkan-drivers
      vulkan-tools
      qt6-shader-baker
    )

    to_install=()
    for pkg in "${packages[@]}"; do
      if dpkg -s "$pkg" >/dev/null 2>&1; then
        log "Package '$pkg' already installed"
        continue
      fi
      if apt-cache show "$pkg" >/dev/null 2>&1; then
        to_install+=("$pkg")
      else
        warn "Package '$pkg' is not available in current apt sources"
      fi
    done

    if (( ${#to_install[@]} > 0 )); then
      log "Installing packages: ${to_install[*]}"
      run_cmd apt-get install -y --no-install-recommends "${to_install[@]}"
    else
      log "No additional apt packages required"
    fi
  fi
else
  log "Skipping system package installation"
fi

python_cmd="python3"
if ! command -v "$python_cmd" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    python_cmd="python"
  else
    warn "python3 is required but not found"
    exit 1
  fi
fi

if [[ ${skip_python} -eq 0 ]]; then
  if command -v uv >/dev/null 2>&1; then
    log "Synchronising Python environment via uv"
    uv sync --extra dev

    log "Ensuring PySide6/OpenGL wheels via uv"
    uv pip install --upgrade --no-cache-dir \
      "PySide6>=6.10,<7" \
      "PySide6-Addons>=6.10,<7" \
      "PySide6-Essentials>=6.10,<7" \
      "shiboken6>=6.10,<7" \
      "PyOpenGL==3.1.10" \
      "PyOpenGL-accelerate==3.1.10"
  else
    log "uv not found; falling back to pip"
    "$python_cmd" -m pip install --upgrade pip
    "$python_cmd" -m pip install -r requirements-dev.txt
    "$python_cmd" -m pip install --upgrade --no-cache-dir \
      "PySide6>=6.10,<7" \
      "PySide6-Addons>=6.10,<7" \
      "PySide6-Essentials>=6.10,<7" \
      "shiboken6>=6.10,<7" \
      "PyOpenGL==3.1.10" \
      "PyOpenGL-accelerate==3.1.10"
  fi
else
  log "Skipping Python dependency installation"
fi

env_file=${GITHUB_ENV:-/tmp/setup_linux.env}
log "Exporting headless Qt defaults to ${env_file}"
{
  echo "QT_QPA_PLATFORM=offscreen"
  echo "QT_QUICK_BACKEND=software"
  echo "QSG_RHI_BACKEND=opengl"
  echo "LIBGL_ALWAYS_SOFTWARE=1"
  echo "MESA_GL_VERSION_OVERRIDE=4.1"
  echo "MESA_GLSL_VERSION_OVERRIDE=410"
  echo "QT_LOGGING_RULES=*.debug=false;qt.scenegraph.general=false"
  if [[ -z "${DISPLAY:-}" ]]; then
    echo "DISPLAY="
  fi
} >>"${env_file}"

log "Linux environment bootstrap complete"
