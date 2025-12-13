"""LLM helper utilities copied from conversation_analysis/ai_aided_annotations/util.py.

Copied from: platform/conversation_analysis/conversation_analysis/ai_aided_annotations/util.py
Date: 2025-12-13
Modified for hackathon project independence
"""
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from pydantic import BaseModel

    from coding_agent.base import RateLimitingConfig  # noqa: TCH001

logger = logging.getLogger(__name__)


def call_llm_with_prompt(
    llm: BaseChatModel,
    system_prompt: str,
    user_prompt: str,
    context_identifier: tuple[str, str],
    schema: type[BaseModel] | None = None,
    rate_limiting_config: RateLimitingConfig | None = None,
    debug_logging: bool = False,
) -> AIMessage | BaseModel:
    """Build messages and call the LLM with the appropriate prompts.

    This is a generic utility function that can be used by different workflows
    to call LLMs with consistent logging and optional rate limiting.

    Args:
        llm: The language model to use for processing.
        system_prompt: The system prompt to use.
        user_prompt: The user prompt to use.
        context_identifier: A tuple of (key, value) for logging context (e.g., ("Node", "reason")).
        schema: Optional Pydantic BaseModel subclass for structured output. If provided, uses llm.with_structured_output().
        rate_limiting_config: RateLimitingConfig for LLM call delays and sleep behavior.
        debug_logging: Whether to log LLM inputs and outputs.

    Returns:
        The LLM's response message.
    """
    context_key, context_value = context_identifier

    # Use standard logger (Prefect integration removed for hackathon independence)
    _logger = logger

    if debug_logging:
        _logger.debug(
            f"\n{'=' * 80}\n"
            f"[{context_key}={context_value}] LLM Input:\n"
            f"{'-' * 40}\n"
            f"System Prompt:\n{system_prompt}\n"
            f"{'-' * 40}\n"
            f"User Prompt:\n{user_prompt}\n"
            f"{'=' * 80}"
        )

    messages: list[BaseMessage] = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    # Use structured output if schema is provided, otherwise use regular LLM.
    if schema is not None:
        response: AIMessage = llm.with_structured_output(
            schema=schema, method="json_mode"
        ).invoke(input=messages)
    else:
        response: AIMessage = llm.invoke(input=messages)

    if debug_logging:
        # Handle different response types for logging.
        response_content: str
        if hasattr(response, "content"):
            # Regular AIMessage response.
            response_content = response.content
        else:
            # Pydantic object response from structured output.
            response_content = str(response)

        _logger.debug(
            f"\n{'=' * 80}\n"
            f"[{context_key}={context_value}] LLM Output:\n"
            f"{'-' * 40}\n"
            f"Response:\n{response_content}\n"
            f"{'=' * 80}"
        )

    if rate_limiting_config and rate_limiting_config.should_sleep():
        sleeping_time: float = rate_limiting_config.get_sleep_duration()

        if debug_logging:
            _logger.info(
                f"[{context_key}={context_value}] Sleeping for {sleeping_time:.2f} seconds before next LLM call."
            )

        time.sleep(sleeping_time)

    return response

