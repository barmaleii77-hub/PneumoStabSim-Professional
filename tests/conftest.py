"""
Pytest configuration and shared fixtures
"""

import os
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Set up environment variables for testing
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("PYTHONHASHSEED", "0")


@pytest.fixture(scope="session")
def project_root_path():
    """Provide project root path"""
    return project_root


@pytest.fixture
def sample_geometry_params():
    """Provide sample geometry parameters"""
    from src.core.geometry import GeometryParams

    geometry = GeometryParams()
    geometry.wheelbase = 2.5
    geometry.lever_length = 0.4
    geometry.cylinder_inner_diameter = 0.08
    geometry.enforce_track_from_geometry()

    return geometry


@pytest.fixture
def sample_cylinder_params():
    """Provide sample cylinder parameters"""
    return {
        "inner_diameter": 0.08,
        "rod_diameter": 0.035,
        "piston_thickness": 0.02,
        "body_length": 0.25,
        "dead_zone_rod": 0.001,
        "dead_zone_head": 0.001,
    }


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for Qt tests"""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    yield app

    # Cleanup handled by Qt


@pytest.fixture
def geometry_bridge(sample_geometry_params):
    """Create GeometryBridge instance"""
    from src.ui.geometry_bridge import create_geometry_converter

    return create_geometry_converter(
        wheelbase=sample_geometry_params.wheelbase,
        lever_length=sample_geometry_params.lever_length,
        cylinder_diameter=sample_geometry_params.cylinder_inner_diameter,
    )


# Markers for organizing tests
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interactions"
    )
    config.addinivalue_line("markers", "smoke: Lightweight application smoke scenarios")
    config.addinivalue_line("markers", "system: End-to-end system tests")
    config.addinivalue_line("markers", "slow: Tests that take significant time")
    config.addinivalue_line("markers", "gui: Tests requiring GUI/QML")


# Safe exit on test completion
def pytest_unconfigure(config):
    """Clean up after tests"""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        return

    app = QApplication.instance()
    if app is not None:
        app.quit()
