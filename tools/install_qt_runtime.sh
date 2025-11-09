#!/usr/bin/env bash
set -euo pipefail

if ! command -v apt-get >/dev/null 2>&1; then
    echo "Error: apt-get is required to install the Qt runtime libraries automatically." >&2
    echo "Please install libgl1, libxkbcommon0, libegl1, and libgles2 using your distribution's package manager." >&2
    exit 1
fi

if [ "${1-}" = "--dry-run" ]; then
    echo "apt-get update"
    echo "apt-get install -y libgl1 libxkbcommon0 libegl1 libgles2"
    exit 0
fi

if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        exec sudo "$0" "$@"
    fi
    echo "Error: root privileges are required. Re-run this script with sudo or as root." >&2
    exit 2
fi

apt-get update
apt-get install -y libgl1 libxkbcommon0 libegl1 libgles2
