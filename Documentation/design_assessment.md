# Self-Healing Time Parser: Design Assessment & Architecture

**Date:** December 13, 2025  
**Project:** AGI House Gemini 3 Hackathon  
**Status:** Design Phase - Awaiting Review

---

## Executive Summary

This document outlines the design and architecture for a self-healing time parser system that uses an LLM-based coding agent to automatically update parsing logic when encountering new time expression patterns. The system learns from failures and improves itself without manual intervention.

---

## 1. Feasibility Assessment

### ✅ Is this idea sound? Can this be done?

**Yes, this is absolutely feasible and well-suited for a hackathon project.** The approach aligns with modern self-healing/adaptive systems patterns and can be implemented effectively using existing codebase utilities.

### Key Enablers:
- Dynamic module loading utilities in `utils/dynamic_loading.py`
- Proven LLM integration patterns via `call_llm_with_prompt()` in `utils/llm_helpers.py`
- Well-structured workflow patterns in `coding_agent/base.py`
- Python's built-in `importlib.reload()` for dynamic code updates

---

## 2. Code Modules Available in Project

### ✅ Successfully Copied and Available:

1. **LLM Integration:**
   - `utils/llm_helpers.py`
     - Contains `call_llm_with_prompt()` function (uses LangChain API)
     - **Status:** LangChain API is stable and should work properly
     - **Usage:** Import via `from utils.llm_helpers import call_llm_with_prompt`
   - `coding_agent/base.py`
     - Contains `_call_llm_with_prompt()` wrapper method
     - Contains `WorkflowBase` class (no conversation dependency)
     - Contains `AnnotationState` class for workflow state management
     - Contains `RateLimitingConfig` class for rate limiting configuration
     - **Usage:** Import via `from coding_agent.base import WorkflowBase, AnnotationState, RateLimitingConfig`

2. **Interface Patterns:**
   - `coding_agent/llms.py`
     - `NodeLLMs` Pydantic model for LLM configuration
     - **Usage:** Import via `from coding_agent.llms import NodeLLMs`
   - `coding_agent/prompts.py`
     - `NodePrompts` and `SystemAndUserPromptPair` models
     - **Usage:** Import via `from coding_agent.prompts import NodePrompts, SystemAndUserPromptPair`

3. **Dynamic Loading Utilities:**
   - `utils/dynamic_loading.py`
     - `verify_dynamic_loading_support()` - Validates module can be loaded
     - `import_library_module()` - Imports module by name
     - `load_class()` - Loads class from module
     - **Usage:** Import via `from utils.dynamic_loading import verify_dynamic_loading_support, import_library_module, load_class`

### ⚠️ Note on Module Reloading:
- Python's standard `importlib.reload()` will be used (standard library, no dependencies needed)

---

## 3. Architecture & Design

### 3.1 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Time Parser Module                        │
│  (Dynamic - gets reloaded when updated by Coding Agent)     │
│                                                               │
│  class TimeParser:                                           │
│      def parse(self, text: str) -> datetime:                │
│          # Regex-based parsing logic                         │
│          # Updated by Coding Agent                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ parse_time_expression()
                       │
                       ▼
            ┌──────────────────────┐
            │  Exception Handler   │
            │  (Tee/Wrapper)       │
            │  - Captures errors   │
            │  - Logs to queue     │
            │  - Doesn't block     │
            └──────────┬───────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
┌───────────────┐          ┌──────────────────────┐
│ Original Code │          │  Error Queue File     │
│  Continues    │          │  (error_queue.jsonl)  │
│  (Returns     │          │  - JSONL format       │
│   None/raises)│          │  - One error per line │
└───────────────┘          └──────────┬───────────┘
                                      │
                                      │ (threshold check: >= 5)
                                      ▼
                            ┌──────────────────────┐
                            │  Coding Agent        │
                            │  (LangGraph Workflow)│
                            └──────────┬───────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
        ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
        │  REASON Node     │  │  PLAN Node    │  │  ACT Node        │
        │  - Analyze errors│  │  - Design fix│  │  - Generate code │
        │  - Find patterns │  │  - Plan tests│  │  - Write files   │
        └──────────────────┘  └──────────────┘  └──────────────────┘
                                        │
                                        ▼
                            ┌──────────────────────┐
                            │  VALIDATE Node       │
                            │  - Run pytest        │
                            │  - Check all pass    │
                            └──────────┬───────────┘
                                        │
                        ┌───────────────┴───────────────┐
                        │                                 │
                        ▼                                 ▼
            ┌──────────────────────┐        ┌──────────────────────┐
            │  All Tests Pass?     │        │  Some Tests Fail?    │
            │  YES                 │        │  NO                  │
            │  - Remove processed  │        │  - Retry/Refine      │
            │    errors from queue │        │  - Loop back to PLAN │
            │  - Reload module     │        │    or REASON         │
            └──────────────────────┘        └──────────────────────┘
```

### 3.2 Component Breakdown

#### 3.2.1 Time Parser Module (`time_parser/parser.py`)
- **Purpose:** Main orchestrator that discovers and loads cluster-specific parser modules
- **Initial State:** Basic implementation that loads cluster modules from `parsers/` subdirectory
- **Update Mechanism:** Agent generates new cluster module files; main parser discovers and loads them dynamically
- **Interface:**
  ```python
  class TimeParser:
      def __init__(self):
          """Initialize parser and load all cluster modules."""
          self._cluster_parsers: dict[str, Callable] = {}
          self._load_cluster_modules()
      
      def _load_cluster_modules(self) -> None:
          """Dynamically discover and load all cluster parser modules."""
          # Discovers all .py files in parsers/ directory
          # Imports each module and registers its parse() function
      
      def reload_cluster_modules(self) -> None:
          """Reload all cluster modules (called after agent updates)."""
          # Reloads modules using importlib.reload()
      
      def parse(self, text: str) -> datetime.datetime:
          """Parse time expression by trying all cluster parsers."""
          # Tries each cluster parser in order
          # Returns first successful result or raises exception
  ```

#### 3.2.1a Cluster Parser Modules (`time_parser/parsers/`)
- **Purpose:** Individual parser modules, one per error cluster
- **Structure:** Each module exports a `parse(text: str) -> datetime | None` function
- **Update Mechanism:** Agent generates new module files (e.g., `relative_dates.py`, `specific_dates.py`)
- **Naming:** Module filename matches cluster_id from REASON node
- **Example:**
  ```python
  # time_parser/parsers/relative_dates.py
  def parse(text: str) -> datetime | None:
      """Parse relative date expressions."""
      # Cluster-specific parsing logic
      # Returns datetime if successful, None otherwise
  ```

#### 3.2.2 Exception Interceptor (`time_parser/wrapper.py`)
- **Purpose:** Capture parsing failures without blocking execution
- **Pattern:** Decorator or context manager that wraps parser calls
- **Behavior:**
  - Catches exceptions from `TimeParser.parse()`
  - Logs error to queue file (JSONL format)
  - Re-raises exception or returns None (configurable)
  - Does NOT block original code execution

**Usage Example in Application Code:**
```python
# application_code.py
from time_parser.wrapper import intercept_parser_errors
from time_parser.parser import TimeParser

parser = TimeParser()

# Option 1: Decorator pattern
@intercept_parser_errors(parser)
def parse_deadline(text: str) -> datetime.datetime | None:
    return parser.parse(text)

# Option 2: Direct wrapper
def process_follow_up_task(timing_description: str):
    try:
        deadline = intercept_parser_errors(parser)(parser.parse)(timing_description)
        if deadline:
            print(f"✓ Parsed: {timing_description} -> {deadline}")
        else:
            print(f"✗ Failed to parse: {timing_description}")
    except Exception as e:
        # Error already logged by interceptor
        print(f"✗ Error: {e}")
        # Continue with business logic (e.g., use fallback deadline)
```

**Race Condition Prevention:**
- **File Locking:** Use file locks when agent updates parser module
- **Atomic Updates:** Write updated parser to temporary file, then atomically replace
- **Version Check:** Application code checks parser module version/timestamp before use
- **Graceful Degradation:** If parser is being updated, application can:
  - Use cached parser instance
  - Retry after brief delay
  - Fall back to default behavior

#### 3.2.3 Error Queue (`error_queue.jsonl`)
- **Format:** JSONL (one JSON object per line)
- **Structure:** (Finalized based on real error examples from `follow_up_tasks_202512121435.jsonl`)
  ```json
  {
    "customer_id": 3,
    "deadline_at": null,
    "timing_description": "After the initial service appointment is completed.",
    "auxiliary_pretty": "{\n    \"parsing_error\": {\n        \"error_type\": \"parsing_failed\",\n        \"error_message\": \"Could not parse timing description: After the initial service appointment is completed.\",\n        \"original_timing\": \"After the initial service appointment is completed.\"\n    },\n    \"deadline_parsing\": {\n        \"timezone_used\": \"UTC\",\n        \"parsing_method\": \"fallback\",\n        \"original_timing\": \"After the initial service appointment is completed.\",\n        \"parsed_timestamp\": null\n    }\n}"
  }
  ```
- **Key Fields:**
  - `timing_description`: The input text that failed to parse (primary field for agent)
  - `auxiliary_pretty`: JSON string containing error details (can be parsed for additional context)
  - `deadline_at`: null for parsing failures, timestamp for successful parses
- **Error Clustering & Processing:**
  - Agent scans error queue file and uses LLM to cluster similar errors
  - Agent processes up to N error clusters per batch (default: 5 clusters, configurable via constant)
  - All error rows within successfully processed clusters are removed from queue
  - Processed errors become test cases for the parser module

#### 3.2.4 Coding Agent (`coding_agent/agent.py`)
- **Architecture:** LangGraph workflow with reasoning/planning/act pattern
- **Nodes:**
  1. **REASON Node:** Analyze error patterns, identify commonalities
  2. **PLAN Node:** Design code changes and test strategy
  3. **ACT Node:** Generate updated parser code and tests
  4. **VALIDATE Node:** Run pytest, verify all tests pass
- **Loop Logic:** If validation fails, loop back to PLAN or REASON
- **Success Criteria:** All tests pass (verifiable reward signal)

#### 3.2.5 Module Reloader (`coding_agent/reloader.py`)
- **Purpose:** Reload updated cluster parser modules
- **Implementation:** 
  - Uses `importlib.reload()` for existing modules
  - Uses `importlib.import_module()` for newly created modules
  - Calls `TimeParser.reload_cluster_modules()` to refresh main parser
- **Safety:** Only reloads after successful test validation
- **Scope:** Reloads all cluster modules in `parsers/` directory

#### 3.2.6 Test Runner (`coding_agent/test_runner.py`)
- **Framework:** pytest
- **Behavior:**
  - Runs all tests in `time_parser/tests/` directory (pytest auto-discovery)
  - Agent generates new test files for each cluster (e.g., `test_relative_dates.py`)
  - Agent keeps running tests until all pass
  - Only proceeds to module reload when all tests pass
  - Each test file corresponds to a parser module (modular structure)

---

## 4. Coding Agent Design: Reasoning/Planning/Act Pattern

### 4.1 Should We Use LangGraph with Reasoning/Planning/Act?

**Recommendation: YES, use LangGraph with R/P/A pattern**

#### Why LangGraph is Beneficial:

1. **Natural Workflow Structure:**
   - REASON → PLAN → ACT → VALIDATE is a clear, sequential workflow
   - LangGraph excels at managing stateful, multi-step processes
   - Built-in error handling and retry logic

2. **State Management:**
   - Agent needs to maintain state across steps:
     - Error batch being processed
     - Current parser code
     - Generated code updates
     - Test results
   - LangGraph's state management handles this elegantly

3. **Conditional Logic:**
   - If VALIDATE fails → loop back to PLAN or REASON
   - LangGraph's conditional edges make this straightforward
   - Can implement retry limits and fallback strategies

4. **Extensibility:**
   - Easy to add nodes (e.g., REFLECT, REVIEW)
   - Can add parallel processing for multiple error patterns
   - Aligns with existing codebase patterns

5. **Best Practices Alignment:**
   - Matches modern agent architecture patterns (ReAct, Plan-and-Solve)
   - Demonstrates sophisticated but appropriate tool usage
   - Makes the hackathon project stand out

#### Implementation Pattern:

**Base Class Selection:**
- **Use `WorkflowBase` from `coding_agent/base.py`** (already copied into project)
- This is an **independent, self-contained hackathon project**
- All necessary code is available in the project:
  - `WorkflowBase` class and `AnnotationState` class in `coding_agent/base.py`
  - `call_llm_with_prompt()` function in `utils/llm_helpers.py`
  - `RateLimitingConfig` class in `coding_agent/base.py`
  - Dynamic loading utilities in `utils/dynamic_loading.py`
- Project structure is standalone for hackathon demonstration

**LangGraph Interface Reuse:**
- **YES, we can use LangGraph patterns** from `coding_agent/base.py`
- The node structure (REASON, PLAN, ACT, VALIDATE) is similar to existing workflows
- Main differences:
  - Our nodes operate on error clusters and code generation (not conversation data)
  - State contains error clusters, parser code, test results (not conversation state)
  - Output is updated parser module (not conversation annotations)
- **Recommendation:** Use `WorkflowBase` from `coding_agent/base.py` and adapt node implementations for our use case

```python
# coding_agent/agent.py
# Uses WorkflowBase from coding_agent/base.py
# Adapted for hackathon project

