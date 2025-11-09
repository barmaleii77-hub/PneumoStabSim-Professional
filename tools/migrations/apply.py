#!/usr/bin/env python3
"""Wrapper CLI for the settings migration runner.

Developers are encouraged to use this thin shim instead of calling the
``src.tools.settings_migrate`` module directly.  It keeps tooling anchored in
``tools/`` alongside other contributor utilities and allows us to evolve the
runner implementation without breaking documentation links.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

from src.tools import settings_migrate


def main(argv: Sequence[str] | None = None) -> int:
    """Delegate to :mod:`src.tools.settings_migrate`."""

    return settings_migrate.main(argv)


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main(sys.argv[1:]))
