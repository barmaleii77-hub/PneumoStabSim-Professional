"""
Complete gas smoke test - ASCII only
"""

import os
import logging
import math
from datetime import datetime
from ..pneumo.system import create_standard_diagonal_system
from ..pneumo.sim_time import advance_gas
from ..pneumo.enums import ThermoMode, Wheel
from .config_defaults import (
    create_default_system_configuration, create_default_gas_network,
    get_default_lever_angles
)
from ..common.units import DEG2RAD, PA_ATM, T_AMBIENT


def run_full_smoke_test():
    """Run complete gas smoke test"""
    # Setup logging
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/gas_smoke.log', mode='w'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("=== COMPLETE GAS SMOKE TEST ===")
    
    try:
        # Step 1: Initialize system
        config = create_default_system_configuration()
        system = create_standard_diagonal_system(
            cylinder_specs=config['cylinder_specs'],
            line_configs=config['line_configs'],
            receiver=config['receiver'],
            master_isolation_open=False
        )
        gas_network = create_default_gas_network(system)
        
        logger.info("System initialized successfully")
        logger.info(f"Initial tank: p={gas_network.tank.p:.0f}Pa, V={gas_network.tank.V:.6f}m3")
        
        # Step 2: Apply kinematic scenario (0.01m equivalent stroke)
        roll_angles = {
            Wheel.LP: 0.05,   # ~3 degrees
            Wheel.PP: 0.0,
            Wheel.LZ: 0.0, 
            Wheel.PZ: 0.05    # ~3 degrees
        }
        
        system.update_system_from_lever_angles(roll_angles)
        gas_network.update_pressures_due_to_volume(ThermoMode.ISOTHERMAL)
        
        logger.info("Kinematic scenario applied")
        
        # Step 3: Run simulation for 2.5 seconds with dt=5ms
        dt = 0.005  # 5ms
        total_time = 2.5
        steps = int(total_time / dt)
        
        logger.info(f"Starting simulation: {steps} steps, dt={dt}s")
        
        for step in range(steps):
            current_time = step * dt
            
            # Log every 0.5 seconds
            if step % 100 == 0:  # Every 0.5s
                pressures = [gas.p for gas in gas_network.lines.values()]
                logger.info(f"t={current_time:.2f}s: Tank={gas_network.tank.p:.0f}Pa, Lines=[{min(pressures):.0f}-{max(pressures):.0f}]Pa")
            
            advance_gas(dt, system, gas_network, ThermoMode.ISOTHERMAL)
        
        # Step 4: Final validation
        logger.info("=== FINAL RESULTS ===")
        
        final_pressures = []
        for line_name, gas_state in gas_network.lines.items():
            logger.info(f"{line_name.value}: {gas_state.p:.0f}Pa")
            final_pressures.append(gas_state.p)
        
        logger.info(f"Tank: {gas_network.tank.p:.0f}Pa")
        
        # Validate invariants
        validation = gas_network.validate_invariants()
        
        # Check masses and volumes
        all_valid = validation['is_valid']
        
        for line_name, gas_state in gas_network.lines.items():
            if gas_state.m < 0:
                logger.error(f"Negative mass in {line_name.value}")
                all_valid = False
        
        if gas_network.tank.m < 0:
            logger.error("Negative tank mass")
            all_valid = False
        
        volumes = gas_network.compute_line_volumes()
        for line_name, volume in volumes.items():
            if volume <= 0:
                logger.error(f"Non-positive volume in {line_name.value}")
                all_valid = False
        
        # Console output
        print(f"\n=== FINAL CONSOLE OUTPUT ===")
        print(f"p_line range: {min(final_pressures):.0f} - {max(final_pressures):.0f}Pa")
        print(f"p_tank: {gas_network.tank.p:.0f}Pa")
        print(f"Validation: {'PASS' if all_valid else 'FAIL'}")
        
        logger.info(f"Test result: {'SUCCESS' if all_valid else 'FAILURE'}")
        
        return all_valid
        
    except Exception as e:
        logger.error(f"Test crashed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = run_full_smoke_test()
    exit(0 if success else 1)