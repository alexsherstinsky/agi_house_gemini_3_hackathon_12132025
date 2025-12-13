"""Error queue management utilities."""

from __future__ import annotations

import fcntl
import json
import os
import time
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
        
    Raises:
        IOError: If file operations fail after retries
    """
    queue_file = Path(queue_path)
    
    if not queue_file.exists():
        return
    
    # Read all errors with shared lock
    all_errors = []
    for attempt in range(3):
        try:
            with open(queue_file, "r", encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            all_errors.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock
            break
        except (IOError, OSError) as e:
            if attempt < 2:
                time.sleep(0.1)
                continue
            raise IOError(f"Failed to read queue file after 3 attempts: {e}") from e
    
    # Filter out processed cluster errors by index
    remaining_errors = [
        error for idx, error in enumerate(all_errors)
        if idx not in processed_cluster_indices
    ]
    
    # Write remaining errors with exclusive lock
    for attempt in range(3):
        try:
            with open(queue_file, "w", encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock for writing
                for error in remaining_errors:
                    f.write(json.dumps(error) + "\n")
                f.flush()
                os.fsync(f.fileno())
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock
            break
        except (IOError, OSError) as e:
            if attempt < 2:
                time.sleep(0.1)
                continue
            raise IOError(f"Failed to write queue file after 3 attempts: {e}") from e


def append_error_to_queue(
    queue_path: str | Path,
    error: dict[str, Any],
) -> None:
    """Append a single error to the queue file.
    
    Args:
        queue_path: Path to error queue JSONL file
        error: Error dictionary to append
        
    Raises:
        IOError: If file operations fail after retries
    """
    queue_file = Path(queue_path)
    
    for attempt in range(3):
        try:
            with open(queue_file, "a", encoding="utf-8") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
                f.write(json.dumps(error) + "\n")
                f.flush()
                os.fsync(f.fileno())
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock
            break
        except (IOError, OSError) as e:
            if attempt < 2:
                time.sleep(0.1)
                continue
            raise IOError(f"Failed to append to queue file after 3 attempts: {e}") from e

