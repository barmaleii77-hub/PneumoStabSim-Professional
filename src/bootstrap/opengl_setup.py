# -*- coding: utf-8 -*-
"""OpenGL 4.5+ Surface Format Configuration"""

from __future__ import annotations

import logging
import os
from typing import Callable

logger = logging.getLogger(__name__)


def configure_opengl_45_profile(
    log_error: Callable[[str], None] | None = None,
) -> tuple[bool, str | None]:
    """Настройка OpenGL 4.5 Core Profile перед созданием QApplication."""
    try:
        from PySide6.QtGui import QSurfaceFormat

        surface_format = QSurfaceFormat()
        surface_format.setVersion(4, 5)
        surface_format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        surface_format.setDepthBufferSize(24)
        surface_format.setStencilBufferSize(8)
        surface_format.setSamples(4)
        surface_format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)

        QSurfaceFormat.setDefaultFormat(surface_format)

        logger.info("✅ OpenGL 4.5 Core Profile configured")
        return True, None

    except ImportError as e:
        reason = f"Failed to import PySide6: {e}"
        if log_error:
            log_error(reason)
        return False, reason

    except Exception as e:
        reason = f"OpenGL setup failed: {e}"
        if log_error:
            log_error(reason)
        return False, reason


def setup_opengl_environment() -> None:
    """Настройка переменных окружения для OpenGL 4.5+"""
    os.environ["QSG_RHI_BACKEND"] = "opengl"
    os.environ.setdefault("QT_OPENGL_VERSION", "4.5")
    os.environ.setdefault("QT_OPENGL_PROFILE", "core")
    os.environ.setdefault("QSG_INFO", "1")

    logger.info("OpenGL environment configured: 4.5 Core")
