"""Base workflow classes copied from conversation_analysis/ai_aided_annotations/tasks/base.py.

Copied from: platform/conversation_analysis/conversation_analysis/ai_aided_annotations/tasks/base.py
Date: 2025-12-13
Modified for hackathon project independence
"""
from __future__ import annotations

from abc import ABC, abstractmethod
import logging
import random
from typing import (
    TYPE_CHECKING,
    Any,
)

from langchain_core.language_models import BaseChatModel  # noqa: TC002
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from utils.llm_helpers import call_llm_with_prompt
from utils.llm_json_parser import LLMJsonParser

if TYPE_CHECKING:
    from langchain_core.messages import AIMessage, AnyMessage, BaseMessage
    from langgraph.graph.state import CompiledStateGraph
    from langgraph.types import StateSnapshot

    from coding_agent.llms import NodeLLMs
    from coding_agent.prompts import NodePrompts

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RateLimitingConfig(BaseModel):
    """Configuration for rate limiting between LLM calls."""

    sleep_between_calls: bool = False
    min_delay: int = 13
    max_delay: int = 26
    jitter_percent: float = 0.1

    def should_sleep(self) -> bool:
        """Check if rate limiting should be applied."""
        return self.sleep_between_calls

    def get_sleep_duration(self) -> float:
        """Calculate sleep duration with jitter."""
        if not self.should_sleep():
            return 0.0
        current_delay: float = random.uniform(self.min_delay, self.max_delay)
        jitter: float = random.uniform(0, current_delay * self.jitter_percent)
        return current_delay + jitter


# Module-level default for rate limiting configuration.
DEFAULT_RATE_LIMITING_CONFIG: RateLimitingConfig = RateLimitingConfig()


class AnnotationState(MessagesState):
    """State for annotation workflows."""

    # Node-to-node communication fields.
    node_output: dict[str, Any] | None = Field(
        default=None, description="Output from the current node."
    )
    final_output: dict[str, Any] | None = Field(
        default=None, description="Final output of the workflow."
    )


