# -*- coding: utf-8 -*-
"""
Quick Test Runner - PROMPT #1 UI Tests
Быстрый запуск тестов для проверки UI
"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run UI tests and display results"""
    print("=" * 70)
    print("?? ЗАПУСК ТЕСТОВ UI - PROMPT #1 VALIDATION")
    print("=" * 70)
    print()
    
    # Test files
    test_files = [
        "tests/ui/test_ui_layout.py",
        "tests/ui/test_panel_functionality.py"
    ]
    
    results = {}
    
    for test_file in test_files:
        test_path = Path(test_file)
        if not test_path.exists():
            print(f"? Test file not found: {test_file}")
            results[test_file] = "NOT_FOUND"
            continue
        
        print(f"\n?? Running: {test_file}")
        print("-" * 70)
        
        try:
            # Run pytest
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Display output
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            # Store result
            if result.returncode == 0:
                results[test_file] = "PASSED"
                print(f"? {test_file}: ALL TESTS PASSED")
            else:
                results[test_file] = "FAILED"
                print(f"? {test_file}: SOME TESTS FAILED")
        
        except subprocess.TimeoutExpired:
            results[test_file] = "TIMEOUT"
            print(f"?? {test_file}: TIMEOUT")
        
        except Exception as e:
            results[test_file] = f"ERROR: {e}"
            print(f"?? {test_file}: ERROR - {e}")
    
    # Summary
    print()
    print("=" * 70)
    print("?? TEST SUMMARY")
    print("=" * 70)
    
    for test_file, status in results.items():
        emoji = "?" if status == "PASSED" else "?" if status == "FAILED" else "??"
        print(f"{emoji} {test_file}: {status}")
    
    print()
    print("=" * 70)
    
    # Overall result
    all_passed = all(status == "PASSED" for status in results.values())
    if all_passed:
        print("?? ALL TESTS PASSED - UI RUSSIFICATION VERIFIED!")
        return 0
    else:
        print("?? SOME TESTS FAILED - CHECK DETAILS ABOVE")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
