"""LLM output parsing utilities for extracting structured data from JSON responses."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_reason_node_output(
    parsed_response: list[dict[str, Any]] | None
) -> dict[str, Any]:
    """Extract structured data from REASON node JSON response.
    
    Args:
        parsed_response: List of dicts from parse_llm_json_extraction_response(), or None
        
    Returns:
        Dict with keys: clusters, selected_clusters, total_errors_analyzed,
        total_clusters_identified, clusters_selected_count
        
    Raises:
        ValueError: If parsed_response is None/empty or missing required keys
    """
    if parsed_response is None or len(parsed_response) == 0:
        raise ValueError("REASON node response is None or empty")
    
    first_dict = parsed_response[0]
    
    if "clusters" not in first_dict:
        raise ValueError("REASON node response missing 'clusters' key")
    
    if "selected_clusters" not in first_dict:
        raise ValueError("REASON node response missing 'selected_clusters' key")
    
    # Extract required fields
    clusters = first_dict["clusters"]
    selected_clusters = first_dict["selected_clusters"]
    
    # Extract optional fields with defaults
    total_errors_analyzed = first_dict.get("total_errors_analyzed", 0)
    if not isinstance(total_errors_analyzed, int):
        logger.warning("total_errors_analyzed is not an int, using default 0")
        total_errors_analyzed = 0
    
    total_clusters_identified = first_dict.get("total_clusters_identified", 0)
    if not isinstance(total_clusters_identified, int):
        logger.warning("total_clusters_identified is not an int, using default 0")
        total_clusters_identified = 0
    
    clusters_selected_count = first_dict.get("clusters_selected_count", len(selected_clusters))
    if not isinstance(clusters_selected_count, int):
        logger.warning("clusters_selected_count is not an int, using default len(selected_clusters)")
        clusters_selected_count = len(selected_clusters)
    
    return {
        "clusters": clusters,
        "selected_clusters": selected_clusters,
        "total_errors_analyzed": total_errors_analyzed,
        "total_clusters_identified": total_clusters_identified,
        "clusters_selected_count": clusters_selected_count,
    }


def extract_plan_node_output(
    parsed_response: list[dict[str, Any]] | None
) -> dict[str, Any]:
    """Extract structured data from PLAN node JSON response.
    
    Args:
        parsed_response: List of dicts from parse_llm_json_extraction_response(), or None
        
    Returns:
        Dict with key: cluster_plans
        
    Raises:
        ValueError: If parsed_response is None/empty or missing required keys
    """
    if parsed_response is None or len(parsed_response) == 0:
        raise ValueError("PLAN node response is None or empty")
    
    first_dict = parsed_response[0]
    
    if "cluster_plans" not in first_dict:
        raise ValueError("PLAN node response missing 'cluster_plans' key")
    
    return {
        "cluster_plans": first_dict["cluster_plans"],
    }


def extract_act_node_output(
    parsed_response: list[dict[str, Any]] | None
) -> dict[str, Any]:
    """Extract structured data from ACT node JSON response.
    
    Args:
        parsed_response: List of dicts from parse_llm_json_extraction_response(), or None
        
    Returns:
        Dict with keys: cluster_modules, test_files
        
    Raises:
        ValueError: If parsed_response is None/empty or missing required keys
    """
    if parsed_response is None or len(parsed_response) == 0:
        raise ValueError("ACT node response is None or empty")
    
    first_dict = parsed_response[0]
    
    if "cluster_modules" not in first_dict:
        raise ValueError("ACT node response missing 'cluster_modules' key")
    
    if "test_files" not in first_dict:
        raise ValueError("ACT node response missing 'test_files' key")
    
    return {
        "cluster_modules": first_dict["cluster_modules"],
        "test_files": first_dict["test_files"],
    }

