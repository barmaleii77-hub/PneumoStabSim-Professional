"""Local stub package overriding external pytest-qt to prevent event loop hangs.

Provides minimal plugin fixture 'qtbot' and no-op hook implementations.
"""

from __future__ import annotations

__all__ = ["qtbot"]
