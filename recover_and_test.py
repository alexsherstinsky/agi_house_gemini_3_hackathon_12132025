#!/usr/bin/env python3
"""Recover generated code from workflow state and run tests.

This script can:
1. Extract generated code from a workflow state
2. Write it to disk
3. Run the tests
"""

import json
from pathlib import Path
from coding_agent.test_runner import run_pytest
from coding_agent.reloader import reload_parser


def write_generated_code_to_disk(
    cluster_modules: dict[str, str],
    test_files: dict[str, str],
    parsers_dir: str | Path = "time_parser/parsers",
    tests_dir: str | Path = "time_parser/tests",
) -> None:
    """Write generated code from workflow state to disk.
    
    Args:
        cluster_modules: Dict mapping cluster_id to module code
        test_files: Dict mapping cluster_id to test file code
        parsers_dir: Directory for parser modules
        tests_dir: Directory for test files
    """
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


def recover_from_state_file(state_file: str | Path) -> None:
    """Recover generated code from a saved state file and write to disk.
    
    Args:
        state_file: Path to JSON file containing workflow state
    """
    state_path = Path(state_file)
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_file}")
    
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    
    node_output = state.get("node_output", {})
    cluster_modules = node_output.get("generated_cluster_modules", {})
    test_files = node_output.get("generated_test_files", {})
    
    if not cluster_modules:
        raise ValueError("No generated_cluster_modules found in state")
    if not test_files:
        raise ValueError("No generated_test_files found in state")
    
    print(f"Found {len(cluster_modules)} cluster modules and {len(test_files)} test files in state")
    write_generated_code_to_disk(cluster_modules, test_files)


def recover_from_workflow(workflow) -> None:
    """Recover generated code from a workflow instance and write to disk.
    
    Args:
        workflow: CodingAgentWorkflow instance
    """
    state = workflow.get_state()
    node_output = state.values.get("node_output", {})
    
    cluster_modules = node_output.get("generated_cluster_modules", {})
    test_files = node_output.get("generated_test_files", {})
    
    if not cluster_modules:
        raise ValueError("No generated_cluster_modules found in workflow state")
    if not test_files:
        raise ValueError("No generated_test_files found in workflow state")
    
    print(f"Found {len(cluster_modules)} cluster modules and {len(test_files)} test files in workflow state")
    write_generated_code_to_disk(cluster_modules, test_files)


def run_tests_and_reload(tests_dir: str | Path = "time_parser/tests", parsers_dir: str | Path = "time_parser/parsers") -> dict:
    """Run tests and reload parser if tests pass.
    
    Args:
        tests_dir: Directory containing test files
        parsers_dir: Directory containing parser modules
        
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
    
    if test_results['all_passed']:
        print(f"\n✓ All tests passed! Reloading parser...")
        parser = reload_parser(parsers_dir)
        print(f"✓ Parser reloaded with {len(parser._cluster_parsers)} cluster modules")
    else:
        print(f"\n✗ Some tests failed. Parser not reloaded.")
    
    return test_results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Recover from state file
        state_file = sys.argv[1]
        print(f"Recovering from state file: {state_file}")
        recover_from_state_file(state_file)
    else:
        print("Usage:")
        print("  python recover_and_test.py <state_file.json>  # Recover from saved state")
        print("  Or use recover_from_workflow(workflow) in a notebook")
        sys.exit(1)
    
    # Run tests
    run_tests_and_reload()
