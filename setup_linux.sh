#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[setup_linux] %s\n' "$1"
}

host_os=$(uname -s 2>/dev/null || echo "unknown")
log "Detected host kernel: ${host_os}"

if [[ "${host_os}" != "Linux" ]]; then
  log "This bootstrap script only supports Linux hosts."
  exit 1
fi

log "Updating package index"
sudo apt-get update

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
    log "Skipping unavailable package '$pkg'"
  fi
done

if (( ${#to_install[@]} > 0 )); then
  log "Installing: ${to_install[*]}"
  for pkg in "${to_install[@]}"; do
    if ! sudo apt-get install -y --no-install-recommends "$pkg"; then
      log "Package '$pkg' could not be installed; continuing"
    fi
  done
else
  log "No additional apt packages required"
fi

if command -v uv >/dev/null 2>&1; then
  log "Synchronising Python environment via uv"
  uv sync --extra dev
else
  if ! command -v python3 >/dev/null 2>&1; then
    log "python3 is required but not found"
    exit 1
  fi
  log "Upgrading pip"
  python3 -m pip install --upgrade pip
  log "Installing project dependencies via pip"
  python3 -m pip install -r requirements-dev.txt
fi

log "Ensuring critical PySide6 / OpenGL wheels"
python3 -m pip install --upgrade --no-cache-dir \
  "PySide6>=6.10,<7" \
  "PySide6-Addons>=6.10,<7" \
  "PySide6-Essentials>=6.10,<7" \
  "shiboken6>=6.10,<7" \
  "PyOpenGL==3.1.10" \
  "PyOpenGL-accelerate==3.1.10"

log "Exporting Qt headless defaults"
cat <<'ENV' >> "${GITHUB_ENV:-/tmp/setup_linux.env}"
QT_QPA_PLATFORM=offscreen
QT_QUICK_BACKEND=software
QSG_RHI_BACKEND=opengl
LIBGL_ALWAYS_SOFTWARE=1
MESA_GL_VERSION_OVERRIDE=4.1
MESA_GLSL_VERSION_OVERRIDE=410
ENV

log "Linux environment bootstrap complete"
