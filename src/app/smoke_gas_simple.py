"""
Gas system smoke test
Tests complete gas simulation with kinematic scenario
"""

import os
import logging
from src.pneumo.system import create_standard_diagonal_system
from src.pneumo.sim_time import advance_gas
from src.pneumo.enums import ThermoMode, Wheel
from .config_defaults import (
    create_default_system_configuration,
    create_default_gas_network,
)
from src.common.units import DEG2RAD


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


def run_simple_gas_test():
    """Run simplified gas smoke test"""
    logger = setup_gas_logging()
    logger.info("=== SIMPLE GAS SMOKE TEST ===")

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

        logger.info("PASS: System and gas network created")
        logger.info(f"Tank: V={gas_network.tank.V:.6f}m3, p={gas_network.tank.p:.0f}Pa")

        # Test kinematic change
        roll_angles = {
            Wheel.LP: 3.0 * DEG2RAD,
            Wheel.LZ: 3.0 * DEG2RAD,
            Wheel.PP: -3.0 * DEG2RAD,
            Wheel.PZ: -3.0 * DEG2RAD,
        }

        system.update_system_from_lever_angles(roll_angles)
        gas_network.update_pressures_due_to_volume(ThermoMode.ISOTHERMAL)

        logger.info("PASS: Kinematic scenario applied")

        # Short simulation
        for i in range(10):
            advance_gas(0.01, system, gas_network, ThermoMode.ISOTHERMAL, logger)

        logger.info("PASS: Gas simulation completed")

        # Final state
        logger.info("Final pressures:")
        for line_name, gas_state in gas_network.lines.items():
            logger.info(f"  {line_name.value}: {gas_state.p:.0f}Pa")
        logger.info(f"  Tank: {gas_network.tank.p:.0f}Pa")

        return True

    except Exception as e:
        logger.error(f"FAIL: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = run_simple_gas_test()
    print(f"Gas smoke test: {'PASSED' if success else 'FAILED'}")
    exit(0 if success else 1)
