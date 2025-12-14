"""Main TimeParser class that orchestrates cluster-specific parsers."""
import importlib
import sys
from pathlib import Path
from typing import Callable
from datetime import datetime, timezone


class TimeParser:
    """Main parser that orchestrates cluster-specific parsers."""
    
    def __init__(self):
        """Initialize parser and load all cluster modules."""
        self._cluster_parsers: dict[str, Callable[[str], datetime | None]] = {}
        self._load_cluster_modules()
    
    def _load_cluster_modules(self) -> None:
        """Dynamically discover and load all cluster parser modules."""
        parsers_dir = Path(__file__).parent / "parsers"
        
        # Discover all Python modules in parsers/ directory
        for module_file in parsers_dir.glob("*.py"):
            if module_file.name == "__init__.py":
                continue
            
            module_name = module_file.stem
            full_module_path = f"time_parser.parsers.{module_name}"
            
            try:
                # Import the module
                module = importlib.import_module(full_module_path)
                
                # Each cluster module should export a parse function
                if hasattr(module, "parse"):
                    parse_func = getattr(module, "parse")
                    self._cluster_parsers[module_name] = parse_func
            except Exception as e:
                # Log error but continue loading other modules
                print(f"Warning: Failed to load parser module {module_name}: {e}")
    
    def reload_cluster_modules(self) -> None:
        """Reload all cluster modules (called after agent updates modules)."""
        parsers_dir = Path(__file__).parent / "parsers"
        
        # Reload existing modules
        for module_name in list(self._cluster_parsers.keys()):
            full_module_path = f"time_parser.parsers.{module_name}"
            if full_module_path in sys.modules:
                try:
                    importlib.reload(sys.modules[full_module_path])
                except Exception as e:
                    print(f"Warning: Failed to reload module {module_name}: {e}")
        
        # Reload all modules (discovers new modules too)
        self._load_cluster_modules()
    
    def parse(self, text: str) -> datetime:
        """Parse time expression by trying all cluster parsers.
        
        Args:
            text: Time expression string to parse
            
        Returns:
            datetime object with UTC timezone
            
        Raises:
            ValueError: If no cluster parser can parse the input
        """
        # Try each cluster parser in order
        for cluster_name, parse_func in self._cluster_parsers.items():
            try:
                result = parse_func(text)
                if result is not None:
                    return result
            except Exception:
                # Continue to next parser if this one fails
                continue
        
        # Basic fallback cases for initial testing (before agent generates modules)
        text_lower = text.lower().strip()
        if text_lower == "asap":
            return datetime.now(timezone.utc)
        elif text_lower == "now":
            return datetime.now(timezone.utc)
        
        # If no parser succeeded, raise exception
        raise ValueError(f"Could not parse time expression: {text}")

