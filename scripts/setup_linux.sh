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
Usage: scripts/setup_linux.sh [--skip-system] [--skip-python] [--skip-qt] [--qt-version <version>]

  --skip-system   Skip installation of system packages (apt).
  --skip-python   Skip synchronising Python dependencies.
  --skip-qt       Skip offline Qt runtime provisioning via tools/setup_qt.py.
  --qt-version    Override the Qt version to provision (defaults to 6.10.0).

The script installs Qt/graphics packages required by the test-suite and
ensures the PySide6 runtime is available. Environment variables for headless
runs are exported to \$GITHUB_ENV when present.
USAGE
}

skip_system=0
skip_python=0
skip_qt=0
qt_version="${QT_VERSION:-6.10.0}"

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
    --skip-qt)
      skip_qt=1
      shift
      ;;
    --qt-version)
      if [[ -z "${2:-}" ]]; then
        warn "--qt-version requires a value"
        usage
        exit 1
      fi
      qt_version="$2"
      shift 2
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
      qt6-base-dev
      qt6-base-dev-tools
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
python_for_scripts="${python_cmd}"

if [[ ${skip_python} -eq 0 ]]; then
  if command -v uv >/dev/null 2>&1; then
    log "Synchronising Python environment via uv"
    uv sync --extra dev

    if [[ -x ".venv/bin/python" ]]; then
      python_for_scripts="$(pwd)/.venv/bin/python"
      log "Using ${python_for_scripts} for subsequent provisioning steps"
    fi

    log "Ensuring PySide6/OpenGL wheels via uv"
    uv pip install --upgrade --no-cache-dir \
      "PySide6==6.10.*" \
      "PySide6-Addons==6.10.*" \
      "PySide6-Essentials==6.10.*" \
      "shiboken6==6.10.*" \
      numpy \
      pytest-qt \
      "PyOpenGL==3.1.10" \
      "PyOpenGL-accelerate==3.1.10" \
      "aqtinstall>=3.2.1,<3.3"
  else
    log "uv not found; falling back to pip"
    "$python_cmd" -m pip install --upgrade pip
    "$python_cmd" -m pip install -r requirements-dev.txt
    "$python_cmd" -m pip install --upgrade --no-cache-dir \
      "PySide6==6.10.*" \
      "PySide6-Addons==6.10.*" \
      "PySide6-Essentials==6.10.*" \
      "shiboken6==6.10.*" \
      numpy \
      pytest-qt \
      "PyOpenGL==3.1.10" \
      "PyOpenGL-accelerate==3.1.10" \
      "aqtinstall>=3.2.1,<3.3"
    python_for_scripts="${python_cmd}"
  fi
else
  log "Skipping Python dependency installation"
fi

qt_bin=""
qt_plugins=""
qt_qml=""
if [[ ${skip_qt} -eq 0 ]]; then
  log "Provisioning Qt runtime via tools/setup_qt.py (version ${qt_version})"
  if [[ ! -f tools/setup_qt.py ]]; then
    warn "tools/setup_qt.py not found; skipping Qt provisioning"
  else
    if "${python_for_scripts}" tools/setup_qt.py --qt-version "${qt_version}" --prune-archives; then
      host_arch="gcc_64"
      qt_root="$(pwd)/Qt/${qt_version}/${host_arch}"
      if [[ -d "${qt_root}" ]]; then
        qt_bin="${qt_root}/bin"
        qt_plugins="${qt_root}/plugins"
        qt_qml="${qt_root}/qml"
        if [[ -n "${GITHUB_PATH:-}" && -d "${qt_bin}" ]]; then
          log "Registering Qt bin directory with GITHUB_PATH"
          printf '%s\n' "${qt_bin}" >> "${GITHUB_PATH}"
        elif [[ -d "${qt_bin}" ]]; then
          export PATH="${qt_bin}:${PATH}"
        fi
      else
        warn "Qt root ${qt_root} not found after provisioning"
      fi
    else
      warn "Qt provisioning script failed"
    fi
  fi
else
  log "Skipping Qt runtime provisioning"
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
  echo "QT_VERSION=${qt_version}"
  if [[ -n "${qt_plugins}" ]]; then
    echo "QT_PLUGIN_PATH=${qt_plugins}"
  fi
  if [[ -n "${qt_qml}" ]]; then
    echo "QML2_IMPORT_PATH=${qt_qml}"
  fi
} >>"${env_file}"

log "Linux environment bootstrap complete"
