"""Module reloading utilities for dynamic parser updates."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from time_parser.parser import TimeParser


def reload_cluster_modules(parsers_dir: str | Path) -> None:
    """Reload all cluster parser modules after agent updates.
    
    Args:
        parsers_dir: Path to directory containing cluster parser modules
    """
    parsers_path = Path(parsers_dir)
    
    if not parsers_path.exists():
        return
    
    # First, clean up any stale module references for files that no longer exist
    # Get set of actual module files
    actual_module_files = {
        f.stem for f in parsers_path.glob("*.py") 
        if f.name != "__init__.py"
    }
    
    # Remove stale entries from sys.modules
    stale_modules = []
    for module_key in list(sys.modules.keys()):
        if module_key.startswith("time_parser.parsers."):
            module_name = module_key.split(".")[-1]
            if module_name not in actual_module_files:
                stale_modules.append(module_key)
    
    for stale_key in stale_modules:
        del sys.modules[stale_key]
        print(f"Warning: Cleaned up stale module reference: {stale_key}")
    
    # Reload existing modules - only process files that actually exist
    for module_file in parsers_path.glob("*.py"):
        if module_file.name == "__init__.py":
            continue
        
        # Verify file exists (should always be true from glob, but be defensive)
        if not module_file.exists():
            continue
        
        module_name = module_file.stem
        full_module_path = f"time_parser.parsers.{module_name}"
        
        try:
            if full_module_path in sys.modules:
                # Reload existing module
                try:
                    importlib.reload(sys.modules[full_module_path])
                except (ModuleNotFoundError, ImportError) as e:
                    # Module was in sys.modules but can't be reloaded (file deleted?)
                    print(f"Warning: Cannot reload module {module_name} (file may have been deleted): {e}")
                    # Clean up stale reference
                    del sys.modules[full_module_path]
                    continue
            else:
                # Import new module - only if file exists
                try:
                    importlib.import_module(full_module_path)
                except (ModuleNotFoundError, ImportError) as e:
                    # Module doesn't exist or can't be imported - skip it
                    # This can happen if there's a stale reference or import error
                    print(f"Warning: Skipping module {module_name} (not found or import failed): {e}")
                    # Clean up stale reference if it exists
                    if full_module_path in sys.modules:
                        del sys.modules[full_module_path]
                    continue
        except Exception as e:
            # Other errors during reload - log but continue
            print(f"Warning: Failed to reload module {module_name}: {e}")
            # Clean up stale reference if it exists
            if full_module_path in sys.modules:
                try:
                    del sys.modules[full_module_path]
                except Exception:
                    pass
            continue
    
    # Reload main parser to refresh cluster module registry
    if "time_parser.parser" in sys.modules:
        importlib.reload(sys.modules["time_parser.parser"])


def reload_parser(parsers_dir: str | Path) -> "TimeParser":
    """Reload parser and return new instance.
    
    Args:
        parsers_dir: Path to directory containing cluster parser modules
        
    Returns:
        New TimeParser instance with reloaded modules
    """
    reload_cluster_modules(parsers_dir)
    
    # Import TimeParser after cleaning up modules
    # This ensures we start with a clean state
    if "time_parser.parser" in sys.modules:
        importlib.reload(sys.modules["time_parser.parser"])
    
    from time_parser.parser import TimeParser
    
    # Create parser instance - it will load modules from files that exist
    # The _load_cluster_modules() method only processes existing files, so it should be safe
    try:
        parser = TimeParser()
        parser.reload_cluster_modules()  # Refresh cluster module registry
        return parser
    except Exception as e:
        # If initialization fails, try to clean up and retry once
        print(f"Warning: Parser initialization failed: {e}")
        # Clean up any problematic module references
        parsers_path = Path(parsers_dir)
        if parsers_path.exists():
            actual_module_files = {
                f.stem for f in parsers_path.glob("*.py") 
                if f.name != "__init__.py"
            }
            for module_key in list(sys.modules.keys()):
                if module_key.startswith("time_parser.parsers."):
                    module_name = module_key.split(".")[-1]
                    if module_name not in actual_module_files:
                        try:
                            del sys.modules[module_key]
                        except Exception:
                            pass
        # Retry once
        parser = TimeParser()
        parser.reload_cluster_modules()
        return parser

