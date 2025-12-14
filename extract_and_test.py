#!/usr/bin/env python3
"""Extract generated code from workflow result and run tests."""

from pathlib import Path
from coding_agent.test_runner import run_pytest
from coding_agent.reloader import reload_parser


def extract_and_write_code(result: dict, parsers_dir: str | Path = "time_parser/parsers", tests_dir: str | Path = "time_parser/tests") -> None:
    """Extract generated code from workflow result and write to disk.
    
    Args:
        result: Workflow result dictionary with generated_cluster_modules and generated_test_files
        parsers_dir: Directory for parser modules
        tests_dir: Directory for test files
    """
    cluster_modules = result.get("generated_cluster_modules", {})
    test_files = result.get("generated_test_files", {})
    
    if not cluster_modules:
        raise ValueError("No generated_cluster_modules in result")
    if not test_files:
        raise ValueError("No generated_test_files in result")
    
    parsers_path = Path(parsers_dir)
    tests_path = Path(tests_dir)
    
    parsers_path.mkdir(parents=True, exist_ok=True)
    tests_path.mkdir(parents=True, exist_ok=True)
    
    # Write parser modules
    print(f"\n📝 Writing {len(cluster_modules)} parser modules to {parsers_path}...")
    for cluster_id, code in cluster_modules.items():
        module_path = parsers_path / f"{cluster_id}.py"
        module_path.write_text(code, encoding="utf-8")
        print(f"  ✓ Wrote {module_path}")
    
    # Write test files
    print(f"\n📝 Writing {len(test_files)} test files to {tests_path}...")
    for cluster_id, test_code in test_files.items():
        test_path = tests_path / f"test_{cluster_id}.py"
        test_path.write_text(test_code, encoding="utf-8")
        print(f"  ✓ Wrote {test_path}")


def run_tests(tests_dir: str | Path = "time_parser/tests") -> dict:
    """Run tests and return results.
    
    Args:
        tests_dir: Directory containing test files
        
    Returns:
        Test results dictionary
    """
    print(f"\n🧪 Running tests in {tests_dir}...")
    test_results = run_pytest(tests_dir, verbose=True)
    
    print(f"\n{'='*60}")
    print(f"Test Results:")
    print(f"  All passed: {test_results['all_passed']}")
    print(f"  Return code: {test_results['returncode']}")
    
    if test_results['test_output']:
        print(f"\nTest Output:")
        print(test_results['test_output'])
    
    if test_results['test_errors']:
        print(f"\nTest Errors:")
        print(test_results['test_errors'])
    
    return test_results


if __name__ == "__main__":
    print("This script should be imported and used in a notebook.")
    print("Example:")
    print("  from extract_and_test import extract_and_write_code, run_tests")
    print("  extract_and_write_code(result)")
    print("  test_results = run_tests()")
