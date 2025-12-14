"""Coding agent workflow for self-healing time parser."""
import fcntl
import json
import keyword
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from coding_agent.base import (
    AnnotationState,
    DEFAULT_RATE_LIMITING_CONFIG,
    RateLimitingConfig,
    WorkflowBase,
)
from coding_agent import config
from coding_agent.error_queue import append_error_to_queue, read_error_queue, remove_processed_cluster_errors
from coding_agent.llms import NodeLLMs
from coding_agent.prompts import NodePrompts
from coding_agent.reloader import reload_parser
from coding_agent.test_runner import run_pytest
from utils.llm_output_parsing_util import (
    extract_act_node_output,
    extract_plan_node_output,
    extract_reason_node_output,
)

logger = logging.getLogger(__name__)


def _sanitize_cluster_id(cluster_id: str) -> str:
    """Sanitize cluster ID to be a valid Python module name.
    
    Args:
        cluster_id: Original cluster ID string
        
    Returns:
        Sanitized cluster ID that is a valid Python identifier
    """
    # Step 1: Convert to lowercase
    cluster_id = cluster_id.lower()
    
    # Step 2: Replace spaces and special characters with underscores
    cluster_id = re.sub(r'[^a-z0-9_]', '_', cluster_id)
    
    # Step 3: Remove leading/trailing underscores
    cluster_id = cluster_id.strip('_')
    
    # Step 4: Replace multiple consecutive underscores with single underscore
    cluster_id = re.sub(r'_+', '_', cluster_id)
    
    # Step 5: Ensure starts with letter or underscore
    if cluster_id and cluster_id[0].isdigit():
        cluster_id = f"cluster_{cluster_id}"
    
    # Step 6: Validate - check if empty or is a Python keyword
    if not cluster_id or keyword.iskeyword(cluster_id):
        cluster_id = f"{cluster_id}_cluster" if cluster_id else "cluster"
    
    # Step 7: Final validation - ensure result is non-empty and valid Python identifier
    if not cluster_id or not cluster_id.isidentifier():
        cluster_id = "cluster"
    
    return cluster_id


