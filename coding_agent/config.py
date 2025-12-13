"""Configuration constants for the coding agent."""

# Error Threshold
ERROR_THRESHOLD: int = 5  # Minimum errors before agent activates

# Batch Processing Configuration
CLUSTER_BATCH_SIZE: int = 3  # Number of error clusters to process per batch

# Retry Configuration
MAX_RETRY_ATTEMPTS: int = 3  # Maximum retry attempts per error batch

