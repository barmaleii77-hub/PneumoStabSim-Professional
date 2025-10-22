"""
Gas system smoke test
Tests complete gas simulation with kinematic scenario
"""

import os
import logging
import math
from datetime import datetime
from ..pneumo.system import create_standard_diagonal_system
from ..pneumo.sim_time import run_gas_simulation
from ..pneumo.enums import ThermoMode, Wheel
from .config_defaults import (
    create_default_system_configuration,
    create_default_gas_network,
    get_default_lever_angles,
    get_default_gas_parameters,
)
from ..common.units import DEG2RAD


def setup_gas_logging():
    """Setup logging for gas smoke test"""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/gas_smoke.log", mode="w"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)


def create_test_system_and_network(logger):
    """Create test pneumatic system and gas network"""
    logger.info("=== Creating Test System and Gas Network ===")

    try:
        # Create system from defaults
        config = create_default_system_configuration()

        system = create_standard_diagonal_system(
            cylinder_specs=config["cylinder_specs"],
            line_configs=config["line_configs"],
            receiver=config["receiver"],
            master_isolation_open=config["master_isolation_open"],
        )

        # Create gas network
        gas_network = create_default_gas_network(system)

        logger.info("PASS: System and gas network created successfully")
        logger.info(f"  - {len(system.cylinders)} cylinders")
        logger.info(f"  - {len(system.lines)} pneumatic lines")
        logger.info(f"  - {len(gas_network.lines)} gas line states")
        logger.info(
            f"  - Tank: V={gas_network.tank.V:.6f}m³, p={gas_network.tank.p:.0f}Pa"
        )

        return system, gas_network

    except Exception as e:
        logger.error(f"FAIL: System creation failed: {e}")
        raise


def simulate_kinematic_scenario(system, gas_network, logger):
    """Simulate kinematic scenario: roll motion (left up, right down)"""
    logger.info("\n=== Simulating Kinematic Scenario ===")

    try:
        # Initial state
        initial_angles = get_default_lever_angles()
        logger.info("Initial lever angles (all horizontal):")
        for wheel, angle in initial_angles.items():
            logger.info(f"  {wheel.value}: {angle * 180/math.pi:.1f}°")

        # Apply initial angles
        system.update_system_from_lever_angles(initial_angles)

        # Log initial volumes and gas state
        volumes = gas_network.compute_line_volumes()
        logger.info("Initial line volumes:")
        for line_name, volume in volumes.items():
            gas_state = gas_network.lines[line_name]
            logger.info(
                f"  {line_name.value}: V={volume:.6f}m³, p={gas_state.p:.0f}Pa, m={gas_state.m:.6f}kg"
            )

        # Simulate roll scenario: left side up 0.01m equivalent, right side down 0.01m equivalent
        # This represents body roll where left wheels rise and right wheels drop
        roll_angles = {
            Wheel.LP: 3.0 * DEG2RAD,  # Left front up 3°
            Wheel.LZ: 3.0 * DEG2RAD,  # Left rear up 3°
            Wheel.PP: -3.0 * DEG2RAD,  # Right front down 3°
            Wheel.PZ: -3.0 * DEG2RAD,  # Right rear down 3°
        }

        logger.info("Applying roll scenario (left up, right down):")
        for wheel, angle in roll_angles.items():
            logger.info(f"  {wheel.value}: {angle * 180/math.pi:.1f}°")

        # Apply roll angles
        system.update_system_from_lever_angles(roll_angles)

        # Update gas network with new volumes
        gas_network.update_pressures_due_to_volume(ThermoMode.ISOTHERMAL)

        # Log updated volumes and pressures
        new_volumes = gas_network.compute_line_volumes()
        logger.info("Updated line volumes after roll:")
        for line_name, volume in new_volumes.items():
            gas_state = gas_network.lines[line_name]
            initial_vol = volumes[line_name]
            vol_change = ((volume - initial_vol) / initial_vol) * 100
            logger.info(
                f"  {line_name.value}: V={volume:.6f}m³ ({vol_change:+.2f}%), p={gas_state.p:.0f}Pa"
            )

        return True

    except Exception as e:
        logger.error(f"FAIL: Kinematic simulation failed: {e}")
        raise