class CodingAgentWorkflow(WorkflowBase):  # Base class from coding_agent/base.py
    """Self-healing coding agent using R/P/A pattern."""
    
    def _add_workflow_nodes_and_edges(self, workflow: StateGraph) -> None:
        # Add nodes
        workflow.add_node("reason", self._reason_node)      # Cluster errors
        workflow.add_node("plan", self._plan_node)           # Design fixes
        workflow.add_node("act", self._act_node)             # Generate code
        workflow.add_node("validate", self._validate_node)   # Run tests
        
        # Add edges (sequential for now)
        workflow.set_entry_point("reason")
        workflow.add_edge("reason", "plan")
        workflow.add_edge("plan", "act")
        workflow.add_edge("act", "validate")
        
        # TODO: <Alex>ALEX</Alex> - Parallel processing opportunity:
        # Multiple clusters could be processed in parallel after REASON node
        # Could split into parallel PLAN/ACT/VALIDATE chains for each cluster
        # Then merge results before final queue cleanup
        
        # Conditional edge: if tests pass, end; else retry
        workflow.add_conditional_edges(
            "validate",
            self._should_retry,
            {
                "retry": "plan",  # Loop back to plan (refine approach)
                "success": END,   # All tests pass
                "failure": END,   # Max retries reached (safety valve)
            }
        )
        
        # TODO: <Alex>ALEX</Alex> - Parallel processing opportunity:
        # REASON node could process multiple error queue files in parallel
        # ACT node could generate parser code and tests in parallel
        # VALIDATE node could run tests for different clusters in parallel
```


### 4.2 Workflow State & Data Flow

**Initial State (Input to First Node - REASON):**
```python
{
    "messages": [],  # LangGraph messages (empty initially)
    "node_output": None,
    "final_output": None,
    # Custom fields for coding agent:
    "error_queue_path": "error_queue.jsonl",
    "parsers_dir": "time_parser/parsers/",  # Directory for cluster modules
    "tests_dir": "time_parser/tests/",      # Directory for test files
    "error_clusters": None,  # Will be populated by REASON node
    "selected_clusters": None,  # Up to 5 clusters selected for processing
    "existing_cluster_modules": None,  # List of existing cluster modules (read by PLAN node)
    "generated_cluster_modules": None,  # New cluster module files from ACT node (dict: cluster_id -> code)
    "generated_test_files": None,  # New test files from ACT node (dict: cluster_id -> test_code)
    "test_results": None,  # Results from VALIDATE node
    "retry_count": 0
}
```

**Final Output (Retrieved from Workflow):**
```python
{
    "success": True,
    "processed_clusters": ["relative_dates", "specific_times", "time_ranges"],  # List of cluster IDs processed
    "errors_removed_count": 15,  # Total number of errors removed from queue (across all clusters)
    "parser_updated": True,
    "tests_passed": True,
    "retry_count": 1,
    "generated_cluster_modules": {  # Dictionary mapping cluster_id to module code
        "relative_dates": "# time_parser/parsers/relative_dates.py\n...",  # Complete module code
        "specific_times": "# time_parser/parsers/specific_times.py\n...",  # Complete module code
        "time_ranges": "# time_parser/parsers/time_ranges.py\n...",  # Complete module code
    },
    "generated_test_files": {  # Dictionary mapping cluster_id to test code
        "relative_dates": "# time_parser/tests/test_relative_dates.py\n...",  # Complete test file code
        "specific_times": "# time_parser/tests/test_specific_times.py\n...",  # Complete test file code
        "time_ranges": "# time_parser/tests/test_time_ranges.py\n...",  # Complete test file code
    },
    "cluster_error_indices": {  # Dictionary mapping cluster_id to list of error indices (for queue cleanup)
        "relative_dates": [0, 1, 5, 12],  # Error indices from original queue file
        "specific_times": [2, 8, 15],
        "time_ranges": [3, 7, 11, 14],
    }
}
```

**Note on Multiple Clusters:**
- When multiple error clusters are identified in a single pass (e.g., 5 clusters as per `CLUSTER_BATCH_SIZE`), the final output contains:
  - **Multiple entries** in `generated_cluster_modules` (one per cluster)
  - **Multiple entries** in `generated_test_files` (one per cluster)
  - **Multiple entries** in `cluster_error_indices` (one per cluster)
- Each cluster gets its own module file (`parsers/<cluster_id>.py`) and test file (`tests/test_<cluster_id>.py`)
- The `errors_removed_count` is the sum of all errors across all processed clusters
- All cluster modules are generated in a single ACT node execution, then all are written to disk, then all tests are run together

**LLM Output Format Recommendation: MODULAR ARCHITECTURE**

**Key Architectural Decision:** Use modular architecture with one module per error cluster.

- **ACT Node generates NEW cluster module files** (one per cluster)
  - **Rationale:**
    - Simpler for hackathon (no complex code insertion logic)
    - Each cluster is isolated in its own module file
    - LLM generates complete, self-contained module files
    - Easier to validate (each module file is syntactically correct)
    - No overwriting of existing modules (only creates new ones)
    - Scales naturally - no limit on number of clusters
    - Better organization and maintainability
  - **Module Structure:** Each module exports a `parse(text: str) -> datetime | None` function
  - **File Naming:** Use cluster_id from REASON node (e.g., `relative_dates.py`, `specific_dates.py`)
  - **Location:** Modules go in `time_parser/parsers/` subdirectory
  - **Main Parser:** Orchestrates by discovering and loading all cluster modules dynamically

- **Test Files:** Generate new test files (one per cluster)
  - **File Naming:** `test_<cluster_id>.py` matches `parsers/<cluster_id>.py`
  - **Structure:** Parameterized tests for all error cases in that cluster
  - **Location:** Test files go in `time_parser/tests/` directory
  - **Updating:** If test file exists, add new cases to existing parameterized test lists
  - **Discovery:** pytest automatically discovers all `test_*.py` files

**Benefits of Modular Architecture:**
- ✅ **Unlimited Scalability:** No limit on number of error clusters
- ✅ **Clear Organization:** Each cluster is isolated in its own module and test file
- ✅ **Easy Maintenance:** Changes to one cluster don't affect others
- ✅ **Natural Growth:** New clusters simply add new module files
- ✅ **Agent-Friendly:** Agent generates new files instead of modifying large files
- ✅ **Better Testability:** Tests are organized by cluster, matching parser structure

**Scalability: Modular Architecture for Parser Modules**

**Problem:** As more error clusters are processed, a single `parser.py` file would become very long (hundreds/thousands of lines), making it difficult to maintain and update.

**Solution: Modular Architecture with Cluster-Specific Modules (RECOMMENDED)**

**Architecture:**
- **Main Parser (`parser.py`):** Orchestrates parsing by discovering and loading cluster-specific modules
- **Cluster Modules (`parsers/` subdirectory):** One Python module per error cluster/class
  - Each module contains parsing logic for a specific error cluster
  - Modules are dynamically discovered and loaded by the main parser
  - No limit on number of clusters - each gets its own module file
- **Test Modules (`tests/` subdirectory):** One test file per cluster module
  - Matches the modular structure of parser modules
  - pytest automatically discovers all test files

**Benefits:**
- ✅ **Unlimited Scalability:** No limit on number of error clusters
- ✅ **Clear Organization:** Each cluster is isolated in its own module
- ✅ **Easy Maintenance:** Changes to one cluster don't affect others
- ✅ **Natural Growth:** New clusters simply add new module files
- ✅ **Better Testability:** Tests are organized by cluster, matching parser structure
- ✅ **Agent-Friendly:** Agent generates new module files instead of modifying large files

**Directory Structure:**
```
time_parser/
├── __init__.py
├── parser.py              # Main TimeParser class (orchestrator)
└── parsers/               # Cluster-specific parser modules
    ├── __init__.py
    ├── relative_dates.py      # Module for relative date cluster
    ├── specific_dates.py      # Module for specific date cluster
    ├── time_ranges.py         # Module for time range cluster
    └── ...                    # More modules as clusters are processed
```

**Main Parser Implementation:**
```python
# time_parser/parser.py
import importlib
import os
from pathlib import Path
from typing import Callable
from datetime import datetime

class TimeParser:
    """Main parser that orchestrates cluster-specific parsers."""
    
    def __init__(self):
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
        
        for module_name in list(self._cluster_parsers.keys()):
            full_module_path = f"time_parser.parsers.{module_name}"
            if full_module_path in sys.modules:
                importlib.reload(sys.modules[full_module_path])
        
        # Reload all modules
        self._load_cluster_modules()
    
    def parse(self, text: str) -> datetime:
        """Parse time expression by trying all cluster parsers."""
        # Try each cluster parser in order
        for cluster_name, parse_func in self._cluster_parsers.items():
            try:
                result = parse_func(text)
                if result is not None:
                    return result
            except Exception:
                # Continue to next parser if this one fails
                continue
        
        # If no parser succeeded, raise exception
        raise ValueError(f"Could not parse time expression: {text}")
