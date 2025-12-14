"""Utilities for cleaning up stale test files and parser modules."""

from pathlib import Path


def cleanup_stale_tests(
    parsers_dir: str | Path,
    tests_dir: str | Path,
    notebooks_tests_dir: str | Path | None = None,
) -> None:
    """Remove test files that don't have corresponding parser modules.
    
    Args:
        parsers_dir: Directory containing parser modules
        tests_dir: Directory containing test files
        notebooks_tests_dir: Optional directory in notebooks/ (for cleanup)
    """
    parsers_path = Path(parsers_dir)
    tests_path = Path(tests_dir)
    
    # Also check notebooks directory if it exists
    notebooks_tests_path = Path(notebooks_tests_dir) if notebooks_tests_dir else None
    
    # Get list of existing parser modules (without .py extension)
    existing_modules = {
        f.stem for f in parsers_path.glob("*.py")
        if f.name != "__init__.py"
    }
    
    print(f"Found {len(existing_modules)} parser modules:")
    for module in sorted(existing_modules):
        print(f"  - {module}")
    
    # Get all test files
    test_files = list(tests_path.glob("test_*.py"))
    if notebooks_tests_path and notebooks_tests_path.exists():
        test_files.extend(notebooks_tests_path.glob("test_*.py"))
    
    print(f"\nFound {len(test_files)} test files")
    
    # Find test files that don't have corresponding modules
    stale_tests = []
    valid_tests = []
    
    for test_file in test_files:
        # Extract module name from test file (test_<module_name>.py)
        module_name = test_file.stem[5:]  # Remove "test_" prefix
        
        if module_name not in existing_modules:
            stale_tests.append(test_file)
        else:
            valid_tests.append(test_file)
    
    print(f"\nValid test files ({len(valid_tests)}):")
    for test_file in sorted(valid_tests):
        print(f"  ✓ {test_file.name}")
    
    if stale_tests:
        print(f"\nStale test files ({len(stale_tests)}):")
        for test_file in sorted(stale_tests):
            print(f"  ✗ {test_file.name} (module '{test_file.stem[5:]}' not found)")
        
        # Ask for confirmation (or auto-delete if running from script)
        print(f"\nRemoving {len(stale_tests)} stale test files...")
        for test_file in stale_tests:
            test_file.unlink()
            print(f"  ✓ Removed {test_file.name}")
        
        print(f"\n✓ Cleanup complete! Removed {len(stale_tests)} stale test files.")
    else:
        print("\n✓ No stale test files found. All tests match existing modules.")
