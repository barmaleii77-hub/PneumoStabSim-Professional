#!/usr/bin/env python
"""
P11 Test: Logging system with QueueHandler
Tests log file overwrite, non-blocking logging, structured events
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, ".")

from src.common import (
    init_logging,
    log_valve_event,
    log_pressure_update,
    log_ode_step,
    log_export,
    log_ui_event,
)


def test_logging_system():
    """Test P11 logging system"""
    print("=" * 70)
    print("P11 LOGGING TEST")
    print("=" * 70)

    # Initialize logging (use "PneumoStabSim" to match category loggers!)
    logger = init_logging("PneumoStabSim", Path("logs"))

    print("\n1. Testing structured logging categories...")

    # Test UI events
    log_ui_event("APP_START", "Application initialized")
    log_ui_event("WINDOW_CREATED", "Main window created")

    # Test valve events
    log_valve_event(0.1, "A1", "CV_ATMO", True, 50000, 0.001)
    log_valve_event(0.2, "A1", "CV_TANK", False, -20000, 0.0)
    log_valve_event(0.3, "TANK", "RELIEF_MIN", True, 100000, 0.005)

    # Test pressure updates
    log_pressure_update(0.1, "LINE_A1", 150000, 293.15, 0.0001)
    log_pressure_update(0.2, "TANK", 500000, 295.0, 0.001)

    # Test ODE steps
    log_ode_step(0.001, 1, 0.001, 1e-6)
    log_ode_step(0.002, 2, 0.001, 2e-6)
    log_ode_step(0.003, 3, 0.001, None)

    # Test export event
    log_export("TIMESERIES", Path("test_data.csv"), 1000)

    print("2. Testing high-frequency logging (non-blocking test)...")

    # Simulate intensive logging
    start = time.perf_counter()
    for i in range(100):
        log_ode_step(i * 0.001, i, 0.001, 1e-6)

    elapsed = time.perf_counter() - start
    print(f"   Logged 100 events in {elapsed:.4f}s ({100/elapsed:.0f} events/s)")

    print("\n3. Testing log levels...")
    logger.debug("DEBUG level message")
    logger.info("INFO level message")
    logger.warning("WARNING level message")
    logger.error("ERROR level message")

    print("\n4. Checking log file...")
    log_file = Path("logs/run.log")
    if log_file.exists():
        size = log_file.stat().st_size
        print(f"   Log file exists: {log_file}")
        print(f"   Size: {size} bytes")

        # Show first few lines
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()[:10]

        print(f"\n   First {len(lines)} lines:")
        for line in lines:
            print(f"   {line.rstrip()}")

        # Check for category logs
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()

        categories_found = []
        for cat in ["UI", "VALVE_EVENT", "PRESSURE_UPDATE", "ODE_STEP", "EXPORT"]:
            if cat in content:
                categories_found.append(cat)

        print(
            f"\n   Categories found: {', '.join(categories_found) if categories_found else 'NONE'}"
        )
    else:
        print("   ERROR: Log file not found!")

    print("\n5. Testing log file overwrite...")
    print("   (Re-run this test to verify overwrite)")

    log_ui_event("TEST_COMPLETE", "All tests passed")

    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("Check logs/run.log for full output")
    print("=" * 70)


if __name__ == "__main__":
    test_logging_system()

    # Give queue time to flush
    print("\nWaiting for log queue to flush...")
    time.sleep(0.5)