```

**Cluster Module Example:**
```python
# time_parser/parsers/relative_dates.py
"""Parser module for relative date expressions cluster."""
from datetime import datetime, timedelta, UTC
import re

def parse(text: str) -> datetime | None:
    """Parse relative date expressions like 'tomorrow', 'next week', etc."""
    text_lower = text.lower().strip()
    
    # Pattern matching for relative dates
    if text_lower == "tomorrow":
        return datetime.now(UTC) + timedelta(days=1)
    elif text_lower == "next week":
        return datetime.now(UTC) + timedelta(weeks=1)
    elif match := re.match(r"in (\d+) days?", text_lower):
        days = int(match.group(1))
        return datetime.now(UTC) + timedelta(days=days)
    # ... more patterns
    
    return None  # Not a relative date expression
```

**Agent ACT Node Changes:**
- **Instead of:** Generating complete `parser.py` file
- **Now:** Generate new cluster module files in `parsers/` subdirectory
- **File naming:** Use cluster_id from REASON node (e.g., `relative_dates.py`, `specific_dates.py`)
- **Module structure:** Each module exports a `parse(text: str) -> datetime | None` function
- **Main parser:** Only needs to be updated if orchestration logic changes (rare)

**Test Structure (Matching Modular Architecture):**
```
time_parser/tests/
├── __init__.py
├── test_relative_dates.py      # Tests for parsers/relative_dates.py
├── test_specific_dates.py      # Tests for parsers/specific_dates.py
├── test_time_ranges.py         # Tests for parsers/time_ranges.py
└── ...                         # More test files as clusters are processed
```

**Test File Example:**
```python
# time_parser/tests/test_relative_dates.py
"""Tests for relative_dates parser module."""
import pytest
from datetime import datetime
from time_parser.parsers.relative_dates import parse

@pytest.mark.parametrize("input_text,expected_day_offset", [
    ("tomorrow", 1),
    ("next week", 7),
    ("in 2 days", 2),
    ("in 5 days", 5),
])
def test_relative_dates(input_text: str, expected_day_offset: int):
    """Test parsing of relative date expressions."""
    result = parse(input_text)
    assert result is not None
    assert isinstance(result, datetime)
    # Additional assertions as needed
```

**Implementation Notes:**
1. **Module Discovery:** Main parser uses `Path.glob()` to discover all `.py` files in `parsers/` directory
2. **Dynamic Loading:** Uses `importlib.import_module()` to load cluster modules
3. **Reloading:** After agent updates, call `reload_cluster_modules()` to refresh
4. **Error Handling:** If a cluster module fails to load, main parser continues with other modules
5. **Module Interface:** Each cluster module must export a `parse(text: str) -> datetime | None` function

**Feasibility Assessment:**
- ✅ **Highly Feasible:** Python's dynamic module loading makes this straightforward
- ✅ **Standard Pattern:** Common Python pattern for plugin-based architectures
- ✅ **Agent-Friendly:** Agent generates new files instead of modifying existing large files
- ✅ **Test-Friendly:** pytest automatically discovers test files in `tests/` directory
- ✅ **Scalable:** No practical limit on number of cluster modules

**Hackathon Recommendation:**
- **Use modular architecture from the start** - it's cleaner and more scalable
- **Simpler than single-file approach** - agent generates new files, not complex code insertion
- **Better demonstrates self-healing** - new capabilities appear as new modules
- **Easier to debug** - each cluster is isolated

### 4.3 Node Responsibilities

#### REASON Node (Error Clustering & Analysis):
- **Input:** All errors from queue file (or subset if file is very large)
- **Task:** 
  1. **Cluster errors** into similar groups using LLM-based classification
  2. **Select up to N clusters** (default: 5) for processing in this batch
  3. **Analyze patterns** within each cluster to identify commonalities
- **Output:** Structured analysis with error clusters and their characteristics
- **LLM Schema:** `ErrorClusterAnalysis` Pydantic model
- **Example Output:**
  ```python
  {
      "clusters": [
          {
              "cluster_id": "relative_dates",
              "error_indices": [0, 1, 5, 12],
              "commonality": "relative date expressions",
              "examples": ["tomorrow", "next week", "in 2 days", "Monday morning"],
              "suggested_approach": "Add dateutil.relativedelta support"
          },
          {
              "cluster_id": "context_dependent",
              "error_indices": [2, 8, 15],
              "commonality": "requires external context",
              "examples": ["After service completion", "When customer is ready"],
              "suggested_approach": "May be unparseable - attempt with defaults"
          }
      ],
      "selected_clusters": ["relative_dates", "context_dependent", ...]  # Up to 5
  }
  ```
- **Note:** LLM-based clustering is feasible for hackathon - LLM can identify semantic similarities in error patterns

#### PLAN Node:
- **Input:** Error cluster analysis + current parser code (read from file)
- **Task:** Design code changes and test strategy for selected clusters
- **Output:** Plan for code updates and test cases
- **LLM Schema:** `CodePlan` Pydantic model
- **Example Output:**
  ```python
  {
      "code_changes": "Add parse_relative_date() method...",
      "test_cases": [
          {"input": "tomorrow", "expected": "2025-12-14T00:00:00Z"},
          ...
      ],
      "dependencies": ["dateutil"]
  }
  ```
- **TODO: <Alex>ALEX</Alex> - Parallel processing opportunity:**
  - Could plan fixes for multiple clusters in parallel
  - Each cluster could have its own planning thread/node

#### ACT Node:
- **Input:** Plan + selected error clusters + existing cluster modules (if any)
- **Task:** Generate new cluster parser modules and corresponding test files
- **Output:** New module files in `parsers/` and test files in `tests/` directories
- **LLM Schema:** `CodeUpdate` Pydantic model (contains module code and test code)
- **Action:** 
  - Write new cluster module files to `parsers/<cluster_id>.py`
  - Write new test files to `tests/test_<cluster_id>.py`
  - Use file locking to prevent race conditions
  - Each cluster gets its own module and test file
- **Module Structure:** Each cluster module exports a `parse(text: str) -> datetime | None` function
- **Test Structure:** Each test file uses parameterized tests for that cluster's error cases
- **TODO: <Alex>ALEX</Alex> - Parallel processing opportunity:**
  - Could generate parser modules and test files in parallel
  - Could generate code for multiple clusters in parallel (each cluster is independent)

#### VALIDATE Node:
- **Input:** Updated code files (parser.py and tests/test_parser.py)
- **Task:** Run pytest, collect results
- **Output:** Test results (pass/fail)
- **Implementation:** Subprocess call to pytest
- **Decision:** All pass → success, any fail → retry
- **TODO: <Alex>ALEX</Alex> - Parallel processing opportunity:**
  - Could run tests for different clusters in parallel (if tests are organized by cluster)
  - Could run parser validation and test validation in parallel

### 4.4 Retry Logic & Safety Valve

**Retry Configuration:**
- Maximum retry attempts is configurable via constant (default: 3)
- Constant defined in `coding_agent/config.py`
- Example: `MAX_RETRY_ATTEMPTS = 3`

**Safety Valve Feature:**
When the Coding Agent is unable to make all tests pass after the maximum number of retry attempts:
1. Agent gives up on the current error batch
2. Agent logs the failed batch to a separate file (`failed_batches.jsonl`)
3. Agent continues with the next batch (does not block processing)
4. Failed batches can be reviewed manually later

**Implementation:**
```python
# coding_agent/config.py
MAX_RETRY_ATTEMPTS: int = 3  # Configurable max retries per batch

def _should_retry(self, state: AnnotationState) -> str:
    """Determine if agent should retry or succeed."""
    test_results = state["node_output"]["test_results"]
    
    if test_results["all_passed"]:
        return "success"
    elif test_results["retry_count"] < MAX_RETRY_ATTEMPTS:
        return "retry"
    else:
        # Safety valve: log failed batch and give up
        self._log_failed_batch(state["error_batch"], test_results)
        return "failure"  # Give up after max retries

def _log_failed_batch(self, error_batch: list[dict], test_results: dict) -> None:
    """Log failed batch to separate file for human review."""
    failed_batch_entry = {
        "error_batch": error_batch,
        "test_results": test_results,
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "retry_count": test_results["retry_count"]
    }
    with open("failed_batches.jsonl", "a") as f:
        f.write(json.dumps(failed_batch_entry) + "\n")
```

---

## 5. Error Queue Management

### 5.1 Format: JSONL

**Rationale:**
- Easy to append (one line per error)
- Easy to read batch (read N lines)
- Easy to remove processed items (rewrite file without processed lines)
- Human-readable for debugging

### 5.2 Error Clustering & Batch Processing

**Approach:** Cluster similar errors, then process clusters in batches

**Configuration:**
- Number of clusters to process per batch is configurable via constant (default: 5)
- Constant defined in `coding_agent/config.py`
- Example: `CLUSTER_BATCH_SIZE = 5`

**Process:**
1. **Read all errors** from queue file (or sample if file is very large)
2. **LLM-based clustering:** REASON node uses LLM to cluster errors by semantic similarity
3. **Select clusters:** Choose up to N clusters (default: 5) for processing
4. **Process clusters:** Generate code fixes for all errors in selected clusters
5. **Remove processed errors:** After successful validation, remove ALL errors from successfully processed clusters

**Benefits:**
- More efficient: one code fix handles multiple similar errors
- Better pattern recognition: LLM identifies semantic similarities
- Comprehensive coverage: all errors in a cluster are addressed together
- Reduces redundant code generation

**LLM Clustering Feasibility:**
- **YES, feasible for hackathon:** LLM can analyze error patterns and group them semantically
- LLM receives error queue file and identifies clusters based on:
  - Similar timing expressions (e.g., "relative dates", "specific dates with times")
  - Similar error characteristics (e.g., "context-dependent", "ambiguous")
- Clustering prompt template provided to LLM with examples

**Implementation:**
```python
# coding_agent/config.py
CLUSTER_BATCH_SIZE: int = 5  # Number of error clusters to process per batch

def get_error_clusters(queue_path: str) -> list[dict]:
    """Read all errors from queue and return for clustering."""
    with open(queue_path, 'r') as f:
        errors = [json.loads(line) for line in f]
    return errors

