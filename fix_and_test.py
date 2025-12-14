#!/usr/bin/env python3
"""Fix test failures by writing modules to disk and cleaning up stale tests."""

from pathlib import Path
from recover_and_test import write_generated_code_to_disk, run_tests_and_reload
from cleanup_stale_tests import cleanup_stale_tests


def fix_and_test(result: dict, parsers_dir: str | Path = "notebooks/time_parser/parsers", 
                 tests_dir: str | Path = "notebooks/time_parser/tests") -> dict:
    """Fix test failures by writing modules and cleaning up.
    
    Args:
        result: Workflow result dictionary
        parsers_dir: Directory for parser modules
        tests_dir: Directory for test files
        
    Returns:
        Test results dictionary
    """
    print("=" * 70)
    print("FIXING TEST FAILURES")
    print("=" * 70)
    
    # Step 1: Write generated modules to disk
    cluster_modules = result.get("generated_cluster_modules", {})
    test_files = result.get("generated_test_files", {})
    
    if not cluster_modules:
        print("\n❌ No generated modules found in result!")
        print("   Cannot fix - need to rerun workflow")
        return {"all_passed": False, "test_output": "", "test_errors": "No generated modules", "returncode": 1}
    
    print(f"\n1. Writing {len(cluster_modules)} parser modules to disk...")
    write_generated_code_to_disk(cluster_modules, test_files, parsers_dir, tests_dir)
    
    # Step 2: Clean up stale test files
    print(f"\n2. Cleaning up stale test files...")
    cleanup_stale_tests(parsers_dir, tests_dir, notebooks_tests_dir="notebooks/time_parser/tests")
    
    # Step 3: Run tests
    print(f"\n3. Running tests...")
    test_results = run_tests_and_reload(tests_dir, parsers_dir)
    
    return test_results


if __name__ == "__main__":
    print("Usage: Call fix_and_test(result) with your workflow result")
    print("Example:")
    print("  from fix_and_test import fix_and_test")
    print("  result = workflow.run(initial_state=initial_state)")
    print("  test_results = fix_and_test(result)")