def run_gas_time_simulation(system, gas_network, logger):
    """Run gas simulation over time"""
    logger.info("\n=== Running Gas Time Simulation ===")

    try:
        gas_params = get_default_gas_parameters()

        # Simulation parameters
        total_time = 3.0  # 3 seconds
        dt = gas_params["dt"]  # 5ms time step
        thermo_mode = gas_params["thermo_mode"]
        log_interval = 0.5  # Log every 500ms

        logger.info("Simulation parameters:")
        logger.info(f"  Total time: {total_time}s")
        logger.info(f"  Time step: {dt}s")
        logger.info(f"  Thermo mode: {thermo_mode.value}")
        logger.info(f"  Steps: {int(total_time/dt)}")

        # Initial validation
        validation = gas_network.validate_invariants()
        if not validation["is_valid"]:
            logger.warning("Initial validation failed:")
            for error in validation["errors"]:
                logger.warning(f"  ERROR: {error}")

        # Run simulation
        history = run_gas_simulation(
            total_time=total_time,
            dt=dt,
            system=system,
            net=gas_network,
            thermo_mode=thermo_mode,
            log_interval=log_interval,
            log=logger,
        )

        # Analyze results
        logger.info("\n=== Simulation Results Analysis ===")

        # Final pressures
        logger.info("Final line pressures:")
        for line_name, gas_state in gas_network.lines.items():
            logger.info(f"  {line_name.value}: {gas_state.p:.0f}Pa")

        logger.info(f"Final tank pressure: {gas_network.tank.p:.0f}Pa")

        # Pressure ranges during simulation
        logger.info("Pressure ranges during simulation:")
        for line_name in gas_network.lines.keys():
            pressures = history["line_pressures"][line_name]
            min_p = min(pressures)
            max_p = max(pressures)
            logger.info(
                f"  {line_name.value}: {min_p:.0f} - {max_p:.0f}Pa (range: {max_p-min_p:.0f}Pa)"
            )

        tank_pressures = history["tank_pressure"]
        logger.info(f"  Tank: {min(tank_pressures):.0f} - {max(tank_pressures):.0f}Pa")

        return history

    except Exception as e:
        logger.error(f"FAIL: Gas simulation failed: {e}")
        raise


def validate_final_state(gas_network, history, logger):
    """Validate final simulation state"""
    logger.info("\n=== Final State Validation ===")

    try:
        # Validate gas network invariants
        validation = gas_network.validate_invariants()

        if validation["is_valid"]:
            logger.info("PASS: All gas network invariants valid")
        else:
            logger.warning("WARN: Some invariants violated:")
            for error in validation["errors"]:
                logger.warning(f"  ERROR: {error}")

        if validation["warnings"]:
            logger.info("Warnings:")
            for warning in validation["warnings"]:
                logger.info(f"  WARNING: {warning}")

        # Check for physical reasonableness
        all_reasonable = True

        # Check masses are non-negative
        for line_name, gas_state in gas_network.lines.items():
            if gas_state.m < 0:
                logger.error(f"FAIL: Negative mass in {line_name.value}: {gas_state.m}")
                all_reasonable = False

        if gas_network.tank.m < 0:
            logger.error(f"FAIL: Negative tank mass: {gas_network.tank.m}")
            all_reasonable = False

        # Check volumes are above minimum
        volumes = gas_network.compute_line_volumes()
        for line_name, volume in volumes.items():
            if volume <= 0:
                logger.error(
                    f"FAIL: Non-positive volume in {line_name.value}: {volume}"
                )
                all_reasonable = False

        if gas_network.tank.V <= 0:
            logger.error(f"FAIL: Non-positive tank volume: {gas_network.tank.V}")
            all_reasonable = False

        # Check pressures are reasonable (not extreme)
        for line_name, gas_state in gas_network.lines.items():
            if gas_state.p > 1e6:  # > 10 bar
                logger.warning(
                    f"WARN: Very high pressure in {line_name.value}: {gas_state.p:.0f}Pa"
                )

        if gas_network.tank.p > 1e6:
            logger.warning(f"WARN: Very high tank pressure: {gas_network.tank.p:.0f}Pa")

        if all_reasonable:
            logger.info("PASS: All physical parameters are reasonable")

        return validation["is_valid"] and all_reasonable

    except Exception as e:
        logger.error(f"FAIL: Final validation failed: {e}")
        return False


def run_gas_smoke_test():
    """Run complete gas smoke test"""
    logger = setup_gas_logging()
    logger.info("=" * 70)
    logger.info("PNEUMOSTABSIM GAS SYSTEM SMOKE TEST")
    logger.info(f"Started at: {datetime.now()}")
    logger.info("=" * 70)

    try:
        # Test 1: Create system and gas network
        system, gas_network = create_test_system_and_network(logger)

        # Test 2: Simulate kinematic scenario
        kinematic_ok = simulate_kinematic_scenario(system, gas_network, logger)

        # Test 3: Run gas time simulation
        history = run_gas_time_simulation(system, gas_network, logger)

        # Test 4: Validate final state
        validation_ok = validate_final_state(gas_network, history, logger)

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("GAS SMOKE TEST SUMMARY")
        logger.info("=" * 70)

        all_passed = kinematic_ok and validation_ok

        if all_passed:
            logger.info("SUCCESS: ALL TESTS PASSED - Gas system working correctly!")
        else:
            logger.warning("WARNING: Some tests failed - check logs above for details")

        logger.info(f"Completed at: {datetime.now()}")

        # Output key results to console
        print("\n=== CONSOLE SUMMARY ===")
        print(f"Gas smoke test: {'PASSED' if all_passed else 'FAILED'}")
        print(f"Final tank pressure: {gas_network.tank.p:.0f}Pa")
        print("Final line pressures:")
        for line_name, gas_state in gas_network.lines.items():
            print(f"  {line_name.value}: {gas_state.p:.0f}Pa")
        print(f"Simulation steps completed: {len(history['time'])}")

        return all_passed

    except Exception as e:
        logger.error(f"CRASH: GAS SMOKE TEST CRASHED: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = run_gas_smoke_test()
    exit(0 if success else 1)