# Clustering happens in REASON node via LLM
# Returns: list of clusters, each containing error indices and characteristics
```

### 5.3 Queue Management

**Process:**
1. Agent reads all errors from queue file
2. REASON node clusters errors using LLM
3. Agent selects up to N clusters (default: 5) for processing
4. Agent processes selected clusters and generates fixes
5. Agent runs tests until all pass (or max retries reached)
6. **Upon success:** Remove ALL errors from successfully processed clusters
7. **Upon success:** Add processed errors as test cases to test file
8. **Upon failure (max retries):** Log failed clusters to separate file for human review

**Implementation:**
```python
def remove_processed_cluster_errors(
    queue_path: str, 
    processed_cluster_indices: list[int]  # Error indices from successfully processed clusters
) -> None:
    """Remove all errors from successfully processed clusters."""
    # Read all errors
    with open(queue_path, 'r') as f:
        all_errors = [json.loads(line) for line in f]
    
    # Filter out processed cluster errors by index
    remaining_errors = [
        error for idx, error in enumerate(all_errors)
        if idx not in processed_cluster_indices
    ]
    
    # Rewrite file
    with open(queue_path, 'w') as f:
        for error in remaining_errors:
            f.write(json.dumps(error) + '\n')
```

**Note:** LLM-based clustering in REASON node is a good approach - LLM can identify semantic patterns in error messages and timing descriptions, grouping similar errors effectively.

---

## 6. Test Generation & Validation

### 6.1 Test Framework: pytest

**Rationale:**
- Standard Python testing framework
- Easy to run programmatically
- Good error reporting
- Supports parameterized tests

### 6.2 Test Generation Strategy

**Directory Structure:**
- **Implementation:** `time_parser/parser.py` (updated by agent)
- **Tests:** `time_parser/tests/test_parser.py` (separate directory, updated by agent)
- This follows pytest conventions where tests are in a separate `tests/` subdirectory

**Process:**
1. Agent generates test cases for each error cluster processed
2. Agent adds test cases to `time_parser/tests/test_parser.py`
3. Agent runs `pytest time_parser/tests/` (runs all tests in tests directory)
4. If any test fails, agent refines code and retries
5. **Success Criteria:** All tests pass (verifiable reward)

**Test Structure Recommendation (Based on Error Analysis):**

After analyzing `follow_up_tasks_202512121435.jsonl`, errors fall into distinct clusters:
- **Relative dates:** "tomorrow", "next week", "in 2 days", "Monday morning"
- **Specific dates with times:** "On December 18th, prior to 4-5 PM", "By 9 AM on Monday"
- **Time ranges:** "Within 1-2 business days", "In 3-5 business days"
- **Context-dependent:** "After service completion", "When customer is ready"
- **Ambiguous:** "At customer's earliest convenience"

**Recommended Structure: Parameterized Tests per Cluster**

```python
# time_parser/tests/test_parser.py (generated/updated by agent)

import pytest
from datetime import datetime
from time_parser.parser import TimeParser

class TestRelativeDates:
    """Tests for relative date expressions cluster."""
    
    @pytest.mark.parametrize("input_text", [
        "tomorrow",
        "Tomorrow morning",
        "next week",
        "Monday or Tuesday next week",
        "in 2 days",
        "within 1-2 days",
    ])
    def test_relative_dates(self, input_text):
        """Test parsing of relative date expressions."""
        parser = TimeParser()
        result = parser.parse(input_text)
        assert result is not None
        assert isinstance(result, datetime)
        # Additional assertions as needed

class TestSpecificDatesWithTimes:
    """Tests for specific dates with time expressions cluster."""
    
    @pytest.mark.parametrize("input_text", [
        "By 9 AM on Monday",
        "On December 18th, prior to the 4-5 PM appointment window",
        "Monday morning by 9 AM",
        "Before Wednesday, December 17th",
    ])
    def test_specific_dates_times(self, input_text):
        """Test parsing of specific dates with times."""
        parser = TimeParser()
        result = parser.parse(input_text)
        assert result is not None
        assert isinstance(result, datetime)

class TestTimeRanges:
    """Tests for time range expressions cluster."""
    
    @pytest.mark.parametrize("input_text", [
        "Within 1-2 business days",
        "In 3-5 business days",
        "Within 5-10 minutes",
        "within 15-20 minutes of original call end",
    ])
    def test_time_ranges(self, input_text):
        """Test parsing of time range expressions."""
        parser = TimeParser()
        result = parser.parse(input_text)
        assert result is not None
        assert isinstance(result, datetime)

# Note: Context-dependent and ambiguous errors may not have tests
# if they are determined to be unparseable
```

**Rationale:**
- **Parameterized tests per cluster:** Each error cluster gets its own test class
- **One test method per cluster:** Uses `@pytest.mark.parametrize` to test all errors in cluster
- **Clear organization:** Test classes match error clusters identified by REASON node
- **Easy to maintain:** Agent can add new test cases to existing parameterized tests
- **Efficient:** pytest runs all parameterized cases, showing which specific inputs fail

**Scalability: Modular Test Architecture**

**Problem:** As more error clusters are processed, a single `test_parser.py` file would become very long (hundreds/thousands of lines with many test cases).

**Solution: Modular Test Structure Matching Parser Modules (RECOMMENDED)**

**Architecture:**
- **One test file per cluster module:** Matches the modular structure of parser modules
- **Test file naming:** `test_<cluster_id>.py` corresponds to `parsers/<cluster_id>.py`
- **pytest auto-discovery:** pytest automatically discovers all `test_*.py` files in `tests/` directory
- **Shared utilities:** Common test helpers in `conftest.py` or `test_utils.py`

**Benefits:**
- ✅ **Perfect Alignment:** Test structure matches parser structure
- ✅ **Unlimited Scalability:** No limit on number of test files
- ✅ **Clear Organization:** Each cluster's tests are isolated
- ✅ **Easy Maintenance:** Changes to one cluster's tests don't affect others
- ✅ **Natural Growth:** New clusters simply add new test files
- ✅ **Agent-Friendly:** Agent generates new test files instead of modifying large files

**Directory Structure:**
```
time_parser/tests/
├── __init__.py
├── conftest.py              # Shared pytest fixtures
├── test_utils.py            # Shared test utilities
├── test_relative_dates.py   # Tests for parsers/relative_dates.py
├── test_specific_dates.py   # Tests for parsers/specific_dates.py
├── test_time_ranges.py      # Tests for parsers/time_ranges.py
└── ...                      # More test files as clusters are processed
```

**Test File Structure:**
```python
# time_parser/tests/test_relative_dates.py
"""Tests for relative_dates parser module."""
import pytest
from datetime import datetime
from time_parser.parsers.relative_dates import parse
from time_parser.tests.test_utils import assert_valid_datetime

@pytest.mark.parametrize("input_text,expected_day_offset", [
    ("tomorrow", 1),
    ("next week", 7),
    ("in 2 days", 2),
    ("in 5 days", 5),
    ("Monday morning", None),  # New cases added here
    ("next Tuesday", None),
])
def test_relative_dates(input_text: str, expected_day_offset: int | None):
    """Test parsing of relative date expressions."""
    result = parse(input_text)
    assert_valid_datetime(result, input_text)
    # Additional cluster-specific assertions
```

**Shared Test Utilities:**
```python
# time_parser/tests/test_utils.py
"""Shared test utilities for all test modules."""
from datetime import datetime

def assert_valid_datetime(result: datetime | None, input_text: str) -> None:
    """Shared assertion helper for valid datetime results."""
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime), f"Result not datetime: {input_text}"
    assert result.tzinfo is not None, f"Result not timezone-aware: {input_text}"
```

**Shared Fixtures:**
```python
# time_parser/tests/conftest.py
"""Shared pytest fixtures."""
import pytest
from time_parser.parser import TimeParser

@pytest.fixture
def parser():
    """Fixture providing TimeParser instance."""
    return TimeParser()
```

**Agent ACT Node Changes:**
- **Instead of:** Generating/updating single `test_parser.py` file
- **Now:** Generate new test files in `tests/` subdirectory
- **File naming:** Use cluster_id from REASON node (e.g., `test_relative_dates.py`)
- **Test structure:** Each test file uses parameterized tests for that cluster
- **Updating existing tests:** If test file exists, agent adds new test cases to existing parameterized test lists

**LLM Instructions for Test Generation:**
```python
# ACT Node prompt enhancement for test generation
test_generation_instructions = """
When generating test code:
1. Create one test file per cluster: test_<cluster_id>.py
2. Use @pytest.mark.parametrize for test cases within each cluster
3. If test file already exists, add new cases to existing parameterized test lists
4. Import shared utilities from test_utils.py for common assertions
5. Keep test files focused on one cluster each

Example structure:
- test_relative_dates.py: Tests for relative_dates parser module
- test_specific_dates.py: Tests for specific_dates parser module
- Each file uses parameterized tests for that cluster's error cases
"""
```

**Feasibility Assessment:**
- ✅ **Highly Feasible:** Standard pytest pattern for modular test organization
- ✅ **Natural Fit:** Matches the modular parser architecture perfectly
- ✅ **Agent-Friendly:** Agent generates new test files, not complex file modifications
- ✅ **Scalable:** No practical limit on number of test files
- ✅ **Maintainable:** Each cluster's tests are isolated and easy to understand

**Hackathon Recommendation:**
- **Use modular test structure from the start** - matches parser architecture
- **Simpler than single-file approach** - agent generates new files
- **Better organization** - clear one-to-one mapping between parser modules and test files
- **Easier to debug** - test failures are clearly associated with specific clusters

### 6.3 Validation Loop

```python
def validate_node(self, state: AnnotationState) -> dict:
    """Run tests and validate all pass."""
    # Run pytest on tests directory
    result = subprocess.run(
        ["pytest", "time_parser/tests/", "-v"],
        capture_output=True,
        text=True
    )
    
    # Parse results
    all_passed = result.returncode == 0
    
    return {
        "all_passed": all_passed,
        "test_output": result.stdout,
        "retry_count": state.get("retry_count", 0) + 1
    }
