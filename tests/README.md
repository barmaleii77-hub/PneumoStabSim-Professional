# PneumoStabSim Test Suite

Automated testing infrastructure for PneumoStabSim project.

## ?? Structure

```
tests/
??? __init__.py                 # Test package initialization
??? conftest.py                 # Pytest configuration & fixtures
??? unit/                       # Unit tests
?   ??? test_geometry.py       # Geometry calculations
?   ??? test_kinematics.py     # Kinematics tests
?   ??? test_pneumatics.py     # Pneumatic system
?   ??? test_ui_components.py  # UI widgets
??? integration/                # Integration tests
?   ??? test_python_qml.py     # Python?QML communication
?   ??? test_simulation.py     # Full simulation loop
?   ??? test_panels.py         # UI panels integration
??? system/                     # System tests
?   ??? test_full_app.py       # Full application test
??? fixtures/                   # Test data & fixtures
    ??? geometry_data.json
    ??? simulation_scenarios.json
```

## ?? Running Tests

### All Tests
```bash
pytest
```

### Specific Test Suite
```bash
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests
pytest tests/system/                  # System tests
```

### With Coverage
```bash
pytest --cov=src --cov-report=html
```

### Verbose Output
```bash
pytest -v
```

### Specific Test
```bash
pytest tests/unit/test_geometry.py::test_geometry_bridge
```

## ?? Test Coverage Goals

- **Unit Tests:** >80% coverage
- **Integration Tests:** Key workflows tested
- **System Tests:** End-to-end scenarios

## ?? Writing Tests

### Unit Test Example
```python
import pytest
from src.mechanics.kinematics import CylinderKinematics
from src.core.geometry import Point2

def test_cylinder_kinematics():
    """Test cylinder kinematics calculations"""
    # Arrange
    kinematics = CylinderKinematics(
        frame_hinge=Point2(0, 0),
        inner_diameter=0.08,
        rod_diameter=0.035,
        piston_thickness=0.02,
        body_length=0.25,
        dead_zone_rod=0.001,
        dead_zone_head=0.001
    )
    
    # Act
    # ... perform test
    
    # Assert
    assert result == expected
```

### Integration Test Example
```python
import pytest
from src.ui.main_window import MainWindow

def test_geometry_update_flow(qapp):
    """Test geometry parameter update through entire stack"""
    window = MainWindow()
    
    # Update geometry
    window.update_geometry({'frameLength': 2500.0})
    
    # Verify QML received update
    assert window.qml_root.property('frameLength') == 2500.0
```

## ?? Test Naming Convention

- `test_<module>_<function>` for unit tests
- `test_<workflow>_<scenario>` for integration tests
- `test_<feature>_end_to_end` for system tests

## ? Performance Tests

Performance benchmarks in `tests/performance/`:
- Simulation loop speed
- Rendering FPS
- Memory usage

## ?? Debugging Failed Tests

```bash
# Run with pdb on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Stop on first failure
pytest -x
```

## ?? Dependencies

Test dependencies (see `requirements-dev.txt`):
- pytest
- pytest-qt
- pytest-cov
- pytest-benchmark

## ?? CI/CD Integration

Tests run automatically on:
- Every commit (via GitHub Actions)
- Pull requests
- Before releases

## ?? Coverage Reports

HTML coverage reports generated in `htmlcov/` directory.
View with: `open htmlcov/index.html`

---

**Last Updated:** 2025-01-05  
**Test Framework:** pytest  
**Coverage Tool:** pytest-cov
