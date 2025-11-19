"""Local stub plugin module shadowing real pytest-qt.

Implements minimal hook functions so pytest does not attempt to run GUI event
loop processing that can hang in headless CI. The real package is blocked via
PYTEST_DISABLE_PLUGIN_AUTOLOAD and local module precedence on sys.path.
"""

from __future__ import annotations
import time
from typing import Callable


class _StubQtBot:
    def wait(self, ms: int) -> None:
        time.sleep(ms / 1000.0)

    def waitUntil(
        self, cond: Callable[[], bool], timeout: int = 1000, interval: int = 25
    ) -> None:  # noqa: D401
        end = time.time() + timeout / 1000.0
        while time.time() < end:
            try:
                if cond():
                    return None
            except Exception:
                pass
            time.sleep(interval / 1000.0)
        raise AssertionError("waitUntil timeout (local pytestqt stub)")


qtbot = _StubQtBot()

# Pytest hook shims (no-op) -------------------------------------------------


def pytest_configure(config):  # noqa: D401
    return None


def pytest_unconfigure(config):  # noqa: D401
    return None


def pytest_sessionstart(session):  # noqa: D401
    return None


def pytest_sessionfinish(session, exitstatus):  # noqa: D401
    return None


def pytest_runtest_setup(item):  # noqa: D401
    return None


def pytest_runtest_call(item):  # noqa: D401
    return None


def pytest_runtest_teardown(item, nextitem):  # noqa: D401
    return None


__all__ = ["qtbot"]
