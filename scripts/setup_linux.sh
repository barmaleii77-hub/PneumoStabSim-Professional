#!/usr/bin/env bash
# PneumoStabSim Professional — Linux dependency bootstrap
# Installs system and Python dependencies required for Qt Quick 3D tests.

set -Eeuo pipefail

log() {
  printf '[setup-linux] %s\n' "$1"
}

if [[ "${EUID}" -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1; then
    log "Re-running with sudo to install system packages"
    exec sudo --preserve-env=QT_QPA_PLATFORM "$0" "$@"
  else
    log "Root privileges required to install system packages"
    exit 1
  fi
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update

packages=(
  xvfb xauth dbus-x11
  mesa-utils mesa-utils-extra
  libgl1 libgl1-mesa-dri libglu1-mesa
  libegl1 libegl1-mesa libgles2 libgles2-mesa
  libosmesa6 libgbm1 libdrm2
  libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0
  libxcb-shape0 libxcb-randr0 libxcb-glx0 libxcb-xfixes0
  libxkbcommon0 libxkbcommon-x11-0 libxkbcommon-dev
  libvulkan1 mesa-vulkan-drivers vulkan-tools
  qt6-shader-baker
  python3-pip
)

available=()
for pkg in "${packages[@]}"; do
  if apt-cache show "$pkg" >/dev/null 2>&1; then
    available+=("$pkg")
  else
    log "Skipping unavailable package: $pkg"
  fi
done

if [[ ${#available[@]} -gt 0 ]]; then
  apt-get install -y --no-install-recommends "${available[@]}"
else
  log "No system packages available for installation"
fi

if ! command -v pip3 >/dev/null 2>&1; then
  log "Installing python3-pip"
  apt-get install -y python3-pip
fi

log "System dependencies installed"

if ! command -v python3 >/dev/null 2>&1; then
  log "python3 executable is required"
  exit 1
fi

PYTHON_BIN=${PYTHON_BIN:-python3}
PIP_FLAGS=("--break-system-packages")
PY_PACKAGES=(
  "PySide6>=6.10,<7"
  "PySide6-Essentials>=6.10,<7"
  "PySide6-Addons>=6.10,<7"
)

for pkg in "${PY_PACKAGES[@]}"; do
  log "Installing $pkg"
  "${PYTHON_BIN}" -m pip install "${PIP_FLAGS[@]}" "$pkg"
done

QT_QUICK_PKG="PySide6-QtQuick3D>=6.10,<7"
if ! "${PYTHON_BIN}" -m pip install "${PIP_FLAGS[@]}" "$QT_QUICK_PKG"; then
  log "PySide6-QtQuick3D 6.10 is unavailable; attempting 6.7 fallback"
  if ! "${PYTHON_BIN}" -m pip install "${PIP_FLAGS[@]}" "PySide6-QtQuick3D>=6.7,<6.8"; then
    log "Warning: PySide6-QtQuick3D wheels could not be installed; ensure Qt Quick 3D binaries are provided by Qt SDK"
  fi
fi

log "PySide6 runtime packages installed"

log "Configuring Qt headless defaults"
export QT_QPA_PLATFORM=${QT_QPA_PLATFORM:-offscreen}
export QT_QUICK_BACKEND=${QT_QUICK_BACKEND:-software}
export QSG_RHI_BACKEND=${QSG_RHI_BACKEND:-opengl}

log "Setup complete. Launch tests with: QT_QPA_PLATFORM=$QT_QPA_PLATFORM"
