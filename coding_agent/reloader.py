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
    
    # Reload existing modules
    for module_file in parsers_path.glob("*.py"):
        if module_file.name == "__init__.py":
            continue
        
        module_name = module_file.stem
        full_module_path = f"time_parser.parsers.{module_name}"
        
        if full_module_path in sys.modules:
            importlib.reload(sys.modules[full_module_path])
        else:
            importlib.import_module(full_module_path)
    
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
    
    from time_parser.parser import TimeParser
    
    parser = TimeParser()
    parser.reload_cluster_modules()  # Refresh cluster module registry
    return parser