class WorkflowBase(ABC):
    """Core workflow functionality without conversation dependency."""

    def __init__(
        self,
        node_llms: NodeLLMs,
        node_prompts: NodePrompts,
        thread_id: str,
        enforce_structured_llm_output: bool = False,
        rate_limiting_config: RateLimitingConfig = DEFAULT_RATE_LIMITING_CONFIG,
        fail_fast: bool = False,
        error_logging: bool = True,
        debug_logging: bool = False,
    ) -> None:
        """Initialize the workflow base.

        Args:
            node_llms: Mapping of workflow nodes to their respective language models for each step of the workflow.
            node_prompts: Mapping of workflow nodes to their system and user prompts for each step of the workflow.
            thread_id: Unique identifier for the workflow thread, used for checkpointing and state management.
            enforce_structured_llm_output: Whether to enforce structured output using schemas when available.
            rate_limiting_config: RateLimitingConfig for LLM call delays and sleep behavior.
            fail_fast: Whether to fail fast on errors (True) or continue with error logging (False).
            error_logging: Whether to log warnings and errors when fail_fast is False.
            debug_logging: Whether to log LLM inputs and outputs.
        """
        self._node_llms: NodeLLMs = node_llms
        self._node_prompts: NodePrompts = node_prompts
        self._thread_config: dict[str, Any] = {
            "configurable": {
                "thread_id": thread_id,
            },
        }
        self._enforce_structured_llm_output: bool = enforce_structured_llm_output
        self._rate_limiting_config: RateLimitingConfig = rate_limiting_config
        self._fail_fast: bool = fail_fast
        self._error_logging: bool = error_logging
        self._debug_logging: bool = debug_logging

        # Initialize JSON parser for parsing LLM responses.
        self._llm_json_parser: LLMJsonParser = LLMJsonParser()

        self._graph: CompiledStateGraph = self._build_graph()

    @property
    def graph(self) -> CompiledStateGraph:
        return self._graph

    def run(
        self,
        initial_state: AnnotationState | None = None,
    ) -> dict[str, Any]:
        """Run the workflow.

        Args:
            initial_state: Optional initial state to start from. If None, creates a new empty state.

        Returns:
            Workflow output.
        """
        try:
            # Create initial state if not provided.
            state_to_run: AnnotationState
            if initial_state is None:
                state_to_run = AnnotationState(
                    messages=[],
                    node_output=None,
                    final_output=None,
                )
            else:
                state_to_run = initial_state

            # Run workflow.
            final_state: AnnotationState = self._graph.invoke(
                input=state_to_run,
                config=self._thread_config,
            )

            return final_state["final_output"] or {}
        except Exception as e:
            error_message: str = f"Workflow failed with error: {str(e)}."
            raise RuntimeError(error_message) from e

    def get_state(self) -> StateSnapshot:
        """Get the current state of the workflow.

        Returns:
            The current state snapshot.
        """
        return self._graph.get_state(config=self._thread_config)

    def get_state_history(self) -> list[StateSnapshot]:
        """Get the history of states for the workflow.

        Returns:
            List of state snapshots in chronological order.
        """
        return list(self._graph.get_state_history(config=self._thread_config))

    @staticmethod
    def _update_state(
        state: AnnotationState,
        messages: list[BaseMessage],
        node_output: dict[str, Any],
    ) -> None:
        """Update the state with new messages and node output.

        Args:
            state: Current workflow state.
            messages: New messages to add to the state.
            node_output: New node output to set in the state.
        """
        all_messages: list[AnyMessage] = add_messages(state["messages"], messages)
        state["messages"] = all_messages
        state["node_output"] = node_output

    def _call_llm_with_prompt(
        self,
        node_name: str,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel] | None = None,
    ) -> AIMessage | BaseModel:
        """Build messages and call the LLM with the appropriate prompts.

        Args:
            node_name: Name of the current node.
            system_prompt: The system prompt to use.
            user_prompt: The user prompt to use.
            schema: Optional Pydantic BaseModel subclass for structured output. If provided, uses llm.with_structured_output().

        Returns:
            The LLM's response message.
        """
        node_llm: BaseChatModel = getattr(self._node_llms, node_name)

        context_identifier: tuple[str, str] = (
            "Node",
            self._assemble_logging_context(node_name=node_name),
        )

        try:
            return call_llm_with_prompt(
                llm=node_llm,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                context_identifier=context_identifier,
                schema=schema if self._enforce_structured_llm_output else None,
                rate_limiting_config=self._rate_limiting_config,
                debug_logging=self._debug_logging,
            )
        except Exception as e:
            raise RuntimeError(f"LLM invocation failed: {e}.") from e

    def _assemble_logging_context(
        self,
        node_name: str,
    ) -> str:
        """Assemble logging and LLM context identifier from node name.

        Args:
            node_name: Name of the current node.

        Returns:
            Context string for logging and LLM context_identifier.
        """
        context_parts: list[str] = [f"Node={node_name}"]
        context_str: str = ", ".join(context_parts)
        return context_str

    @abstractmethod
    def _add_workflow_nodes_and_edges(self, workflow: StateGraph) -> None:
        """Add workflow-specific nodes and edges to the graph.

        Args:
            workflow: The StateGraph to add nodes and edges to.
        """
        ...

    def _build_graph(self) -> CompiledStateGraph:
        """Build the workflow graph.

        This method creates the graph, adds nodes and edges via the abstract method,
        and compiles the graph.

        Returns:
            Compiled workflow graph.
        """
        # Create graph.
        workflow: StateGraph = StateGraph(state_schema=AnnotationState)

        # Add workflow-specific nodes and edges.
        self._add_workflow_nodes_and_edges(workflow=workflow)

        # Compile graph with memory checkpointing.
        return workflow.compile(checkpointer=MemorySaver())