```

---

## 7. File Structure

```
DO_NOT_COMMIT/AGI_HOUSE_GEMINI_3_HACKATHON_12132025/
├── project_description.txt
├── design_assessment.md (this file)
├── time_parser/
│   ├── __init__.py
│   ├── parser.py          # Main TimeParser class (orchestrator, rarely updated)
│   ├── parsers/           # Cluster-specific parser modules (generated by agent)
│   │   ├── __init__.py
│   │   ├── relative_dates.py      # Module for relative date cluster
│   │   ├── specific_dates.py      # Module for specific date cluster
│   │   ├── time_ranges.py          # Module for time range cluster
│   │   └── ...                     # More modules as clusters are processed
│   └── tests/             # Test directory (pytest convention)
│       ├── __init__.py
│       ├── conftest.py            # Shared pytest fixtures
│       ├── test_utils.py          # Shared test utilities
│       ├── test_relative_dates.py  # Tests for parsers/relative_dates.py
│       ├── test_specific_dates.py  # Tests for parsers/specific_dates.py
│       ├── test_time_ranges.py     # Tests for parsers/time_ranges.py
│       └── ...                     # More test files as clusters are processed
├── coding_agent/
│   ├── __init__.py
│   ├── agent.py           # Main CodingAgentWorkflow class
│   ├── config.py          # Configuration constants (batch size, retry limits)
│   ├── llms.py            # NodeLLMs configuration
│   ├── prompts.py         # NodePrompts configuration
│   ├── error_queue.py     # Queue management utilities
│   ├── test_runner.py     # pytest integration
│   └── reloader.py        # Module reloading utilities
├── utils/                  # Utility modules for the project
│   ├── __init__.py
│   ├── dynamic_loading.py # Dynamic module loading utilities
│   └── llm_helpers.py     # LLM helper functions
├── notebooks/              # Jupyter notebooks for demos
│   └── demo.ipynb          # Main demo notebook
├── error_queue.jsonl       # Error queue file
├── failed_batches.jsonl    # Failed batches log (safety valve)
├── follow_up_tasks_202512121435.jsonl  # Real error examples (converted from JSON)
└── pyproject.toml          # Project dependencies (self-contained)
```

**Note on Directory Structure:**
- **Main Parser (`time_parser/parser.py`):** Contains the `TimeParser` class that orchestrates cluster-specific parsers. This file is rarely updated - only if orchestration logic changes.
- **Cluster Modules (`time_parser/parsers/`):** Contains one Python module per error cluster. Each module exports a `parse()` function. Agent generates new module files here.
- **Tests (`time_parser/tests/`):** Contains test files organized by cluster. Each test file corresponds to a parser module. pytest automatically discovers all `test_*.py` files.
- **Modular Architecture:** This structure scales naturally - no limit on number of clusters. Each cluster is isolated in its own module and test file.

---

## 8. Technical Debt & Future Enhancements

### 8.1 Current Limitations

**TODO: Audit Trail for Parser Changes**
- Currently: Parser file is overwritten without backup
- Future: Implement version control/audit trail
  - Keep history of parser versions
  - Enable rollback to previous versions
  - Track which errors triggered which changes
  - Similar to audit trail patterns in `applications/home_services_leader`

**Implementation Note:**
```python
# TODO: <Alex>ALEX -- Implement audit trail for parser changes.</Alex>
# Future enhancement: Keep version history of parser.py
# - Store each version with timestamp and error batch that triggered it
# - Enable rollback functionality
# - Track change impact (which errors were fixed by which version)
```

### 8.2 Other Future Enhancements (Out of Scope for Hackathon)

- Parallel processing of multiple error batches
- Confidence scoring for generated code
- Human-in-the-loop approval for major changes
- Performance monitoring (parsing speed, accuracy)
- Integration with version control (git commits)

---

## 9. Demo Flow (Jupyter Notebook)

**Demo Format:** Jupyter Notebook (`demo.ipynb`)

**Rationale:**
- Better visualization of what's happening at each step
- Can show intermediate states (error queue, generated code, test results)
- Interactive exploration of the self-healing process
- More engaging for hackathon demonstration

### 9.1 Initial State

```python
# Cell 1: Show initial parser implementation
# time_parser/parser.py (initial - orchestrator)
class TimeParser:
    def __init__(self):
        self._cluster_parsers: dict[str, Callable] = {}
        self._load_cluster_modules()
    
    def _load_cluster_modules(self) -> None:
        """Discover and load cluster modules."""
        # Initially empty - agent will generate modules
        pass
    
    def parse(self, text: str) -> datetime.datetime:
        """Try all cluster parsers."""
        # Initially only handles basic cases
        if text.lower() == "asap":
            return datetime.datetime.now(datetime.UTC)
        elif text.lower() == "now":
            return datetime.datetime.now(datetime.UTC)
        else:
            raise ValueError(f"Unknown pattern: {text}")

# Initially, parsers/ directory is empty
# Agent will generate cluster modules like:
# - parsers/relative_dates.py
# - parsers/specific_dates.py
# etc.
```

### 9.2 Error Collection Phase

```python
# Cell 2: Demonstrate error collection with interceptor
from time_parser.wrapper import intercept_parser_errors
from time_parser.parser import TimeParser

parser = TimeParser()

# Wrap parser to automatically log errors
wrapped_parse = intercept_parser_errors(parser)(parser.parse)

# These will fail and be logged to error_queue.jsonl
test_inputs = [
    "call me tomorrow",
    "next week",
    "in 2 days",
    "after the call",
    "ASAP"  # This one succeeds
]

print("Testing parser with various inputs:")
for input_text in test_inputs:
    try:
        result = wrapped_parse(input_text)
        print(f"✓ Parsed: {input_text} -> {result}")
    except Exception as e:
        # Error already logged by interceptor
        print(f"✗ Failed: {input_text} -> {e}")

# Cell 3: Show error queue contents and clustering preview
import json

print("\nError Queue Contents:")
with open("error_queue.jsonl", "r") as f:
    errors = [json.loads(line) for line in f]
    print(f"Total errors: {len(errors)}")
    for i, error in enumerate(errors[:5]):  # Show first 5
        print(f"  {i+1}. {error['timing_description']}")

# Preview: Show how LLM would cluster these
print("\nPreview: Error Clustering (what REASON node will do):")
print("  Cluster 1: Relative dates - ['tomorrow', 'next week', 'in 2 days']")
print("  Cluster 2: Context-dependent - ['after the call']")
```

### 9.3 Agent Activation

**Activation Mechanism:**
- **Manual trigger in demo:** User explicitly calls agent activation function
- **In production:** Could be triggered by:
  - Scheduled job (e.g., every hour)
  - File watcher (monitors error queue file size)
  - API endpoint
  - Background thread checking queue periodically

**Race Condition Handling in Demo:**
- **File locking:** Use `fcntl` (Unix) or `msvcrt` (Windows) to lock parser file during updates
- **Atomic file replacement:** Write to temp file, then rename atomically
- **Version checking:** Application code can check parser module modification time

```python
# Cell 4: Check threshold and activate agent
import fcntl
import os
from coding_agent.agent import CodingAgentWorkflow
from coding_agent.config import CLUSTER_BATCH_SIZE

error_count = get_error_count()
print(f"Errors in queue: {error_count}")

# Check if we have enough errors to form clusters
if error_count >= CLUSTER_BATCH_SIZE:
    print("Activating Coding Agent...")
    
    # Lock parser file to prevent race conditions
    parser_file_path = "time_parser/parser.py"
    with open(parser_file_path, 'r+') as f:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
            
            # Initialize and run agent
            agent = CodingAgentWorkflow(
                error_queue_path="error_queue.jsonl",
                parser_path=parser_file_path,
                # ... other config
            )
            result = agent.run()  # Processes error clusters, updates parser, runs tests
            
            print(f"Agent completed! Processed {result['errors_removed_count']} errors")
            print(f"Clusters processed: {result['processed_clusters']}")
            
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock
else:
    print(f"Waiting for {CLUSTER_BATCH_SIZE} or more errors to form clusters...")
```

**Concurrent Usage Scenario:**
```python
# Cell 5: Demonstrate concurrent usage
# Simulate application code running while agent might be updating parser

import threading
import time

def application_worker():
    """Simulate application code using parser."""
    parser = TimeParser()
    test_inputs = ["tomorrow", "next week", "ASAP"]
    
    for i in range(10):
        for input_text in test_inputs:
            try:
                result = parser.parse(input_text)
                print(f"[Worker] ✓ Parsed: {input_text}")
            except Exception as e:
                print(f"[Worker] ✗ Failed: {input_text} -> {e}")
        time.sleep(1)

# Start application worker in background
worker_thread = threading.Thread(target=application_worker, daemon=True)
worker_thread.start()

# Agent can run in parallel (with file locking)
# Application code will use cached parser instance or wait for lock
```

### 9.4 Success Verification

```python
# Cell 5: Reload and verify
parser = reload_parser()  # Reloads updated module

# Now these should all work
print("Testing updated parser:")
for input_text in test_inputs:
    result = parser.parse(input_text)
    print(f"✓ Parsed: {input_text} -> {result}")

# Cell 6: Show test results
run_tests_and_display()  # Run pytest and show results
```

---

## 10. Open Questions & Decisions Needed

### 10.1 Error Format (Finalized)

**Status:** ✅ Error examples provided and analyzed

**Final Format (matches `follow_up_tasks_202512121435.jsonl`):**
```json
{
    "customer_id": 3,
    "deadline_at": null,
    "timing_description": "After the initial service appointment is completed.",
    "auxiliary_pretty": "{\n    \"parsing_error\": {\n        \"error_type\": \"parsing_failed\",\n        \"error_message\": \"Could not parse timing description: After the initial service appointment is completed.\",\n        \"original_timing\": \"After the initial service appointment is completed.\"\n    },\n    \"deadline_parsing\": {\n        \"timezone_used\": \"UTC\",\n        \"parsing_method\": \"fallback\",\n        \"original_timing\": \"After the initial service appointment is completed.\",\n        \"parsed_timestamp\": null\n    }\n}"
}
```

**Note:** The `timing_description` field contains the input text that failed to parse. The `auxiliary_pretty` field (JSON string) contains detailed error information that can be parsed if needed.

**Key Takeaways from Error Analysis:**

1. **Error Categories:**
   - **Parsable patterns:** "Tomorrow morning", "By 9 AM on Monday", "Within 1-2 business days", "In 3-5 business days"
   - **Context-dependent (unparseable without additional info):** "After the initial service appointment is completed", "As soon as customer obtains pictures", "When customer is ready"
   - **Ambiguous/vague:** "At customer's earliest convenience", "Customer will initiate when ready"

2. **Expected Failure Rate:**
   - Some errors are inherently unparseable (context-dependent situations)
   - This is expected and acceptable in a resilient architecture
   - Agent should handle gracefully: attempt to parse, but accept that some cases cannot be solved
   - Failed batches after max retries will be logged to `failed_batches.jsonl` for manual review

3. **Pattern Complexity:**
   - Many errors contain relative dates ("tomorrow", "Monday", "next week")
   - Some contain time ranges ("3-5 business days", "1-2 days")
   - Some contain specific dates with times ("December 18th, prior to 4-5 PM")
   - Agent should focus on common patterns first (higher success rate)

### 10.2 LLM Model Configuration

**Recommendation:** Google Gemini 3

**Code Usage:**
- **Use `call_llm_with_prompt()` from `utils/llm_helpers.py`** (already available in project)
- The `call_llm_with_prompt()` function uses LangChain's LLM invocation API
- LangChain API is stable and widely used (should work properly)
- Use `WorkflowBase` from `coding_agent/base.py` which provides `_call_llm_with_prompt()` method

**Configuration:**
- **Schema-less output:** Use `schema=None` for `call_llm_with_prompt()`
  - This will work fine - agent will receive raw text responses
  - Agent can parse JSON from text responses if needed
  - More flexible for initial implementation
- Temperature: 0.1-0.3 for code generation
- Chain-of-thought prompting in REASON node
- Few-shot examples in system prompts

**Implementation:**
```python
# Using call_llm_with_prompt from utils/llm_helpers.py with schema=None
from utils.llm_helpers import call_llm_with_prompt

