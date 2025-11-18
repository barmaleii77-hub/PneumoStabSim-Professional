#!/usr/bin/env bash
set -euo pipefail

log() {
    printf '[install_qt_runtime] %s\n' "$1"
}

warn() {
    printf '[install_qt_runtime][warn] %s\n' "$1" >&2
}

if ! command -v apt-get >/dev/null 2>&1; then
    echo "Error: apt-get is required to install the Qt runtime libraries automatically." >&2
    echo "Please install libgl1, libxkbcommon0, libxkbcommon-x11-0, libegl1, libgles2, and qt6 shader tooling using your distribution's package manager." >&2
    exit 1
fi

packages=(
    libgl1
    libxkbcommon0
    libxkbcommon-x11-0
    libegl1
    libgles2
    qt6-shader-tools
)

if [ "${1-}" = "--dry-run" ]; then
    echo "apt-get update"
    echo "apt-get install -y ${packages[*]}"
    exit 0
fi

if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        exec sudo "$0" "$@"
    fi
    echo "Error: root privileges are required. Re-run this script with sudo or as root." >&2
    exit 2
fi

log "Detecting available runtime packages"
to_install=()
missing=()

for pkg in "${packages[@]}"; do
    if dpkg -s "$pkg" >/dev/null 2>&1; then
        log "Package '$pkg' already installed"
        continue
    fi

    if apt-cache show "$pkg" >/dev/null 2>&1; then
        to_install+=("$pkg")
    else
        missing+=("$pkg")
    fi
done

if (( ${#missing[@]} > 0 )); then
    warn "Skipping unavailable packages: ${missing[*]}"
fi

if (( ${#to_install[@]} > 0 )); then
    log "Installing packages: ${to_install[*]}"
    apt-get update
    apt-get install -y --no-install-recommends "${to_install[@]}"
else
    log "No additional apt packages required"
fi