class CodingAgentWorkflow(WorkflowBase):
    """Self-healing coding agent using R/P/A pattern."""
    
    def __init__(
        self,
        error_queue_path: str | Path,
        parsers_dir: str | Path,
        tests_dir: str | Path,
        node_llms: NodeLLMs,
        node_prompts: NodePrompts,
        thread_id: str,
        rate_limiting_config: RateLimitingConfig = DEFAULT_RATE_LIMITING_CONFIG,
        fail_fast: bool = False,
        error_logging: bool = True,
        debug_logging: bool = False,
        enforce_structured_llm_output: bool = False,
    ) -> None:
        """Initialize the coding agent workflow.
        
        Args:
            error_queue_path: Path to error queue JSONL file
            parsers_dir: Directory for cluster parser modules
            tests_dir: Directory for test files
            node_llms: LLM configuration for each node
            node_prompts: Prompt templates for each node
            thread_id: Unique thread identifier
            rate_limiting_config: Rate limiting configuration
            fail_fast: Whether to fail fast on errors
            error_logging: Whether to log errors
            debug_logging: Whether to enable debug logging
            enforce_structured_llm_output: Whether to enforce structured output (should be False for schema=None)
        """
        # Store configuration as instance variables
        self._error_queue_path = Path(error_queue_path)
        self._parsers_dir = Path(parsers_dir)
        self._tests_dir = Path(tests_dir)
        
        # Call super().__init__() with required parameters
        super().__init__(
            node_llms=node_llms,
            node_prompts=node_prompts,
            thread_id=thread_id,
            enforce_structured_llm_output=enforce_structured_llm_output,
            rate_limiting_config=rate_limiting_config,
            fail_fast=fail_fast,
            error_logging=error_logging,
            debug_logging=debug_logging,
        )
    
    def _sanitize_cluster_id(self, cluster_id: str) -> str:
        """Sanitize cluster ID to be a valid Python module name.
        
        Args:
            cluster_id: Original cluster ID string
            
        Returns:
            Sanitized cluster ID that is a valid Python identifier
        """
        return _sanitize_cluster_id(cluster_id)
    
    def _check_early_exit(self, state: AnnotationState) -> str:
        """Check if workflow should exit early.
        
        Args:
            state: Current workflow state
            
        Returns:
            "exit" if early_exit flag is set, "continue" otherwise
        """
        if state["node_output"] and state["node_output"].get("early_exit") is True:
            return "exit"
        return "continue"
    
    def _add_workflow_nodes_and_edges(self, workflow: StateGraph) -> None:
        """Add workflow nodes and edges to the graph.
        
        Args:
            workflow: The StateGraph to add nodes and edges to
        """
        # Add nodes
        workflow.add_node("reason", self._reason_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("act", self._act_node)
        workflow.add_node("validate", self._validate_node)
        
        # Set entry point
        workflow.add_edge(START, "reason")
        
        # Add conditional edge from reason (check for early exit)
        workflow.add_conditional_edges(
            "reason",
            self._check_early_exit,
            {"continue": "plan", "exit": END}
        )
        
        # Add conditional edge from plan (check for early exit)
        workflow.add_conditional_edges(
            "plan",
            self._check_early_exit,
            {"continue": "act", "exit": END}
        )
        
        # Add conditional edge from act (check for early exit)
        workflow.add_conditional_edges(
            "act",
            self._check_early_exit,
            {"continue": "validate", "exit": END}
        )
        
        # Add conditional edge from validate (retry logic)
        workflow.add_conditional_edges(
            "validate",
            self._should_retry,
            {"success": END, "retry": "plan", "failure": END}
        )
    
    def _reason_node(self, state: AnnotationState) -> AnnotationState:
        """REASON node - analyze errors and cluster them.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with error clusters and selected clusters
        """
        try:
            # Read full error queue
            all_errors = read_error_queue(self._error_queue_path)
            
            # Filter errors: Only include rows where deadline_at is null (parsing failures)
            filtered_errors = [error for error in all_errors if error.get("deadline_at") is None]
            
            # Create mapping from filtered index to global index
            filtered_to_global = {}
            filtered_idx = 0
            for global_idx, error in enumerate(all_errors):
                if error.get("deadline_at") is None:
                    filtered_to_global[filtered_idx] = global_idx
                    filtered_idx += 1
            
            # Error handling: If no errors found, set early exit
            if not filtered_errors:
                node_output = state["node_output"] or {}
                node_output["error_clusters"] = []
                node_output["selected_clusters"] = []
                node_output["cluster_error_indices"] = {}
                node_output["early_exit"] = True
                state["final_output"] = {
                    "success": True,
                    "processed_clusters": [],
                    "errors_removed_count": 0,
                    "parser_updated": False,
                    "tests_passed": False,
                    "retry_count": 0,
                    "message": "No errors to process",
                }
                state["node_output"] = node_output
                return state
            
            # Format error queue contents as JSONL string
            error_queue_contents = "\n".join(json.dumps(error) for error in filtered_errors)
            
            # Get prompts
            system_and_user_prompt_pair = self._node_prompts.reason
            if system_and_user_prompt_pair is None:
                raise ValueError("REASON node prompts not configured")
            
            system_prompt = system_and_user_prompt_pair.system_prompt
            user_prompt = system_and_user_prompt_pair.user_prompt.format(
                error_queue_contents=error_queue_contents
            )
            
            # Call LLM
            response = self._call_llm_with_prompt(
                node_name="reason",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=None,
            )
            
            # Parse JSON response
            if not isinstance(response, AIMessage):
                raise ValueError(f"Expected AIMessage, got {type(response)}")
            
            parsed_response = self._llm_json_parser.parse_llm_json_extraction_response(
                response.content,
                fail_fast=self._fail_fast,
                context_identifier=("Node", "reason"),
                debug_logging=self._debug_logging,
            )
            
            if parsed_response is None or len(parsed_response) == 0:
                # Log the actual response for debugging
                response_str = str(response.content) if not isinstance(response.content, str) else response.content
                logger.error(
                    f"REASON node LLM response parsing failed. Response type: {type(response.content)}, "
                    f"Response length: {len(response_str) if isinstance(response_str, str) else 'N/A'}, "
                    f"Response preview: {response_str[:500] if isinstance(response_str, str) else response_str}"
                )
                raise ValueError("REASON node LLM response parsing failed")
            
            # Extract data using helper function
            extracted_data = extract_reason_node_output(parsed_response)
            
            # Sanitize cluster IDs immediately after extraction
            for cluster in extracted_data["clusters"]:
                original_cluster_id = cluster["cluster_id"]
                sanitized_cluster_id = self._sanitize_cluster_id(original_cluster_id)
                cluster["cluster_id"] = sanitized_cluster_id
            
            # Sanitize selected_clusters and filter to only include clusters that exist
            sanitized_selected = []
            sanitized_cluster_ids = {c["cluster_id"] for c in extracted_data["clusters"]}
            for cluster_id in extracted_data["selected_clusters"]:
                sanitized_id = self._sanitize_cluster_id(cluster_id)
                if sanitized_id in sanitized_cluster_ids:
                    sanitized_selected.append(sanitized_id)
            
            extracted_data["selected_clusters"] = sanitized_selected
            
            # Map error indices from filtered to global
            for cluster in extracted_data["clusters"]:
                filtered_indices = cluster["error_indices"]
                cluster["error_indices"] = [
                    filtered_to_global[idx] for idx in filtered_indices if idx in filtered_to_global
                ]
            
            # Store in state
            node_output = state["node_output"] or {}
            node_output["error_clusters"] = extracted_data["clusters"]
            node_output["selected_clusters"] = extracted_data["selected_clusters"]
            node_output["cluster_error_indices"] = {
                cluster["cluster_id"]: cluster["error_indices"]
                for cluster in extracted_data["clusters"]
                if cluster["cluster_id"] in extracted_data["selected_clusters"]
            }
            
            # Construct messages for state update
            system_message = SystemMessage(content=system_prompt)
            human_message = HumanMessage(content=user_prompt)
            messages = [system_message, human_message, response]
            
            # Update state
            self._update_state(state, messages=messages, node_output=node_output)
            
            return state
            
        except Exception as e:
            error_msg = f"REASON node failed: {e}"
            logger.error(error_msg, exc_info=True)
            if self._fail_fast:
                raise RuntimeError(error_msg) from e
            else:
                # Log warning and return state with error indicators
                logger.warning(error_msg)
                node_output = state["node_output"] or {}
                node_output["error"] = error_msg
                state["node_output"] = node_output
                return state
    
    def _plan_node(self, state: AnnotationState) -> AnnotationState:
        """PLAN node - design code changes and test strategy.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with code plan
        """
        try:
            # Check for early exit
            if state["node_output"] and state["node_output"].get("early_exit") is True:
                return state
            
            # Read existing cluster modules from parsers_dir
            existing_cluster_modules = []
            parsers_dir = Path(self._parsers_dir)
            
            if parsers_dir.exists():
                for module_file in parsers_dir.glob("*.py"):
                    if module_file.name == "__init__.py":
                        continue
                    
                    module_name = module_file.stem
                    description = "Parser module for {module_name} patterns".format(
                        module_name=module_name
                    )
                    
                    try:
                        # Read file content
                        content = module_file.read_text(encoding="utf-8")
                        
                        # Try to extract module docstring
                        lines = content.split("\n")
                        in_docstring = False
                        docstring_content = []
                        
                        for line in lines:
                            stripped = line.strip()
                            # Check for docstring start
                            if stripped.startswith('"""') or stripped.startswith("'''"):
                                if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                                    # Single-line docstring
                                    docstring = stripped.strip('"""').strip("'''").strip()
                                    if docstring:
                                        description = docstring[:100].strip()
                                        break
                                else:
                                    # Multi-line docstring start
                                    in_docstring = True
                                    docstring_content.append(
                                        stripped.strip('"""').strip("'''").strip()
                                    )
                                    continue
                            
                            if in_docstring:
                                if '"""' in stripped or "'''" in stripped:
                                    # Docstring end
                                    docstring_content.append(
                                        stripped.replace('"""', "").replace("'''", "").strip()
                                    )
                                    docstring = " ".join(docstring_content).strip()
                                    if docstring:
                                        description = docstring[:100].strip()
                                    break
                                else:
                                    docstring_content.append(stripped)
                        
                        # If no docstring found, try to extract first non-empty, non-import, non-comment line
                        if description == "Parser module for {module_name} patterns".format(
                            module_name=module_name
                        ):
                            for line in lines:
                                stripped = line.strip()
                                if (
                                    stripped
                                    and not stripped.startswith("#")
                                    and not stripped.startswith("import")
                                    and not stripped.startswith("from")
                                ):
                                    description = stripped[:100].strip()
                                    break
                        
                        # Truncate description to max 150 characters
                        description = description[:150]
                        
                    except Exception as e:
                        logger.warning(
                            f"Failed to extract description from {module_file}: {e}"
                        )
                    
                    existing_cluster_modules.append({
                        "module_name": module_name,
                        "description": description,
                    })
            
            # Format existing_cluster_modules as string
            existing_modules_str = json.dumps(existing_cluster_modules, indent=2)
            
            # Format cluster_analysis from state
            node_output = state["node_output"] or {}
            error_clusters = node_output.get("error_clusters", [])
            selected_clusters = node_output.get("selected_clusters", [])
            
            # Error handling: If selected_clusters is empty or None, set early exit
            if not selected_clusters:
                node_output["code_plan"] = {}
                node_output["early_exit"] = True
                state["final_output"] = {
                    "success": True,
                    "processed_clusters": [],
                    "errors_removed_count": 0,
                    "parser_updated": False,
                    "tests_passed": False,
                    "retry_count": 0,
                    "message": "No clusters selected for processing",
                }
                state["node_output"] = node_output
                return state
            
            # Create cluster_analysis: filter error_clusters by selected_clusters
            cluster_analysis_list = [
                cluster
                for cluster in error_clusters
                if cluster.get("cluster_id") in selected_clusters
            ]
            cluster_analysis = json.dumps(cluster_analysis_list, indent=2)
            
            # Get prompts
            system_and_user_prompt_pair = self._node_prompts.plan
            if system_and_user_prompt_pair is None:
                raise ValueError("PLAN node prompts not configured")
            
            system_prompt = system_and_user_prompt_pair.system_prompt
            user_prompt = system_and_user_prompt_pair.user_prompt.format(
                cluster_analysis=cluster_analysis,
                existing_cluster_modules=existing_modules_str,
            )
            
            # Call LLM
            response = self._call_llm_with_prompt(
                node_name="plan",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=None,
            )
            
            # Parse JSON response
            if not isinstance(response, AIMessage):
                raise ValueError(f"Expected AIMessage, got {type(response)}")
            
            parsed_response = self._llm_json_parser.parse_llm_json_extraction_response(
                response.content,
                fail_fast=self._fail_fast,
                context_identifier=("Node", "plan"),
                debug_logging=self._debug_logging,
            )
            
            if parsed_response is None or len(parsed_response) == 0:
                raise ValueError("PLAN node LLM response parsing failed")
            
            # Extract code_plan using helper function
            code_plan = extract_plan_node_output(parsed_response)
            
            # Error handling: Check if cluster_plans is empty
            if not code_plan.get("cluster_plans"):
                raise ValueError("code_plan has empty cluster_plans array")
            
            # Update state
            node_output = state["node_output"] or {}
            node_output["code_plan"] = code_plan
            
            # Construct messages for state update
            system_message = SystemMessage(content=system_prompt)
            human_message = HumanMessage(content=user_prompt)
            messages = [system_message, human_message, response]
            
            # Update state
            self._update_state(state, messages=messages, node_output=node_output)
            
            return state
            
        except Exception as e:
            error_msg = f"PLAN node failed: {e}"
            logger.error(error_msg, exc_info=True)
            if self._fail_fast:
                raise RuntimeError(error_msg) from e
            else:
                # Log warning and return state with error indicators
                # Preserve existing code_plan if it exists (so ACT can still use it on retry)
                logger.warning(error_msg)
                node_output = state["node_output"] or {}
                # Preserve code_plan if it already exists (don't clear it on PLAN failure)
                existing_code_plan = node_output.get("code_plan")
                node_output["error"] = error_msg
                if existing_code_plan:
                    node_output["code_plan"] = existing_code_plan
                state["node_output"] = node_output
                return state
    
    def _write_file_with_lock(self, file_path: Path, content: str) -> None:
        """Write file atomically with file locking.
        
        Args:
            file_path: Path to target file
            content: Content to write
            
        Raises:
            IOError: If file writing fails after retries
        """
        temp_file = file_path.with_suffix(f"{file_path.suffix}.tmp")
        
        # Retry lock acquisition up to 3 times
        for attempt in range(3):
            try:
                with open(temp_file, "w", encoding="utf-8") as f:
                    # Acquire exclusive lock (blocking)
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    
                    # Write content
                    f.write(content)
                    
                    # Flush and sync
                    f.flush()
                    os.fsync(f.fileno())
                    
                    # Release lock
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                
                # Atomically rename
                temp_file.replace(file_path)
                return
                
            except (IOError, OSError) as e:
                if attempt < 2:
                    time.sleep(0.1)
                    continue
                # Last attempt failed, clean up and raise
                temp_file.unlink(missing_ok=True)
                raise IOError(f"Failed to write file {file_path} after 3 attempts: {e}") from e
        
        # Should not reach here, but just in case
        temp_file.unlink(missing_ok=True)
        raise IOError(f"Failed to write file {file_path}")
    
    def _act_node(self, state: AnnotationState) -> AnnotationState:
        """ACT node - generate code for cluster modules and test files.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with generated cluster modules and test files
        """
        try:
            # Check for early exit
            if state["node_output"] and state["node_output"].get("early_exit") is True:
                return state
            
            # Get code_plan from state
            node_output = state["node_output"] or {}
            code_plan = node_output.get("code_plan")
            
            if code_plan is None:
                # Check if there's an error indicating PLAN failed - if so, this is a critical failure
                error = node_output.get("error", "")
                if "PLAN node failed" in error:
                    raise ValueError(
                        f"code_plan is None and PLAN node failed: {error}. "
                        "Cannot generate code without a plan."
                    )
                else:
                    raise ValueError("code_plan is None or missing from state")
            
            if not code_plan.get("cluster_plans"):
                raise ValueError("code_plan has no cluster_plans to generate code for")
            
            # Format code_plan as JSON string
            code_plan_str = json.dumps(code_plan, indent=2)
            
            # Get prompts
            system_and_user_prompt_pair = self._node_prompts.act
            if system_and_user_prompt_pair is None:
                raise ValueError("ACT node prompts not configured")
            
            system_prompt = system_and_user_prompt_pair.system_prompt
            user_prompt = system_and_user_prompt_pair.user_prompt.format(
                code_plan=code_plan_str
            )
            
            # Call LLM
            response = self._call_llm_with_prompt(
                node_name="act",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=None,
            )
            
            # Parse JSON response
            if not isinstance(response, AIMessage):
                raise ValueError(f"Expected AIMessage, got {type(response)}")
            
            parsed_response = self._llm_json_parser.parse_llm_json_extraction_response(
                response.content,
                fail_fast=self._fail_fast,
                context_identifier=("Node", "act"),
                debug_logging=self._debug_logging,
            )
            
            if parsed_response is None or len(parsed_response) == 0:
                raise ValueError("ACT node LLM response parsing failed")
            
            # Extract cluster_modules and test_files
            extracted_data = extract_act_node_output(parsed_response)
            
            cluster_modules_raw = extracted_data.get("cluster_modules", {})
            test_files_raw = extracted_data.get("test_files", {})
            
            if not cluster_modules_raw or not test_files_raw:
                raise ValueError(
                    "ACT node response missing cluster_modules or test_files"
                )
            
            # Sanitize cluster IDs in extracted data
            cluster_modules = {}
            test_files = {}
            
            for cluster_id, code_string in cluster_modules_raw.items():
                sanitized_id = self._sanitize_cluster_id(cluster_id)
                cluster_modules[sanitized_id] = code_string
            
            for cluster_id, test_code_string in test_files_raw.items():
                sanitized_id = self._sanitize_cluster_id(cluster_id)
                test_files[sanitized_id] = test_code_string
            
            # Basic validation: Check that code strings are not empty
            for cluster_id, code in cluster_modules.items():
                if not code or not code.strip():
                    raise ValueError(f"Empty code for cluster module: {cluster_id}")
            
            for cluster_id, test_code in test_files.items():
                if not test_code or not test_code.strip():
                    raise ValueError(f"Empty test code for cluster: {cluster_id}")
            
            # Write cluster module files
            parsers_dir = Path(self._parsers_dir)
            parsers_dir.mkdir(parents=True, exist_ok=True)
            
            for cluster_id, code in cluster_modules.items():
                module_path = parsers_dir / f"{cluster_id}.py"
                self._write_file_with_lock(module_path, code)
            
            # Write test files
            tests_dir = Path(self._tests_dir)
            tests_dir.mkdir(parents=True, exist_ok=True)
            
            for cluster_id, test_code in test_files.items():
                test_path = tests_dir / f"test_{cluster_id}.py"
                self._write_file_with_lock(test_path, test_code)
            
            # Update state
            node_output = state["node_output"] or {}
            node_output["generated_cluster_modules"] = cluster_modules
            node_output["generated_test_files"] = test_files
            
            # Construct messages for state update
            system_message = SystemMessage(content=system_prompt)
            human_message = HumanMessage(content=user_prompt)
            messages = [system_message, human_message, response]
            
            # Update state
            self._update_state(state, messages=messages, node_output=node_output)
            
            return state
            
        except Exception as e:
            error_msg = f"ACT node failed: {e}"
            logger.error(error_msg, exc_info=True)
            if self._fail_fast:
                raise RuntimeError(error_msg) from e
            else:
                # Log warning and return state with error indicators
                logger.warning(error_msg)
                node_output = state["node_output"] or {}
                node_output["error"] = error_msg
                state["node_output"] = node_output
                return state
    
    def _validate_node(self, state: AnnotationState) -> AnnotationState:
        """VALIDATE node - run tests and validate all pass.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with test results
        """
        try:
            # Run pytest
            try:
                run_pytest_result = run_pytest(self._tests_dir, verbose=True)
            except Exception as e:
                logger.error(f"pytest execution failed: {e}", exc_info=True)
                run_pytest_result = {
                    "all_passed": False,
                    "test_output": "",
                    "test_errors": str(e),
                    "returncode": 1,
                }
            
            test_results = run_pytest_result
            
            # Get and increment retry_count
            node_output = state["node_output"] or {}
            retry_count = node_output.get("retry_count", 0)
            retry_count += 1
            
            # Update state with test results
            node_output["test_results"] = test_results
            node_output["retry_count"] = retry_count
            
            # If tests pass, perform queue cleanup and module reloading
            if test_results["all_passed"]:
                # Queue cleanup (Task 10.1)
                cluster_error_indices = node_output.get("cluster_error_indices", {})
                all_error_indices = [
                    idx
                    for indices in cluster_error_indices.values()
                    for idx in indices
                ]
                
                if all_error_indices:
                    remove_processed_cluster_errors(
                        self._error_queue_path, all_error_indices
                    )
                
                errors_removed_count = len(all_error_indices)
                
                # Module reloading (Task 10.2)
                reload_parser(self._parsers_dir)
                
                # Get processed clusters
                processed_clusters = node_output.get("selected_clusters", [])
                
                # Create final_output
                final_output = {
                    "success": True,
                    "processed_clusters": processed_clusters,
                    "errors_removed_count": errors_removed_count,
                    "parser_updated": True,
                    "tests_passed": True,
                    "retry_count": retry_count,
                    "generated_cluster_modules": node_output.get(
                        "generated_cluster_modules", {}
                    ),
                    "generated_test_files": node_output.get("generated_test_files", {}),
                    "cluster_error_indices": cluster_error_indices,
                }
                
                state["final_output"] = final_output
                node_output["errors_removed_count"] = errors_removed_count
                node_output["parser_reloaded"] = True
            
            # Update state
            state["node_output"] = node_output
            
            return state
            
        except Exception as e:
            error_msg = f"VALIDATE node failed: {e}"
            logger.error(error_msg, exc_info=True)
            if self._fail_fast:
                raise RuntimeError(error_msg) from e
            else:
                # Log warning and set test_results with all_passed=False
                logger.warning(error_msg)
                node_output = state["node_output"] or {}
                node_output["test_results"] = {
                    "all_passed": False,
                    "test_output": "",
                    "test_errors": error_msg,
                    "returncode": 1,
                }
                state["node_output"] = node_output
                return state
    
    def _should_retry(self, state: AnnotationState) -> str:
        """Determine if workflow should retry or succeed.
        
        Args:
            state: Current workflow state
            
        Returns:
            "success", "retry", or "failure"
        """
        test_results = state["node_output"].get("test_results", {})
        
        if test_results.get("all_passed") is True:
            return "success"
        
        node_output = state["node_output"] or {}
        retry_count = node_output.get("retry_count", 0)
        
        # Check for critical errors that prevent progress (e.g., ACT node failed or PLAN node failed)
        critical_error = node_output.get("error")
        if critical_error:
            # Check if it's a critical error from ACT or PLAN node
            is_critical = (
                "ACT node failed" in critical_error or 
                "PLAN node failed" in critical_error
            )
            
            if is_critical:
                # If we've already retried at least once, don't retry again
                if retry_count >= 1:
                    # Set final_output and return failure
                    self._log_failed_batch(state)
                    selected_clusters = node_output.get("selected_clusters", [])
                    cluster_error_indices = node_output.get("cluster_error_indices", {})
                    
                    state["final_output"] = {
                        "success": False,
                        "processed_clusters": selected_clusters,
                        "errors_removed_count": 0,
                        "parser_updated": False,
                        "tests_passed": False,
                        "retry_count": retry_count,
                        "message": f"Workflow failed due to critical error: {critical_error}",
                        "test_results": test_results,
                        "cluster_error_indices": cluster_error_indices,
                        "generated_cluster_modules": node_output.get("generated_cluster_modules", {}),
                        "generated_test_files": node_output.get("generated_test_files", {}),
                    }
                    return "failure"
        
        if retry_count < config.MAX_RETRY_ATTEMPTS:
            return "retry"
        
        # Max retries reached - log failed batch and set final_output before returning failure
        self._log_failed_batch(state)
        
        # Set final_output to indicate failure (BUG FIX: was missing before)
        selected_clusters = node_output.get("selected_clusters", [])
        cluster_error_indices = node_output.get("cluster_error_indices", {})
        all_error_indices = [
            idx
            for indices in cluster_error_indices.values()
            for idx in indices
        ]
        
        # Include error message if present
        error_message = node_output.get("error", "")
        if error_message:
            message = f"Max retries ({config.MAX_RETRY_ATTEMPTS}) reached. Tests did not pass after {retry_count} attempts. Error: {error_message}"
        else:
            message = f"Max retries ({config.MAX_RETRY_ATTEMPTS}) reached. Tests did not pass after {retry_count} attempts."
        
        state["final_output"] = {
            "success": False,
            "processed_clusters": selected_clusters,
            "errors_removed_count": 0,
            "parser_updated": False,
            "tests_passed": False,
            "retry_count": retry_count,
            "message": message,
            "test_results": test_results,
            "cluster_error_indices": cluster_error_indices,
            "generated_cluster_modules": node_output.get("generated_cluster_modules", {}),
            "generated_test_files": node_output.get("generated_test_files", {}),
        }
        
        return "failure"
    
    def _log_failed_batch(self, state: AnnotationState) -> None:
        """Log failed batch to separate file for human review.
        
        Args:
            state: Current workflow state
        """
        try:
            node_output = state["node_output"] or {}
            selected_clusters = node_output.get("selected_clusters", [])
            test_results = node_output.get("test_results", {})
            retry_count = node_output.get("retry_count", 0)
            cluster_error_indices = node_output.get("cluster_error_indices", {})
            
            # Get original errors for samples
            all_errors = read_error_queue(self._error_queue_path)
            error_samples = []
            
            for cluster_id, indices in cluster_error_indices.items():
                cluster_samples = []
                for idx in indices[:3]:  # First 3 errors from each cluster
                    if idx < len(all_errors):
                        cluster_samples.append(all_errors[idx])
                error_samples.extend(cluster_samples)
            
            # Calculate total error count
            total_error_count = sum(len(indices) for indices in cluster_error_indices.values())
            
            # Create failed batch entry
            failed_batch_entry = {
                "selected_clusters": selected_clusters,
                "cluster_error_indices": cluster_error_indices,
                "error_count": total_error_count,
                "test_results": test_results,
                "retry_count": retry_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error_samples": error_samples,
            }
            
            # Append to failed_batches.jsonl
            append_error_to_queue("failed_batches.jsonl", failed_batch_entry)
            
        except Exception as e:
            # Non-critical - log warning but don't raise
            logger.warning(f"Failed to log failed batch: {e}", exc_info=True)

