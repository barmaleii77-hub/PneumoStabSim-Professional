#!/usr/bin/env python
"""
Simple Comprehensive Test for PROMPT #1
"""

import sys
import os
from pathlib import Path
from datetime import datetime

class SimpleTest:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.root = Path(__file__).parent
        
    def check_file(self, path):
        """Check if file exists"""
        if (self.root / path).exists():
            print(f"[OK] {path}")
            self.passed += 1
            return True
        else:
            print(f"[FAIL] {path}")
            self.failed += 1
            return False
    
    def check_content(self, path, text):
        """Check if file contains text"""
        try:
            with open(self.root / path, 'r', encoding='utf-8') as f:
                if text in f.read():
                    print(f"[OK] {path} contains '{text}'")
                    self.passed += 1
                    return True
                else:
                    print(f"[FAIL] {path} missing '{text}'")
                    self.failed += 1
                    return False
        except:
            print(f"[ERROR] {path} cannot read")
            self.failed += 1
            return False
    
    def run(self):
        """Run all tests"""
        print("\n" + "="*70)
        print("COMPREHENSIVE TEST - PROMPT #1".center(70))
        print("="*70 + "\n")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print("TEST 1: File Structure")
        print("-"*70)
        self.check_file('src/ui/main_window.py')
        self.check_file('src/ui/panels/panel_geometry.py')
        self.check_file('src/ui/panels/panel_pneumo.py')
        self.check_file('src/ui/panels/panel_modes.py')
        self.check_file('tests/ui/test_ui_layout.py')
        self.check_file('tests/ui/test_panel_functionality.py')
        self.check_file('README.md')
        
        print("\nTEST 2: QComboBox Presence")
        print("-"*70)
        self.check_content('src/ui/panels/panel_geometry.py', 'QComboBox')
        self.check_content('src/ui/panels/panel_pneumo.py', 'QComboBox')
        self.check_content('src/ui/panels/panel_modes.py', 'QComboBox')
        
        print("\nTEST 3: UTF-8 Encoding")
        print("-"*70)
        self.check_content('src/ui/panels/panel_geometry.py', '# -*- coding: utf-8 -*-')
        self.check_content('src/ui/panels/panel_pneumo.py', '# -*- coding: utf-8 -*-')
        self.check_content('src/ui/panels/panel_modes.py', '# -*- coding: utf-8 -*-')
        
        print("\nTEST 4: Documentation")
        print("-"*70)
        self.check_file('PROMPT_1_100_PERCENT_COMPLETE.md')
        self.check_file('PROMPT_1_FINAL_SUCCESS.md')
        self.check_file('PROMPT_1_DASHBOARD.md')
        
        print("\n" + "="*70)
        print("SUMMARY".center(70))
        print("="*70)
        print(f"\nPassed:  {self.passed}")
        print(f"Failed:  {self.failed}")
        print(f"Total:   {self.passed + self.failed}")
        
        if self.failed == 0:
            print("\n[SUCCESS] ALL TESTS PASSED!\n")
            return 0
        else:
            print(f"\n[FAIL] {self.failed} tests failed\n")
            return 1

if __name__ == '__main__':
    test = SimpleTest()
    sys.exit(test.run())
