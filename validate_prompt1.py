# -*- coding: utf-8 -*-
"""
Final Validation Script - PROMPT #1
Финальная проверка всех изменений перед Git commit
"""

import sys
from pathlib import Path
from typing import List, Tuple

def check_file_exists(filepath: str) -> Tuple[bool, str]:
    """Check if file exists and return status"""
    path = Path(filepath)
    if path.exists():
        size = path.stat().st_size
        return True, f"? {filepath} ({size} bytes)"
    else:
        return False, f"? {filepath} NOT FOUND"

def check_russian_encoding(filepath: str) -> Tuple[bool, str]:
    """Check if file has correct UTF-8 encoding with Russian text"""
    path = Path(filepath)
    if not path.exists():
        return False, f"? {filepath} not found"
    
    try:
        content = path.read_text(encoding='utf-8')
        
        # Check for Russian characters
        russian_chars = any(ord(c) >= 0x0400 and ord(c) <= 0x04FF for c in content)
        
        if russian_chars:
            return True, f"? {filepath} has Russian text (UTF-8)"
        else:
            return False, f"?? {filepath} has no Russian text"
    
    except UnicodeDecodeError:
        return False, f"? {filepath} encoding error"
    except Exception as e:
        return False, f"? {filepath} error: {e}"

def validate_prompt1_changes():
    """Validate all PROMPT #1 changes"""
    
    print("=" * 80)
    print("?? PROMPT #1 FINAL VALIDATION")
    print("=" * 80)
    print()
    
    # Files to check
    modified_files = [
        "src/ui/main_window.py",
        "src/ui/panels/panel_geometry.py",
        "src/ui/panels/panel_pneumo.py"
    ]
    
    test_files = [
        "tests/ui/__init__.py",
        "tests/ui/test_ui_layout.py",
        "tests/ui/test_panel_functionality.py",
        "run_ui_tests.py"
    ]
    
    report_files = [
        "reports/ui/STEP_1_COMPLETE.md",
        "reports/ui/strings_changed_step1.csv",
        "reports/ui/STEP_2_PANELS_COMPLETE.md",
        "reports/ui/strings_changed_complete.csv",
        "reports/ui/PROGRESS_UPDATE.md",
        "reports/ui/STEP_4_TESTS_COMPLETE.md",
        "reports/ui/FINAL_STATUS_REPORT.md",
        "reports/ui/GIT_COMMIT_INSTRUCTIONS.md",
        "reports/ui/PROMPT_1_FINAL_COMPLETION.md",
        "reports/ui/progress_summary.csv",
        "PROMPT_1_USER_SUMMARY.md"
    ]
    
    all_files = modified_files + test_files + report_files
    
    # Track results
    results = {
        'exists': [],
        'missing': [],
        'russian_ok': [],
        'russian_missing': []
    }
    
    # Check file existence
    print("?? Checking file existence...")
    print("-" * 80)
    for filepath in all_files:
        exists, msg = check_file_exists(filepath)
        print(msg)
        if exists:
            results['exists'].append(filepath)
        else:
            results['missing'].append(filepath)
    
    print()
    
    # Check Russian encoding (only for modified files)
    print("???? Checking Russian text encoding...")
    print("-" * 80)
    for filepath in modified_files:
        has_russian, msg = check_russian_encoding(filepath)
        print(msg)
        if has_russian:
            results['russian_ok'].append(filepath)
        else:
            results['russian_missing'].append(filepath)
    
    print()
    
    # Summary
    print("=" * 80)
    print("?? VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Files checked: {len(all_files)}")
    print(f"  ? Exist: {len(results['exists'])}/{len(all_files)}")
    print(f"  ? Missing: {len(results['missing'])}/{len(all_files)}")
    print()
    print(f"Russian encoding checked: {len(modified_files)}")
    print(f"  ? Has Russian: {len(results['russian_ok'])}/{len(modified_files)}")
    print(f"  ?? No Russian: {len(results['russian_missing'])}/{len(modified_files)}")
    print()
    
    # Check if ready for commit
    ready_for_commit = (
        len(results['missing']) == 0 and
        len(results['russian_ok']) == len(modified_files)
    )
    
    if ready_for_commit:
        print("? ALL CHECKS PASSED - READY FOR GIT COMMIT!")
        print()
        print("Next steps:")
        print("  1. Run tests: python run_ui_tests.py")
        print("  2. Git commit: git add . && git commit -m '...'")
        print("  3. Git push: git push origin master")
        return 0
    else:
        print("? VALIDATION FAILED - FIX ISSUES BEFORE COMMIT")
        print()
        if results['missing']:
            print("Missing files:")
            for f in results['missing']:
                print(f"  - {f}")
        if results['russian_missing']:
            print("Files without Russian text:")
            for f in results['russian_missing']:
                print(f"  - {f}")
        return 1

def show_git_status():
    """Show current Git status"""
    import subprocess
    
    print()
    print("=" * 80)
    print("?? GIT STATUS")
    print("=" * 80)
    
    try:
        result = subprocess.run(
            ['git', 'status', '--short'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("?? Git not available or not a repository")
    
    except Exception as e:
        print(f"?? Could not get Git status: {e}")

def count_lines_changed():
    """Count total lines changed"""
    import subprocess
    
    print()
    print("=" * 80)
    print("?? CODE METRICS")
    print("=" * 80)
    
    files_to_check = [
        "src/ui/main_window.py",
        "src/ui/panels/panel_geometry.py",
        "src/ui/panels/panel_pneumo.py"
    ]
    
    total_lines = 0
    for filepath in files_to_check:
        path = Path(filepath)
        if path.exists():
            content = path.read_text(encoding='utf-8')
            lines = len(content.splitlines())
            total_lines += lines
            print(f"  {filepath}: {lines} lines")
    
    print()
    print(f"Total lines in modified files: {total_lines}")
    
    # Count test lines
    test_lines = 0
    test_files = [
        "tests/ui/test_ui_layout.py",
        "tests/ui/test_panel_functionality.py"
    ]
    
    for filepath in test_files:
        path = Path(filepath)
        if path.exists():
            content = path.read_text(encoding='utf-8')
            lines = len(content.splitlines())
            test_lines += lines
    
    print(f"Total lines in test files: {test_lines}")
    print(f"Total code written: {total_lines + test_lines} lines")

if __name__ == "__main__":
    print()
    print("?? PROMPT #1 - FINAL VALIDATION SCRIPT")
    print()
    
    # Run validation
    exit_code = validate_prompt1_changes()
    
    # Show Git status
    show_git_status()
    
    # Show metrics
    count_lines_changed()
    
    print()
    print("=" * 80)
    
    if exit_code == 0:
        print("?? VALIDATION SUCCESSFUL - PROMPT #1 READY FOR COMMIT")
    else:
        print("?? VALIDATION ISSUES FOUND - PLEASE FIX")
    
    print("=" * 80)
    print()
    
    sys.exit(exit_code)