response = call_llm_with_prompt(
    llm=gemini_llm,
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    context_identifier=("Node", "reason"),
    schema=None,  # Schema-less output
    rate_limiting_config=rate_limiting_config,
    debug_logging=debug_logging,
)
# Response will be AIMessage with .content attribute
```

### 10.3 Retry Limits

**Clarification:** This is the same as the safety valve feature mentioned in section 4.3

**Configuration:**
- Maximum retry attempts: 3 (configurable via constant `MAX_RETRY_ATTEMPTS`)
- If validation fails 3 times:
  - Agent gives up on the current batch
  - Logs failed batch to `failed_batches.jsonl` (safety valve)
  - Continues with next batch (does not block processing)
  - Failed batches can be reviewed manually later

---

## 11. Implementation Phases

### Phase 1: Foundation (MVP)
- [ ] Basic TimeParser with 2-3 patterns
- [ ] Exception interceptor/wrapper
- [ ] Error queue (JSONL) with append functionality
- [ ] Simple agent (single LLM call, no LangGraph)

### Phase 2: LangGraph Integration
- [ ] Convert to LangGraph workflow
- [ ] Implement REASON/PLAN/ACT/VALIDATE nodes
- [ ] Add retry logic with conditional edges
- [ ] State management

### Phase 3: Test Integration
- [ ] pytest test runner
- [ ] Test generation by agent
- [ ] Validation loop (run until all pass)
- [ ] Queue cleanup (remove processed errors)

### Phase 4: Polish & Demo
- [ ] Demo Jupyter notebook with clear flow
- [ ] Error examples integration
- [ ] Documentation
- [ ] Technical debt TODOs
- [ ] Safety valve feature (failed batch logging)

---

## 12. Success Criteria

### For Hackathon Demo:

1. ✅ **Self-Healing Demonstrated:**
   - Parser fails on new pattern
   - Error logged to queue
   - Agent activates at threshold
   - Parser updated automatically
   - Next parse succeeds

2. ✅ **Verifiable Reward:**
   - All tests pass after agent update
   - Clear success signal

3. ✅ **Best Practices:**
   - LangGraph R/P/A pattern
   - Structured LLM outputs
   - Proper error handling
   - Clean code structure

---

## 13. Next Steps

1. **Await User Review:** Review this document, provide feedback
2. **Receive Error Examples:** Finalize error format
3. **Refine Design:** Incorporate feedback
4. **Begin Implementation:** Start with Phase 1 (MVP)

---

## Appendix A: Key Code Patterns

### A.1 Dynamic Module Reloading

```python
import importlib
import sys
from pathlib import Path

def reload_parser_modules():
    """Reload all cluster parser modules after agent updates."""
    parsers_dir = Path("time_parser/parsers")
    
    # Reload existing modules
    for module_file in parsers_dir.glob("*.py"):
        if module_file.name == "__init__.py":
            continue
        
        module_name = module_file.stem
        full_module_path = f"time_parser.parsers.{module_name}"
        
        if full_module_path in sys.modules:
            importlib.reload(sys.modules[full_module_path])
        else:
            importlib.import_module(full_module_path)
    
    # Reload main parser to refresh cluster module registry
    if 'time_parser.parser' in sys.modules:
        importlib.reload(sys.modules['time_parser.parser'])
    
    from time_parser.parser import TimeParser
    parser = TimeParser()
    parser.reload_cluster_modules()  # Refresh cluster module registry
    return parser
```

### A.2 Exception Interceptor

```python
from functools import wraps
import json
from datetime import datetime

def intercept_parser_errors(parser_instance):
    """Decorator to intercept and log parser errors to queue file."""
    def decorator(func):
        @wraps(func)
        def wrapper(text: str):
            try:
                return func(text)
            except Exception as e:
                # Log to queue file (JSONL format)
                error_entry = {
                    "customer_id": None,  # Can be provided if available
                    "deadline_at": None,
                    "timing_description": text,
                    "auxiliary_pretty": json.dumps({
                        "parsing_error": {
                            "error_type": "parsing_failed",
                            "error_message": f"Could not parse timing description: {text}",
                            "original_timing": text
                        },
                        "deadline_parsing": {
                            "timezone_used": "UTC",
                            "parsing_method": "fallback",
                            "original_timing": text,
                            "parsed_timestamp": None
                        }
                    })
                }
                
                # Append to error queue file
                with open("error_queue.jsonl", "a") as f:
                    f.write(json.dumps(error_entry) + "\n")
                
                # Re-raise or return None (configurable)
                raise  # or return None
        return wrapper
    return decorator
```

**Usage in Application Code:**
```python
# application_code.py
from time_parser.wrapper import intercept_parser_errors
from time_parser.parser import TimeParser

parser = TimeParser()

# Wrap parser.parse() method
wrapped_parse = intercept_parser_errors(parser)(parser.parse)

# Use in business logic
def process_follow_up_task(timing_description: str):
    try:
        deadline = wrapped_parse(timing_description)
        if deadline:
            print(f"✓ Parsed: {timing_description} -> {deadline}")
            # Continue with business logic using deadline
        else:
            print(f"✗ Failed to parse: {timing_description}")
            # Use fallback logic
    except Exception as e:
        # Error already logged by interceptor
        print(f"✗ Error: {e}")
        # Continue with business logic (graceful degradation)
```

### A.3 LangGraph State Schema

```python
class CodingAgentState(AnnotationState):
    """State for coding agent workflow."""
    error_batch: list[dict] | None = None
    error_analysis: dict[str, Any] | None = None
    code_plan: dict[str, Any] | None = None
    generated_code: str | None = None
    test_results: dict[str, Any] | None = None
    retry_count: int = 0
```

---

---

## 14. Configuration Constants

### 14.1 Batch Processing

```python
# coding_agent/config.py
ERROR_BATCH_SIZE: int = 5  # Number of errors to process per batch
```

### 14.2 Retry Limits

```python
# coding_agent/config.py
MAX_RETRY_ATTEMPTS: int = 3  # Maximum retry attempts per error batch
```

### 14.3 Threshold for Agent Activation

```python
# coding_agent/config.py
ERROR_THRESHOLD: int = ERROR_BATCH_SIZE  # Minimum errors before agent activates
```

---

---

## 15. Error Examples Analysis

### 15.1 Source Data

**File:** `follow_up_tasks_202512121435.jsonl` (converted from JSON)
- **Total Errors:** 71 parsing failures
- **Format:** JSONL (one error per line)
- **Structure:** See Section 10.1 for finalized format

### 15.2 Error Pattern Categories

**Category 1: Parsable Patterns (Agent Can Handle)**
- Relative dates: "tomorrow", "Monday", "next week"
- Time ranges: "Within 1-2 business days", "In 3-5 business days"
- Specific dates with times: "On December 18th, prior to 4-5 PM", "By 9 AM on Monday"
- Time-of-day: "Tomorrow morning", "Monday morning by 9 AM"
- Examples:
  - "Tomorrow morning"
  - "By 9 AM on Monday"
  - "Within 1-2 business days"
  - "In 3-5 business days"
  - "Monday or Tuesday next week"

**Category 2: Context-Dependent (Unparseable Without Additional Info)**
- These require external context (e.g., when did service appointment happen?)
- Agent should attempt to parse but accept failure gracefully
- Examples:
  - "After the initial service appointment is completed"
  - "As soon as customer obtains pictures"
  - "After the estimate has been sent and customer has reviewed it"
  - "When customer is ready"
  - "After today's inspection"

**Category 3: Ambiguous/Vague (Unparseable)**
- No concrete time reference
- Agent should recognize these as unparseable
- Examples:
  - "At customer's earliest convenience"
  - "Customer will initiate when ready"
  - "Customer's discretion"

### 15.3 Expected Behavior

**Success Rate Expectation:**
- Not all errors can be solved (this is expected and acceptable)
- Agent should focus on Category 1 patterns (highest success probability)
- Category 2 and 3 errors will likely fail after max retries
- Failed batches are logged to `failed_batches.jsonl` for manual review
- This is part of resilient architecture - graceful degradation

**Agent Strategy:**
1. Prioritize common patterns (relative dates, time ranges)
2. Attempt to parse context-dependent cases (may succeed with smart defaults)
3. Recognize and skip ambiguous cases (don't waste retries)
4. Log unsolvable cases for human review

---

## 16. Code Independence & Copying Strategy

### 16.1 Self-Contained Project Requirement

**Status:** ✅ **COMPLETED** - All necessary code has been copied into the hackathon project.

**What This Means:**
- **NO imports** from external codebase directories (all code is self-contained in the project)
- **ALL code has been COPIED** into the hackathon project directory
- Project has its own `pyproject.toml` with its own dependencies
- Project can be cloned and run independently
- No dependency on the main ConvoScience codebase structure

**Important Clarification:**
- **Within the hackathon repository:** Normal Python imports are fine - modules can import from each other (e.g., `from utils.llm_helpers import call_llm_with_prompt`)
- **From public packages:** Standard imports from public Python packages are allowed (e.g., `from langchain import ...`, `from pydantic import ...`)
- **Restriction applies only to:** Imports from local existing projects/repositories outside the hackathon directory

### 16.2 Code Available in Project

**✅ All code has been copied and is available:**

- **`utils/llm_helpers.py`:** Contains `call_llm_with_prompt()` function
- **`coding_agent/base.py`:** Contains `WorkflowBase`, `AnnotationState`, and `RateLimitingConfig` classes
- **`coding_agent/llms.py`:** Contains `NodeLLMs` Pydantic model
- **`coding_agent/prompts.py`:** Contains `NodePrompts` and `SystemAndUserPromptPair` models
- **`utils/dynamic_loading.py`:** Contains dynamic loading utilities

**Usage Examples:**
```python
# Import LLM helper
from utils.llm_helpers import call_llm_with_prompt

# Import workflow base classes
from coding_agent.base import WorkflowBase, AnnotationState, RateLimitingConfig

# Import configuration models
from coding_agent.llms import NodeLLMs
from coding_agent.prompts import NodePrompts, SystemAndUserPromptPair

