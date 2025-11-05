#!/usr/bin/env bash
set -euo pipefail

XVFB_ARGS="-screen 0 1920x1080x24 -ac +iglx +extension GLX +render -nolisten tcp"
xvfb-run -s "$XVFB_ARGS" "$@"
