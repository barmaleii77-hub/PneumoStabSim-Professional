"""
Smoke test for domain model
Tests basic functionality and invariants
"""

import os
import math
import logging
from datetime import datetime
from src.pneumo.system import create_standard_diagonal_system
from .config_defaults import create_default_system_configuration, get_default_lever_angles
from src.common.units import DEG2RAD


def setup_logging():
    """Setup logging for smoke test"""
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/domain_smoke.log', mode='w'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def test_system_creation(logger):
    """Test system creation from default configuration"""
    logger.info("=== Testing System Creation ===")
    
    try:
        config = create_default_system_configuration()
        
        # Create system using factory function
        system = create_standard_diagonal_system(
            cylinder_specs=config['cylinder_specs'],
            line_configs=config['line_configs'],
            receiver=config['receiver'],
            master_isolation_open=config['master_isolation_open']
        )
        
        logger.info("PASS: System created successfully")
        logger.info(f"  - {len(system.cylinders)} cylinders")
        logger.info(f"  - {len(system.lines)} pneumatic lines")
        logger.info(f"  - Receiver volume: {system.receiver.V:.3f} m3")
        logger.info(f"  - Master isolation: {system.master_isolation_open}")
        
        return system
        
    except Exception as e:
        logger.error(f"FAIL: System creation failed: {e}")
        raise


def test_invariants_validation(system, logger):
    """Test invariants validation"""
    logger.info("\n=== Testing Invariants Validation ===")
    
    try:
        result = system.validate_invariants()
        
        if result['is_valid']:
            logger.info("PASS: All system invariants valid")
        else:
            logger.warning("WARN: Some invariants violated:")
            for error in result['errors']:
                logger.warning(f"  ERROR: {error}")
        
        if result['warnings']:
            logger.info("Warnings found:")
            for warning in result['warnings']:
                logger.info(f"  WARNING: {warning}")
                
        return result['is_valid']
        
    except Exception as e:
        logger.error(f"FAIL: Invariant validation failed: {e}")
        raise


def test_lever_angle_simulation(system, logger):
    """Test lever angle changes and volume calculations"""
    logger.info("\n=== Testing Lever Angle Simulation ===")
    
    try:
        # Get initial volumes
        initial_volumes = system.get_line_volumes()
        logger.info("Initial line volumes:")
        for line, vol_info in initial_volumes.items():
            logger.info(f"  {line.value}: {vol_info['total_volume']:.6f} m3")
        
        # Test angles
        from src.pneumo.enums import Wheel
        test_angles = {
            Wheel.LP: 5.0 * DEG2RAD,   # 5 degrees
            Wheel.PP: 0.0,
            Wheel.LZ: 0.0,
            Wheel.PZ: -3.0 * DEG2RAD   # -3 degrees
        }
        
        logger.info("Applying test angles: LP=5deg, PP=0deg, LZ=0deg, PZ=-3deg")
        
        # Update system with new angles
        system.update_system_from_lever_angles(test_angles)
        
        # Check new volumes
        new_volumes = system.get_line_volumes()
        logger.info("Updated line volumes:")
        for line, vol_info in new_volumes.items():
            logger.info(f"  {line.value}: {vol_info['total_volume']:.6f} m3")
            
        # Log cylinder positions
        logger.info("Cylinder positions after angle changes:")
        for wheel, cylinder in system.cylinders.items():
            logger.info(f"  {wheel.value}: x = {cylinder.x:.4f} m")
            logger.info(f"    Head vol: {cylinder.vol_head():.6f} m3")
            logger.info(f"    Rod vol:  {cylinder.vol_rod():.6f} m3")
        
        # Validate invariants after changes
        post_change_result = system.validate_invariants()
        if post_change_result['is_valid']:
            logger.info("PASS: All invariants still valid after angle changes")
        else:
            logger.warning("WARN: Some invariants violated after changes:")
            for error in post_change_result['errors']:
                logger.warning(f"  ERROR: {error}")
        
        return post_change_result['is_valid']
        
    except Exception as e:
        logger.error(f"FAIL: Lever angle simulation failed: {e}")
        raise


def test_diagonal_connections(system, logger):
    """Test diagonal connection scheme"""
    logger.info("\n=== Testing Diagonal Connection Scheme ===")
    
    try:
        expected_connections = {
            'A1': "LP:ROD <-> PZ:HEAD",
            'B1': "LP:HEAD <-> PZ:ROD", 
            'A2': "PP:ROD <-> LZ:HEAD",
            'B2': "PP:HEAD <-> LZ:ROD"
        }
        
        all_correct = True
        for line_name, line in system.lines.items():
            actual = line.get_connection_description()
            expected = expected_connections[line_name.value]
            
            if actual == expected:
                logger.info(f"PASS: {line_name.value}: {actual}")
            else:
                logger.error(f"FAIL: {line_name.value}: got {actual}, expected {expected}")
                all_correct = False
                
        if all_correct:
            logger.info("PASS: All diagonal connections correct")
        
        return all_correct
        
    except Exception as e:
        logger.error(f"FAIL: Diagonal connection test failed: {e}")
        raise


def run_smoke_test():
    """Run complete smoke test"""
    logger = setup_logging()
    logger.info("="*60)
    logger.info("PNEUMOSTABSIM DOMAIN MODEL SMOKE TEST")
    logger.info(f"Started at: {datetime.now()}")
    logger.info("="*60)
    
    try:
        # Test 1: System creation
        system = test_system_creation(logger)
        
        # Test 2: Initial invariants
        invariants_ok = test_invariants_validation(system, logger)
        
        # Test 3: Diagonal connections
        connections_ok = test_diagonal_connections(system, logger)
        
        # Test 4: Lever angle simulation  
        simulation_ok = test_lever_angle_simulation(system, logger)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("SMOKE TEST SUMMARY")
        logger.info("="*60)
        
        all_passed = invariants_ok and connections_ok and simulation_ok
        
        if all_passed:
            logger.info("SUCCESS: ALL TESTS PASSED - Domain model is working correctly!")
        else:
            logger.warning("WARNING: Some tests failed - check logs above for details")
            
        logger.info(f"Completed at: {datetime.now()}")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"CRASH: SMOKE TEST CRASHED: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = run_smoke_test()
    exit(0 if success else 1)