# Import dynamic loading utilities
from utils.dynamic_loading import verify_dynamic_loading_support, import_library_module, load_class
```

**Key Point:** All code is now part of the hackathon project and can use normal Python imports to reference other modules within the hackathon repository.

---

---

## 17. Key Design Questions & Answers

### 17.1 State & Data Flow

**a) What state is being passed to the first node (REASON)?**

See Section 4.2 for detailed state structure. Initial state includes:
- `error_queue_path`: Path to error queue file
- `parser_path`: Path to parser module
- `error_clusters`: None initially, populated by REASON node
- `selected_clusters`: Up to 5 clusters selected for processing
- `retry_count`: 0 initially

**b) What is the output of the final node that we seek to retrieve?**

See Section 4.2 for detailed output structure. Final output includes:
- `success`: Boolean indicating if all tests passed
- `processed_clusters`: List of cluster IDs that were successfully processed
- `errors_removed_count`: Number of errors removed from queue
- `parser_updated`: Boolean indicating if parser was updated
- `tests_passed`: Boolean indicating if all tests passed

**c) Will our LLM calls produce entire parser Python module, or just parts?**

**Recommendation: Generate COMPLETE parser module**

- **Rationale:**
  - Simpler for hackathon (no complex code insertion logic)
  - LLM can see full context and ensure consistency
  - Easier to validate (complete file is syntactically correct)
  - Overwrite strategy is acceptable (as per design decision)
- **Alternative (if needed):** Generate code snippets with insertion points, but this adds complexity
- **Test File:** Generate complete test file with all new test cases for processed clusters

### 17.2 Error Clustering via LLM

**Is LLM-based error clustering a good idea for hackathon?**

**YES, it's a good approach:**

- **Feasible:** LLMs excel at semantic pattern recognition
- **Efficient:** One clustering call can process entire error queue
- **Flexible:** Can identify patterns humans might miss
- **Scalable:** Works with any number of errors

**Implementation:**
- REASON node receives error queue file
- LLM prompt includes clustering template with examples
- LLM returns structured clusters with error indices and characteristics
- Agent selects up to N clusters (default: 5) for processing

### 17.3 Test Structure Recommendation

**Based on analysis of `follow_up_tasks_202512121435.jsonl`:**

**Recommended: Parameterized Tests per Cluster**

- **Structure:** One test class per error cluster
- **Method:** One parameterized test method per cluster using `@pytest.mark.parametrize`
- **Rationale:** See Section 6.2 for detailed test structure

### 17.4 Agent Activation Mechanism

**In Demo (Jupyter Notebook):**
- **Manual trigger:** User explicitly calls agent activation function
- **Threshold check:** Agent checks if enough errors exist to form clusters (default: 5)

**In Production (Future):**
- Scheduled job (e.g., every hour)
- File watcher (monitors error queue file size)
- API endpoint
- Background thread checking queue periodically

### 17.5 Race Condition Prevention

**Problem:** Application code using parser while agent updates it

**Solutions:**
1. **File Locking:** Use `fcntl` (Unix) or `msvcrt` (Windows) to lock parser file during updates
2. **Atomic Updates:** Write to temp file, then rename atomically
3. **Version Checking:** Application code checks parser module modification time
4. **Cached Instances:** Application uses cached parser instance, reloads only when needed

See Section 9.3 for demo implementation example.

### 17.6 LangGraph Interface Reuse

**Can we use LangGraph interfaces from `coding_agent/base.py`?**

**YES, with adaptations:**

- **Use `WorkflowBase`:** Core workflow functionality (state management, LLM calls, graph building) - available in `coding_agent/base.py`
- **Use `AnnotationState`:** Adapt for coding agent state (error clusters, parser code, test results) - available in `coding_agent/base.py`
- **Adapt nodes:** Our nodes operate on error clusters and code generation (not conversation data)
- **Skip `WorkflowRunnerBase`:** Not needed - it's a wrapper for conversation/taxonomy services

See Section 4.1 for detailed discussion.

### 17.7 Parallel Processing Opportunities

**Where parallel processing could be added (with ALEX-style comments):**

See Section 4.3 for detailed parallel processing opportunities marked with `TODO: <Alex>ALEX</Alex>` comments.

---

**Document Status:** Updated with Comprehensive Design Answers  
**Last Updated:** December 13, 2025  
**Next Review:** Ready for implementation planning

---

## 18. Prompt Templates for Coding Agent Nodes

This section contains the draft prompt templates for the REASON, PLAN, and ACT nodes of the Coding Agent workflow. These prompts follow the existing codebase patterns with separate system and user prompts.

### 18.1 REASON Node Prompts (Error Clustering & Analysis)

**Purpose:** Analyze error queue file and cluster similar errors into groups for batch processing.

#### REASON_NODE_SYSTEM_PROMPT_TEMPLATE

```python
REASON_NODE_SYSTEM_PROMPT_TEMPLATE: str = """
You are an expert in natural language time expression parsing and pattern recognition.

Your task is to analyze a collection of parsing errors and cluster them into groups of similar patterns. Each cluster represents a class of time expressions that can be handled by a single parsing module.

## Context

We are building a self-healing time parser system. When the parser encounters time expressions it cannot parse, those errors are logged to a queue file. Your job is to identify common patterns among these errors so that we can generate efficient parsing code that handles multiple similar cases at once.

## Clustering Principles

1. **Semantic Similarity**: Group errors that represent similar time expression patterns, even if the exact wording differs
   - Example: "tomorrow", "next week", "in 2 days" → all relative date expressions
   - Example: "By 9 AM on Monday", "Monday morning by 9 AM" → both specific dates with times

2. **Parsing Approach**: Errors that would be solved by similar parsing logic should be clustered together
   - Example: "Within 1-2 business days", "In 3-5 business days" → both time ranges with business day modifiers

3. **Distinguish Parsable from Unparseable**:
   - **Parsable**: Errors that can be solved with additional parsing logic (e.g., relative dates, specific dates, time ranges)
   - **Context-Dependent**: Errors that require external context (e.g., "After service completion", "When customer is ready") - attempt to cluster these but note they may be challenging
   - **Ambiguous/Vague**: Errors that cannot be parsed without additional information (e.g., "At customer's earliest convenience") - cluster separately and note as potentially unparseable

4. **Cluster Naming**: Use descriptive, lowercase_with_underscores names for cluster IDs (e.g., "relative_dates", "specific_dates_with_times", "time_ranges", "context_dependent")

## Output Requirements

You must output a JSON object with the following structure:

```json
{
    "clusters": [
        {
            "cluster_id": "relative_dates",
            "error_indices": [0, 1, 5, 12],
            "commonality": "relative date expressions without specific times",
            "examples": ["tomorrow", "next week", "in 2 days", "Monday morning"],
            "suggested_approach": "Use dateutil.relativedelta and datetime arithmetic",
            "parsability": "parsable",
            "error_count": 4
        },
        {
            "cluster_id": "context_dependent",
            "error_indices": [2, 8, 15],
            "commonality": "requires external context or event completion",
            "examples": ["After service completion", "When customer is ready", "After taking photographs"],
            "suggested_approach": "May be unparseable - attempt with smart defaults or skip",
            "parsability": "context_dependent",
            "error_count": 3
        }
    ],
    "selected_clusters": ["relative_dates", "specific_dates_with_times", "time_ranges"],
    "total_errors_analyzed": 129,
    "total_clusters_identified": 8,
    "clusters_selected_count": 5
}
```

**Field Descriptions:**
- `clusters`: Array of all identified clusters
  - `cluster_id`: Unique identifier (lowercase_with_underscores, used as module filename)
  - `error_indices`: List of error indices from the input array (0-based)
  - `commonality`: Brief description of what makes these errors similar
  - `examples`: 3-5 example timing_description strings from this cluster
  - `suggested_approach`: High-level approach for parsing this cluster
  - `parsability`: One of "parsable", "context_dependent", or "ambiguous"
  - `error_count`: Number of errors in this cluster
- `selected_clusters`: List of cluster_ids selected for processing (up to 5, prioritize parsable clusters)
- `total_errors_analyzed`: Total number of errors in the input
- `total_clusters_identified`: Total number of clusters found
- `clusters_selected_count`: Number of clusters selected (should match length of selected_clusters)

## Selection Criteria

When selecting clusters for processing (up to 5):
1. **Prioritize parsable clusters** over context-dependent or ambiguous ones
2. **Prioritize larger clusters** (more errors per cluster = better efficiency)
3. **Prioritize common patterns** (relative dates, specific dates, time ranges are common)
4. **Balance diversity** - select clusters that represent different parsing challenges

## Important Notes

- Each error index should appear in exactly one cluster
- Cluster IDs must be valid Python module names (lowercase, underscores, no spaces or special chars)
- Focus on identifying patterns that can be solved with regex, dateutil, or datetime arithmetic
- Some errors may be inherently unparseable - that's acceptable, but cluster them separately
- The goal is to generate efficient code that handles multiple similar cases, not one-off solutions
"""
```

#### REASON_NODE_USER_PROMPT_TEMPLATE

```python
REASON_NODE_USER_PROMPT_TEMPLATE: str = """
Error Queue File Contents:

{error_queue_contents}

The above is a JSONL file where each line is a JSON object representing a parsing error. Each error object has:
- `timing_description`: The text that failed to parse (this is the key field for clustering)
- `auxiliary_pretty`: JSON string containing additional error details (optional, for context)

Your task:
1. Analyze all errors and identify clusters of similar patterns
2. Select up to 5 clusters for processing (prioritize parsable, larger clusters)
3. Return the clustering analysis in the exact JSON format specified in the system prompt

Focus on the `timing_description` field when clustering - this contains the actual time expression that needs to be parsed.

Remember:
- Cluster by semantic similarity and parsing approach, not exact string matching
- Each error should appear in exactly one cluster
- Select clusters that will generate the most useful parsing code
- Use descriptive cluster_ids that will become module filenames (e.g., "relative_dates.py")
"""
```

### 18.2 PLAN Node Prompts (Code Planning)

**Purpose:** Design code changes and test strategy for selected error clusters.

#### PLAN_NODE_SYSTEM_PROMPT_TEMPLATE

```python
PLAN_NODE_SYSTEM_PROMPT_TEMPLATE: str = """
You are an expert Python developer specializing in natural language time parsing and test-driven development.

Your task is to design a plan for implementing parsing modules that will handle specific error clusters identified from parsing failures.

## Context

We are building a modular time parser system where:
- Each error cluster gets its own Python module in `time_parser/parsers/`
- Each module exports a `parse(text: str) -> datetime | None` function
- The main parser orchestrates by trying each cluster module in sequence
- Each cluster module also gets a corresponding test file in `time_parser/tests/`

## Module Structure Requirements

Each cluster module must:
1. **Export a `parse()` function** with signature: `def parse(text: str) -> datetime | None`
2. **Return `datetime` objects** with UTC timezone (use `datetime.now(UTC)` or `datetime(..., tzinfo=UTC)`)
3. **Return `None`** if the input doesn't match this cluster's patterns (not an error - other clusters will try)
4. **Use standard libraries**: `datetime`, `re`, `dateutil.relativedelta` (if needed)
5. **Handle edge cases**: Case-insensitive matching, whitespace, punctuation variations

## Test Structure Requirements

Each test file must:
1. **Use pytest** with `@pytest.mark.parametrize` for multiple test cases
2. **Test all error cases** from the cluster (use the examples from REASON node)
3. **Assert valid datetime**: Result is not None, is datetime instance, has UTC timezone
4. **Follow naming**: `test_<cluster_id>.py` matches `parsers/<cluster_id>.py`

## Planning Process

For each selected cluster, you must plan:

1. **Parsing Strategy**:
   - What regex patterns or dateutil features will be used?
   - How will you handle variations (case, whitespace, punctuation)?
   - What edge cases need special handling?

2. **Code Structure**:
   - What helper functions (if any) will the module need?
   - How will patterns be organized (regex dict, if/elif chain, etc.)?
   - What imports are needed?

3. **Test Cases**:
   - List all error examples from the cluster that will become test cases
   - What additional edge cases should be tested?
   - What should the expected datetime values be (relative to "now")?

4. **Dependencies**:
   - What Python standard library modules are needed?
   - Are any third-party packages required (dateutil, etc.)?

## Output Requirements

You must output a JSON object with the following structure:

```json
{
    "cluster_plans": [
        {
            "cluster_id": "relative_dates",
            "parsing_strategy": "Use dateutil.relativedelta for relative date arithmetic. Match patterns like 'tomorrow', 'next week', 'in N days', 'Monday morning' using regex, then calculate datetime relative to now(UTC).",
            "code_structure": "Single parse() function with regex pattern matching dictionary. Patterns map to lambda functions that calculate relative dates.",
            "test_cases": [
                {"input": "tomorrow", "description": "Basic relative date"},
                {"input": "next week", "description": "Week-based relative date"},
                {"input": "in 2 days", "description": "N days in future"},
                {"input": "Monday morning", "description": "Day of week with time of day"}
            ],
            "dependencies": ["datetime", "re", "dateutil.relativedelta"],
            "edge_cases": ["Case variations (Tomorrow, TOMORROW)", "Whitespace variations", "Punctuation (tomorrow!)"]
        }
    ],
    "implementation_notes": "All modules will be generated together. Ensure consistent error handling and return types across modules."
}
```

**Field Descriptions:**
- `cluster_plans`: Array of plans, one per selected cluster
  - `cluster_id`: Must match cluster_id from REASON node
  - `parsing_strategy`: High-level description of how to parse this cluster
  - `code_structure`: Description of code organization (functions, data structures, etc.)
  - `test_cases`: List of test case objects with input and description
  - `dependencies`: List of required imports
  - `edge_cases`: List of edge cases to handle
- `implementation_notes`: Any cross-cluster considerations

## Important Guidelines

- **Keep modules focused**: Each module handles one cluster's patterns
- **Use standard libraries**: Prefer datetime, re, dateutil over custom solutions
- **Handle variations**: Case-insensitive, whitespace-tolerant, punctuation-tolerant
- **Return None for non-matches**: Don't raise exceptions - let other clusters try
- **UTC timezone**: All datetimes must be timezone-aware with UTC
- **Test comprehensively**: Include all error examples plus edge cases
"""
```

#### PLAN_NODE_USER_PROMPT_TEMPLATE

```python
PLAN_NODE_USER_PROMPT_TEMPLATE: str = """
Selected Error Clusters for Processing:

{cluster_analysis}

Existing Cluster Modules (if any):

{existing_cluster_modules}

The cluster_analysis contains the selected clusters from the REASON node, including:
- cluster_id: The identifier that will become the module filename
- examples: Example timing_description strings that failed to parse
- suggested_approach: High-level parsing approach
- error_indices: Original error indices (for reference)

The existing_cluster_modules list shows any cluster modules that already exist (so you can see what patterns are already handled).

Your task:
1. For each selected cluster, design a detailed plan for the parsing module
2. Plan the corresponding test file with all test cases
3. Consider how to handle edge cases and variations
4. Return the planning document in the exact JSON format specified in the system prompt

Focus on:
- Creating efficient, maintainable code
- Handling all examples from the cluster
- Using standard Python libraries where possible
- Writing comprehensive tests
- Ensuring modules can coexist (no conflicts)
"""
```

### 18.3 ACT Node Prompts (Code Generation)

**Purpose:** Generate the actual Python code for cluster modules and test files.

#### ACT_NODE_SYSTEM_PROMPT_TEMPLATE

```python
ACT_NODE_SYSTEM_PROMPT_TEMPLATE: str = """
You are an expert Python developer specializing in natural language time parsing. Your task is to generate complete, production-ready Python modules and test files based on the planning document.

## Context

You are generating code for a modular time parser system where:
- Each error cluster gets its own module: `time_parser/parsers/<cluster_id>.py`
- Each module exports: `def parse(text: str) -> datetime | None`
- Each cluster gets a test file: `time_parser/tests/test_<cluster_id>.py`
- Modules are discovered and loaded dynamically by the main parser

## Code Generation Requirements

### Module Code (`parsers/<cluster_id>.py`)

**Required Structure:**
```python
\"\"\"Parser module for <cluster_id> cluster.\"\"\"
from datetime import datetime, timedelta, UTC
import re
# Additional imports as needed (e.g., from dateutil.relativedelta import relativedelta)

def parse(text: str) -> datetime | None:
    \"\"\"Parse <cluster_description> expressions.
    
    Args:
        text: Time expression string to parse
        
    Returns:
        datetime object with UTC timezone if successful, None otherwise
    \"\"\"
    # Implementation here
    # Must return datetime with UTC timezone or None
```

**Critical Requirements:**
1. **Function signature**: Must be exactly `def parse(text: str) -> datetime | None`
2. **Return type**: Return `datetime` with UTC timezone or `None` (never raise exceptions for non-matches)
3. **Case-insensitive**: Handle "Tomorrow", "tomorrow", "TOMORROW" the same way
4. **Whitespace-tolerant**: Handle extra spaces, tabs, newlines
5. **Punctuation-tolerant**: Handle trailing punctuation (e.g., "tomorrow!", "next week.")
6. **UTC timezone**: All datetimes must use `UTC` timezone
7. **Code quality**: Use clear variable names, add comments for complex logic
8. **Efficiency**: Use regex efficiently, avoid unnecessary loops

### Test File Code (`tests/test_<cluster_id>.py`)

**Required Structure:**
```python
\"\"\"Tests for <cluster_id> parser module.\"\"\"
import pytest
from datetime import datetime, UTC
from time_parser.parsers.<cluster_id> import parse

@pytest.mark.parametrize("input_text,expected_day_offset", [
    ("tomorrow", 1),
    ("next week", 7),
    # ... more test cases
])
def test_<cluster_id>(input_text: str, expected_day_offset: int):
    \"\"\"Test parsing of <cluster_description> expressions.\"\"\"
    result = parse(input_text)
    assert result is not None, f"Failed to parse: {input_text}"
    assert isinstance(result, datetime), f"Result not datetime: {input_text}"
    assert result.tzinfo is not None, f"Result not timezone-aware: {input_text}"
    assert result.tzinfo == UTC, f"Result not UTC: {input_text}"
    # Additional assertions as needed
```

**Critical Requirements:**
1. **Parameterized tests**: Use `@pytest.mark.parametrize` for multiple cases
2. **Test all examples**: Include all error examples from the cluster
3. **Assertions**: Check for None, datetime type, timezone awareness, UTC timezone
4. **Test edge cases**: Case variations, whitespace, punctuation
5. **Clear test names**: Descriptive test function names

## Output Requirements

You must output a JSON object with the following structure:

```json
{
    "cluster_modules": {
        "relative_dates": "# time_parser/parsers/relative_dates.py\n\"\"\"Parser module for relative date expressions.\"\"\"\nfrom datetime import datetime, timedelta, UTC\nimport re\n\ndef parse(text: str) -> datetime | None:\n    # ... complete module code ...",
        "specific_dates": "# time_parser/parsers/specific_dates.py\n\"\"\"Parser module for specific date expressions.\"\"\"\n# ... complete module code ..."
    },
    "test_files": {
        "relative_dates": "# time_parser/tests/test_relative_dates.py\n\"\"\"Tests for relative_dates parser module.\"\"\"\nimport pytest\n# ... complete test file code ...",
        "specific_dates": "# time_parser/tests/test_specific_dates.py\n\"\"\"Tests for specific_dates parser module.\"\"\"\n# ... complete test file code ..."
    }
}
```

**Field Descriptions:**
- `cluster_modules`: Dictionary mapping cluster_id to complete module code (as string)
  - Code must be complete, syntactically correct Python
  - Include file header comment with module description
  - Code should be ready to write directly to file
- `test_files`: Dictionary mapping cluster_id to complete test file code (as string)
  - Code must be complete, syntactically correct Python
  - Include file header comment
  - All test cases from planning document must be included

## Code Quality Guidelines

1. **Follow PEP 8**: Use proper Python style
2. **Add docstrings**: Document functions and modules
3. **Handle edge cases**: Case, whitespace, punctuation variations
4. **Use type hints**: Include return type annotations
5. **Error handling**: Return None for non-matches (don't raise exceptions)
6. **Efficient patterns**: Use compiled regex if repeated, use dict lookups for patterns
7. **Comments**: Add comments for complex logic or non-obvious decisions

## Important Notes

- Generate COMPLETE files - not snippets or partial code
- Each module must be self-contained and importable
- Test files must import from the corresponding parser module
- All code must be syntactically correct and ready to execute
- Use UTC timezone for all datetime objects
- Return None (not raise exceptions) when input doesn't match cluster patterns
"""
```

#### ACT_NODE_USER_PROMPT_TEMPLATE

```python
ACT_NODE_USER_PROMPT_TEMPLATE: str = """
Code Planning Document:

{code_plan}

The code_plan contains the detailed plans for each selected cluster, including:
- parsing_strategy: How to parse this cluster
- code_structure: Code organization approach
- test_cases: All test cases to include
- dependencies: Required imports
- edge_cases: Edge cases to handle

Your task:
1. Generate complete Python module code for each cluster in `cluster_modules`
2. Generate complete test file code for each cluster in `test_files`
3. Ensure all code is syntactically correct and follows the requirements
4. Include all test cases from the planning document
5. Return the code in the exact JSON format specified in the system prompt

Remember:
- Each module must export a `parse(text: str) -> datetime | None` function
- All datetimes must use UTC timezone
- Return None (not raise exceptions) for non-matches
- Test files must use pytest with parameterized tests
- Code must be complete and ready to write to files
"""
```

### 18.4 Prompt Usage in Workflow

**Integration Pattern:**
```python
# coding_agent/prompts.py
from pydantic import BaseModel

