"""
Complete gas system smoke test according to prompt #3 specification
Tests full kinematic scenario with 2-3 seconds simulation
"""

import os
import logging
import math
from datetime import datetime
from ..pneumo.system import create_standard_diagonal_system
from ..pneumo.sim_time import advance_gas
from ..pneumo.enums import ThermoMode, Wheel
from src.core.settings_manager import (
    create_default_gas_network,
    create_default_system_configuration,
)
from ..common.units import PA_ATM, T_AMBIENT


def setup_logging():
    """Setup logging to ./logs/gas_smoke.log"""
    os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/gas_smoke.log", mode="w"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)


def run_complete_gas_smoke_test():
    """Run complete gas smoke test per prompt #3 specification"""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("PNEUMOSTABSIM GAS SMOKE TEST - PROMPT #3")
    logger.info(f"Started at: {datetime.now()}")
    logger.info("=" * 60)

    try:
        # Initialize System from defaults (Prompt #2)
        logger.info("Step 1: Initialize System from defaults")
        config = create_default_system_configuration()

        system = create_standard_diagonal_system(
            cylinder_specs=config["cylinder_specs"],
            line_configs=config["line_configs"],
            receiver=config["receiver"],
            master_isolation_open=config["master_isolation_open"],
        )

        # Initialize GasNetwork with equal starting conditions
        gas_network = create_default_gas_network(system)

        logger.info("System initialized:")
        logger.info(f"  - 4 lines with p={PA_ATM}Pa, T={T_AMBIENT}K")
        logger.info(
            f"  - Receiver: p={gas_network.tank.p}Pa, T={gas_network.tank.T}K, V={gas_network.tank.V:.6f}m?"
        )

        # Log initial masses (calculated from pV/RT)
        for line_name, gas_state in gas_network.lines.items():
            logger.info(f"  - {line_name.value}: m={gas_state.m:.6f}kg")
        logger.info(f"  - Tank: m={gas_network.tank.m:.6f}kg")

        # Simulate kinematic scenario: small lift of front-left and rear-right (roll)
        # Equivalent to 0.01m piston stroke
        logger.info("\nStep 2: Apply kinematic scenario (roll: FL+RR up)")

        # Calculate angles for ~0.01m equivalent stroke
        # Using lever geometry: 0.8m lever, 0.25 fraction
        angle_for_01m = 0.01 / (0.8 * 0.25)  # ~0.05 rad = ~3�

        roll_angles = {
            Wheel.LP: angle_for_01m,  # Left front up
            Wheel.PP: 0.0,  # Right front unchanged
            Wheel.LZ: 0.0,  # Left rear unchanged
            Wheel.PZ: angle_for_01m,  # Right rear up
        }

        logger.info("Applied angles:")
        for wheel, angle in roll_angles.items():
            logger.info(
                f"  {wheel.value}: {angle:.4f}rad ({angle * 180 / math.pi:.2f}�)"
            )

        # Update system kinematics
        system.update_system_from_lever_angles(roll_angles)

        # Update gas pressures due to volume changes (isothermal)
        gas_network.update_pressures_due_to_volume(ThermoMode.ISOTHERMAL)

        # Log pressure changes
        logger.info("Pressures after kinematic update:")
        for line_name, gas_state in gas_network.lines.items():
            logger.info(f"  {line_name.value}: {gas_state.p:.0f}Pa")

        # Run advance_gas for 2-3 seconds with dt=5e-3 (5ms)
        logger.info("\nStep 3: Run gas simulation")
        dt = 5e-3  # 5ms time step as specified
        total_time = 2.5  # 2.5 seconds
        steps = int(total_time / dt)

        logger.info("Simulation parameters:")
        logger.info(f"  - dt: {dt}s")
        logger.info(f"  - Total time: {total_time}s")
        logger.info(f"  - Steps: {steps}")

        # Run simulation
        for step in range(steps):
            current_time = step * dt

            # Log every 0.5 seconds
            if step % int(0.5 / dt) == 0:
                logger.info(
                    f"t={current_time:.2f}s - Tank: {gas_network.tank.p:.0f}Pa, Lines: [{', '.join(f'{gas.p:.0f}' for gas in gas_network.lines.values())}]Pa"
                )

            advance_gas(
                dt,
                system,
                gas_network,
                ThermoMode.ISOTHERMAL,
                log=logger if step % int(1.0 / dt) == 0 else None,
            )  # Detailed log every 1s

        logger.info("\nStep 4: Final state analysis")

        # Final pressures
        logger.info("Final pressures:")
        p_lines = []
        for line_name, gas_state in gas_network.lines.items():
            logger.info(f"  {line_name.value}: {gas_state.p:.0f}Pa")
            p_lines.append(gas_state.p)

        p_tank = gas_network.tank.p
        logger.info(f"  Tank: {p_tank:.0f}Pa")

        # Check invariants
        logger.info("\nStep 5: Invariant validation")
        validation = gas_network.validate_invariants()

        if validation["is_valid"]:
            logger.info("? All invariants valid")
        else:
            logger.error("? Invariant violations:")
            for error in validation["errors"]:
                logger.error(f"  - {error}")

        # Check specific requirements
        all_ok = True

        # Non-negative masses
        for line_name, gas_state in gas_network.lines.items():
            if gas_state.m < 0:
                logger.error(f"? Negative mass in {line_name.value}: {gas_state.m}")
                all_ok = False

        if gas_network.tank.m < 0:
            logger.error(f"? Negative tank mass: {gas_network.tank.m}")
            all_ok = False

        # Non-zero volumes >= residual minimum
        volumes = gas_network.compute_line_volumes()
        for line_name, volume in volumes.items():
            if volume <= 0:
                logger.error(f"? Non-positive volume in {line_name.value}: {volume}")
                all_ok = False

        if gas_network.tank.V <= 0:
            logger.error(f"? Non-positive tank volume: {gas_network.tank.V}")
            all_ok = False

        if all_ok:
            logger.info("? All physical parameters valid")

        # Console output
        print("\n=== CONSOLE SUMMARY ===")
        print(f"Final p_line extremes: {min(p_lines):.0f} - {max(p_lines):.0f}Pa")
        print(f"Final p_tank: {p_tank:.0f}Pa")
        print(f"Invariants: {'PASS' if validation['is_valid'] else 'FAIL'}")
        print(f"Physical checks: {'PASS' if all_ok else 'FAIL'}")

        success = validation["is_valid"] and all_ok
        logger.info(f"\n{'=' * 60}")
        logger.info(f"SMOKE TEST RESULT: {'SUCCESS' if success else 'FAILURE'}")
        logger.info(f"Completed at: {datetime.now()}")
        logger.info(f"{'=' * 60}")

        return success

    except Exception as e:
        logger.error(f"CRASH: Smoke test failed with exception: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = run_complete_gas_smoke_test()
    exit(0 if success else 1)
