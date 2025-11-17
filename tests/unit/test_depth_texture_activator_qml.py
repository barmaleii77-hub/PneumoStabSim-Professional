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


def test_depth_texture_activator_caches_property_checks(
    depth_texture_source: str,
) -> None:
    assert "property var _propertyPresenceCache" in depth_texture_source
    assert "_readCachedPresence" in depth_texture_source
    assert "_cachePresenceResult" in depth_texture_source
    assert "property presence check failed" in depth_texture_source


def test_depth_texture_activator_skips_legacy_properties(
    depth_texture_source: str,
) -> None:
    assert "readonly property var _legacyDepthProperties" in depth_texture_source
    assert "_legacyDepthProperties.indexOf(propertyName) !== -1" in depth_texture_source
    assert "legacy property skipped" in depth_texture_source


def test_depth_texture_activator_short_circuits_legacy_checks(
    depth_texture_source: str,
) -> None:
    has_property_start = depth_texture_source.index("function _hasProperty")
    try_set_property_start = depth_texture_source.index(
        "function _trySetProperty", has_property_start
    )
    has_property_block = depth_texture_source[has_property_start:try_set_property_start]

    assert "_legacyDepthProperties.indexOf(propertyName) !== -1" in has_property_block


def test_depth_texture_activator_avoids_removed_qt_properties(
    depth_texture_source: str,
) -> None:
    forbidden_tokens = (
        "explicitDepthTextureEnabled",
        "explicitVelocityTextureEnabled",
        "requiresDepthTexture",
        "requiresVelocityTexture",
    )

    guard_comment = "// Guard rails for Qt 6.10+"
    guard_anchor = "readonly property var _legacyDepthProperties"
    assert guard_anchor in depth_texture_source, (
        "Legacy guard list must remain present to protect against removed Qt properties"
    )

    guard_start = depth_texture_source.index(guard_comment)
    guard_end = (
        depth_texture_source.index("]", depth_texture_source.index(guard_anchor)) + 1
    )
    guard_block = depth_texture_source[guard_start:guard_end]

    for token in forbidden_tokens:
        assert token in guard_block, (
            f"Legacy property {token} must remain documented in the guard list"
        )
        sanitized = (
            depth_texture_source[:guard_start] + depth_texture_source[guard_end:]
        )
        assert token not in sanitized, (
            f"Legacy property {token} must not appear outside the guard block"
        )


def test_depth_texture_activator_reports_safe_read_failures(
    depth_texture_source: str,
) -> None:
    assert "safe read failed" in depth_texture_source


def test_depth_texture_activator_logs_buffer_invocations(
    depth_texture_source: str,
) -> None:
    assert (
        'DepthTextureActivator:", label + "." + methodName + "() called"'
        in depth_texture_source
    )


def test_depth_texture_activator_clears_cache_on_activate(
    depth_texture_source: str,
) -> None:
    activation_start = depth_texture_source.index("function activate(view3d)")
    cache_clear_pos = depth_texture_source.index(
        "_clearPropertyCache()", activation_start
    )

    assert cache_clear_pos > activation_start


def test_depth_texture_activator_tracks_error_guard_flags(
    depth_texture_source: str,
) -> None:
    assert "property bool _missingViewLogged" in depth_texture_source
    assert "property bool _apiUnavailableLogged" in depth_texture_source