class SystemAndUserPromptPair(BaseModel):
    system_prompt: str
    user_prompt: str

class NodePrompts(BaseModel):
    reason: SystemAndUserPromptPair | None = None
    plan: SystemAndUserPromptPair | None = None
    act: SystemAndUserPromptPair | None = None

# In workflow setup:
node_prompts: NodePrompts = NodePrompts(
    reason=SystemAndUserPromptPair(
        system_prompt=REASON_NODE_SYSTEM_PROMPT_TEMPLATE,
        user_prompt=REASON_NODE_USER_PROMPT_TEMPLATE.format(
            error_queue_contents=error_queue_content_string
        ),
    ),
    plan=SystemAndUserPromptPair(
        system_prompt=PLAN_NODE_SYSTEM_PROMPT_TEMPLATE,
        user_prompt=PLAN_NODE_USER_PROMPT_TEMPLATE.format(
            cluster_analysis=cluster_analysis_json_string,
            existing_cluster_modules=existing_modules_list_string
        ),
    ),
    act=SystemAndUserPromptPair(
        system_prompt=ACT_NODE_SYSTEM_PROMPT_TEMPLATE,
        user_prompt=ACT_NODE_USER_PROMPT_TEMPLATE.format(
            code_plan=code_plan_json_string
        ),
    ),
)
```

**Note:** These are draft prompts. They should be refined based on:
- Actual LLM responses and behavior
- Error patterns observed in real error queue data
- Performance and accuracy requirements
- Gemini 3 specific characteristics

