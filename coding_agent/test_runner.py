"""Test runner utilities for pytest integration."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def run_pytest(tests_dir: str | Path, verbose: bool = True) -> dict[str, Any]:
    """Run pytest on test directory and return results.
    
    Args:
        tests_dir: Path to directory containing test files
        verbose: Whether to run pytest in verbose mode
        
    Returns:
        Dictionary with test results:
        - all_passed: bool - True if all tests passed
        - test_output: str - stdout from pytest
        - test_errors: str - stderr from pytest
        - returncode: int - pytest exit code
    """
    tests_path = Path(tests_dir)
    
    if not tests_path.exists():
        return {
            "all_passed": False,
            "test_output": "",
            "test_errors": f"Test directory does not exist: {tests_dir}",
            "returncode": 1,
        }
    
    # Build pytest command
    cmd = ["pytest", str(tests_path)]
    if verbose:
        cmd.append("-v")
    
    # Run pytest
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    
    return {
        "all_passed": result.returncode == 0,
        "test_output": result.stdout,
        "test_errors": result.stderr,
        "returncode": result.returncode,
    }

