"""PneumoStabSim source package bootstrap."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root (parent of ``src``) is available on ``sys.path`` when
# the package is imported from source checkouts. This allows modules under
# ``src`` to access configuration helpers exposed from the top-level ``config``
# package without requiring ``PYTHONPATH`` tweaks.
_SRC_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SRC_DIR.parent
_root_str = str(_REPO_ROOT)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

__all__: list[str] = []
