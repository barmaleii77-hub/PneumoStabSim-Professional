# -*- coding: utf-8 -*-
"""Runtime Python version guard with sensible minimum and warnings."""

import sys
import os
from typing import Callable

_MIN_VERSION = (3, 10)
_RECOMMENDED_VERSION = (3, 13)


def check_python_compatibility(
    log_warning: Callable[[str], None], log_error: Callable[[str], None]
) -> None:
    """Validate that the interpreter matches the supported range."""
    # Позволяем обходить проверку при явном запросе
    if os.environ.get("PSS_IGNORE_PYTHON_CHECK") == "1":
        log_warning("Python version check bypassed via PSS_IGNORE_PYTHON_CHECK=1")
        return

    version = sys.version_info
    if version < _MIN_VERSION:
        log_error(
            "Python %d.%d+ required. Current interpreter: %d.%d.%d"
            % (_MIN_VERSION[0], _MIN_VERSION[1], version.major, version.minor, version.micro)
        )
        sys.exit(1)

    if version < _RECOMMENDED_VERSION:
        log_warning(
            "Python %d.%d+ detected; Python %d.%d+ is recommended for full support."
            % (version.major, version.minor, _RECOMMENDED_VERSION[0], _RECOMMENDED_VERSION[1])
        )
