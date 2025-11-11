"""Lightweight regression checks for the DepthTextureActivator QML helper."""

from __future__ import annotations

from pathlib import Path

import pytest


QML_PATH = (
    Path(__file__).resolve().parents[2]
    / "assets"
    / "qml"
    / "components"
    / "DepthTextureActivator.qml"
)


@pytest.fixture(scope="module")
def depth_texture_source() -> str:
    """Load the QML source once for this module's tests."""

    return QML_PATH.read_text(encoding="utf-8")


def test_depth_texture_activator_declares_singleton(depth_texture_source: str) -> None:
    lines = [line.strip() for line in depth_texture_source.splitlines() if line.strip()]

    assert lines[0] == "pragma Singleton", (
        "DepthTextureActivator must remain a singleton utility"
    )


@pytest.mark.parametrize(
    "pattern",
    (
        ".depthTextureEnabled =",
        ".depthPrePassEnabled =",
        ".velocityTextureEnabled =",
        ".velocityBufferEnabled =",
    ),
)
def test_depth_texture_activator_avoids_direct_property_assignments(
    depth_texture_source: str, pattern: str
) -> None:
    assert pattern not in depth_texture_source, (
        f"Direct assignments to {pattern} must use helper wrappers"
    )


def test_depth_texture_activator_logs_success_message(
    depth_texture_source: str,
) -> None:
    assert (
        "DepthTextureActivator: Depth/velocity textures successfully activated"
        in depth_texture_source
    ), "Success log output guards future refactors"


def test_depth_texture_activator_reports_status_header(
    depth_texture_source: str,
) -> None:
    assert "=== DepthTextureActivator Status Report ===" in depth_texture_source, (
        "Status report header ensures debugging output remains available"
    )


def test_depth_texture_activator_warns_when_api_unavailable(
    depth_texture_source: str,
) -> None:
    assert (
        "⚠️ DepthTextureActivator: Could not explicitly enable depth textures"
        in depth_texture_source
    ), "Warning log protects manual debugging flows"


def test_depth_texture_activator_caches_property_presence(
    depth_texture_source: str,
) -> None:
    assert "property var _propertyPresenceCache" in depth_texture_source
    assert "function _readCachedPresence" in depth_texture_source
    assert "function _cachePresenceResult" in depth_texture_source


def test_depth_texture_activator_deduplicates_debug_logging(
    depth_texture_source: str,
) -> None:
    assert "property var _diagnosticDedup" in depth_texture_source
    assert "function _logDebugOnce" in depth_texture_source
    assert "_clearPropertyCache()" in depth_texture_source
