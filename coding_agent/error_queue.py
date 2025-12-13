"""Error queue management utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_error_queue(queue_path: str | Path) -> list[dict[str, Any]]:
    """Read all errors from error queue file.
    
    Args:
        queue_path: Path to error queue JSONL file
        
    Returns:
        List of error dictionaries
    """
    queue_file = Path(queue_path)
    
    if not queue_file.exists():
        return []
    
    errors: list[dict[str, Any]] = []
    with open(queue_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    errors.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip invalid JSON lines
                    continue
    
    return errors


def get_error_count(queue_path: str | Path) -> int:
    """Get count of errors in queue file.
    
    Args:
        queue_path: Path to error queue JSONL file
        
    Returns:
        Number of errors in queue
    """
    return len(read_error_queue(queue_path))


def remove_processed_cluster_errors(
    queue_path: str | Path,
    processed_cluster_indices: list[int],
) -> None:
    """Remove all errors from successfully processed clusters.
    
    Args:
        queue_path: Path to error queue JSONL file
        processed_cluster_indices: List of error indices to remove (0-based)
    """
    queue_file = Path(queue_path)
    
    if not queue_file.exists():
        return
    
    # Read all errors
    all_errors = read_error_queue(queue_path)
    
    # Filter out processed cluster errors by index
    remaining_errors = [
        error for idx, error in enumerate(all_errors)
        if idx not in processed_cluster_indices
    ]
    
    # Rewrite file
    with open(queue_file, "w", encoding="utf-8") as f:
        for error in remaining_errors:
            f.write(json.dumps(error) + "\n")


def append_error_to_queue(
    queue_path: str | Path,
    error: dict[str, Any],
) -> None:
    """Append a single error to the queue file.
    
    Args:
        queue_path: Path to error queue JSONL file
        error: Error dictionary to append
    """
    queue_file = Path(queue_path)
    
    with open(queue_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(error) + "\n")

