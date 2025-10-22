"""
Comprehensive import test for all project modules
"""
import sys
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


import sys
from pathlib import Path

print("=" * 60)
print("COMPREHENSIVE IMPORT TEST")
print("=" * 60)
print()

# Counters
total_modules = 0
success_count = 0
fail_count = 0
failures = []

# List of modules to test
modules_to_test = [
    # Core
    ("src.core", "Core geometry"),
    ("src.core.geometry", "GeometryParams"),
    # Mechanics
    ("src.mechanics", "Mechanics"),
    ("src.mechanics.components", "Components"),
    ("src.mechanics.constraints", "Constraints"),
    ("src.mechanics.kinematics", "Kinematics"),
    ("src.mechanics.suspension", "Suspension"),
    # Physics
    ("src.physics", "Physics"),
    ("src.physics.forces", "Forces"),
    ("src.physics.integrator", "Integrator"),
    ("src.physics.odes", "ODEs"),
    # Pneumatics
    ("src.pneumo", "Pneumo"),
    ("src.pneumo.cylinder", "Cylinder"),
    ("src.pneumo.enums", "Enums"),
    ("src.pneumo.flow", "Flow"),
    ("src.pneumo.gas_state", "GasState"),
    ("src.pneumo.geometry", "Pneumo Geometry"),
    ("src.pneumo.line", "Line"),
    ("src.pneumo.network", "Network"),
    ("src.pneumo.receiver", "Receiver"),
    ("src.pneumo.system", "System"),
    ("src.pneumo.thermo", "Thermo"),
    ("src.pneumo.valves", "Valves"),
    # Runtime
    ("src.runtime", "Runtime"),
    ("src.runtime.state", "State"),
    ("src.runtime.sync", "Sync"),
    ("src.runtime.sim_loop", "SimLoop"),
    # Common
    ("src.common", "Common"),
    ("src.common.logging_setup", "Logging"),
    ("src.common.csv_export", "CSV Export"),
    ("src.common.errors", "Errors"),
    ("src.common.units", "Units"),
    # UI - NO OpenGL!
    ("src.ui", "UI"),
    ("src.ui.main_window", "MainWindow"),
    ("src.ui.charts", "Charts"),
    ("src.ui.hud", "HUD"),
    ("src.ui.panels", "Panels"),
]

print("Testing module imports...")
print()

for item in modules_to_test:
    if len(item) == 3:
        module_name, desc, optional = item
    else:
        module_name, desc = item
        optional = False

    total_modules += 1
    try:
        __import__(module_name)
        print(f"OK {desc:30} | {module_name}")
        success_count += 1
    except Exception as e:
        if optional:
            print(f"WARN {desc:30} | {module_name} (optional)")
            success_count += 1
        else:
            print(f"FAIL {desc:30} | {module_name}")
            print(f"   Error: {e}")
            fail_count += 1
            failures.append((module_name, str(e)))

print()
print("=" * 60)
print(f"RESULT: {success_count}/{total_modules} successful")
print(f"Success: {success_count}")
print(f"Failures: {fail_count}")
print("=" * 60)

if failures:
    print()
    print("FAILURES:")
    for mod, err in failures:
        print(f"  {mod}: {err}")
    sys.exit(1)
else:
    print()
    print("ALL MODULES IMPORT SUCCESSFULLY!")
    sys.exit(0)
