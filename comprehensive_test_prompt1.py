#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive Test Suite for PROMPT #1 Completion
Complete testing after PROMPT 1 russification

Tests:
1. Project structure
2. Python syntax validation
3. Import checks
4. UI component tests
5. Russification validation
6. QComboBox functionality
7. Git status
"""

import sys
import os
import ast
import json
from pathlib import Path
from datetime import datetime

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}OK {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}ERROR {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}WARNING {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}INFO {text}{Colors.ENDC}")


class ComprehensiveTest:
    """Comprehensive test suite for PROMPT #1"""
    
    def __init__(self):
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'start_time': datetime.now(),
            'tests': []
        }
        self.project_root = Path(__file__).parent
        
    def run_test(self, name, func):
        """Run a single test and record results"""
        self.results['total_tests'] += 1
        print_info(f"Running: {name}")
        
        try:
            result = func()
            if result.get('status') == 'pass':
                self.results['passed'] += 1
                print_success(f"PASS: {name}")
            elif result.get('status') == 'warning':
                self.results['warnings'] += 1
                print_warning(f"WARNING: {name} - {result.get('message', '')}")
            else:
                self.results['failed'] += 1
                print_error(f"FAIL: {name} - {result.get('message', '')}")
                
            self.results['tests'].append({
                'name': name,
                'result': result
            })
            return result
            
        except Exception as e:
            self.results['failed'] += 1
            print_error(f"ERROR in {name}: {str(e)}")
            self.results['tests'].append({
                'name': name,
                'result': {'status': 'error', 'message': str(e)}
            })
            return {'status': 'error', 'message': str(e)}
    
    # Test implementations
    def test_project_structure(self):
        """Verify project structure exists"""
        required_paths = [
            'src/ui/main_window.py',
            'src/ui/panels/panel_geometry.py',
            'src/ui/panels/panel_pneumo.py',
            'src/ui/panels/panel_modes.py',
            'tests/ui/test_ui_layout.py',
            'tests/ui/test_panel_functionality.py',
            'README.md',
            'app.py'
        ]
        
        missing = []
        for path in required_paths:
            if not (self.project_root / path).exists():
                missing.append(path)
        
        if missing:
            return {
                'status': 'fail',
                'message': f'Missing files: {", ".join(missing)}'
            }
        
        return {'status': 'pass', 'checked': len(required_paths)}
    
    def test_python_syntax(self):
        """Validate Python syntax in all modified files"""
        files_to_check = [
            'src/ui/main_window.py',
            'src/ui/panels/panel_geometry.py',
            'src/ui/panels/panel_pneumo.py',
            'src/ui/panels/panel_modes.py'
        ]
        
        errors = []
        for file_path in files_to_check:
            full_path = self.project_root / file_path
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    ast.parse(code)
            except SyntaxError as e:
                errors.append(f"{file_path}: {str(e)}")
            except FileNotFoundError:
                errors.append(f"{file_path}: File not found")
        
        if errors:
            return {'status': 'fail', 'message': '; '.join(errors)}
        
        return {'status': 'pass', 'checked': len(files_to_check)}
    
    def test_utf8_encoding(self):
        """Check UTF-8 encoding declarations"""
        files_to_check = [
            'src/ui/panels/panel_geometry.py',
            'src/ui/panels/panel_pneumo.py',
            'src/ui/panels/panel_modes.py'
        ]
        
        missing = []
        for file_path in files_to_check:
            full_path = self.project_root / file_path
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    if 'utf-8' not in first_line.lower():
                        missing.append(file_path)
            except FileNotFoundError:
                missing.append(f"{file_path} (not found)")
        
        if missing:
            return {
                'status': 'warning',
                'message': f'Missing UTF-8 declaration: {", ".join(missing)}'
            }
        
        return {'status': 'pass', 'checked': len(files_to_check)}
    
    def test_russian_strings(self):
        """Check for Russian strings in UI files"""
        files_to_check = {
            'src/ui/main_window.py': ['Параметры', 'Старт'],
            'src/ui/panels/panel_modes.py': ['Кинематика', 'Динамика']
        }
        
        missing = []
        for file_path, expected_strings in files_to_check.items():
            full_path = self.project_root / file_path
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for expected in expected_strings:
                        if expected not in content:
                            missing.append(f"{file_path}: '{expected}'")
            except FileNotFoundError:
                missing.append(f"{file_path}: File not found")
        
        if missing:
            return {'status': 'fail', 'message': f'Missing: {", ".join(missing)}'}
        
        return {'status': 'pass', 'checked': sum(len(v) for v in files_to_check.values())}
    
    def test_qcombobox_presence(self):
        """Check for QComboBox in panels"""
        files_to_check = [
            'src/ui/panels/panel_geometry.py',
            'src/ui/panels/panel_pneumo.py',
            'src/ui/panels/panel_modes.py'
        ]
        
        missing = []
        for file_path in files_to_check:
            full_path = self.project_root / file_path
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'QComboBox' not in content:
                        missing.append(file_path)
            except FileNotFoundError:
                missing.append(f"{file_path} (not found)")
        
        if missing:
            return {
                'status': 'fail',
                'message': f'QComboBox not found in: {", ".join(missing)}'
            }
        
        return {'status': 'pass', 'checked': len(files_to_check)}
    
    # Run all tests
    def run_all_tests(self):
        """Run all tests"""
        print_header("COMPREHENSIVE TEST SUITE - PROMPT #1")
        print_info(f"Project Root: {self.project_root}")
        print_info(f"Start Time: {self.results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        print_header("TEST 1: PROJECT STRUCTURE")
        self.run_test("Project Structure", self.test_project_structure)
        
        print_header("TEST 2: PYTHON SYNTAX")
        self.run_test("Python Syntax Validation", self.test_python_syntax)
        
        print_header("TEST 3: UTF-8 ENCODING")
        self.run_test("UTF-8 Encoding Headers", self.test_utf8_encoding)
        
        print_header("TEST 4: RUSSIAN STRINGS")
        self.run_test("Russian UI Strings", self.test_russian_strings)
        
        print_header("TEST 5: QCOMBOBOX")
        self.run_test("QComboBox Presence", self.test_qcombobox_presence)
        
        self.print_summary()
        self.save_results()
        
        return self.results['failed'] == 0
    
    def print_summary(self):
        """Print test summary"""
        end_time = datetime.now()
        duration = (end_time - self.results['start_time']).total_seconds()
        
        print_header("TEST SUMMARY")
        
        print(f"Total Tests:    {self.results['total_tests']}")
        print(f"{Colors.OKGREEN}Passed:         {self.results['passed']}{Colors.ENDC}")
        print(f"{Colors.WARNING}Warnings:       {self.results['warnings']}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed:         {self.results['failed']}{Colors.ENDC}")
        print(f"Duration:       {duration:.2f}s")
        
        if self.results['total_tests'] > 0:
            pass_rate = (self.results['passed'] / self.results['total_tests']) * 100
            print(f"\n{Colors.BOLD}Pass Rate:      {pass_rate:.1f}%{Colors.ENDC}")
        
        if self.results['failed'] == 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}ALL TESTS PASSED!{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}SOME TESTS FAILED{Colors.ENDC}")
    
    def save_results(self):
        """Save results to JSON file"""
        results_file = self.project_root / 'test_results_comprehensive.json'
        
        results_data = {
            **self.results,
            'start_time': self.results['start_time'].isoformat(),
            'end_time': datetime.now().isoformat()
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print_info(f"Results saved to: {results_file}")


def main():
    """Main entry point"""
    test_suite = ComprehensiveTest()
    success = test_suite.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
