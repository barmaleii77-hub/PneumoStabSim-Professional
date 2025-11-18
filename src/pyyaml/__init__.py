"""Compatibility shim for tools expecting ``import pyyaml``.

PyYAML exposes the :mod:`yaml` module, but some external diagnostics import
``pyyaml`` directly.  This package re-exports the public API from
:mod:`yaml` so either import path remains valid once the dependency is
installed.
"""

from __future__ import annotations

from yaml import *  # noqa: F403,F401

__all__ = list(globals().keys())
