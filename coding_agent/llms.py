"""LLM configuration models copied from conversation_analysis/ai_aided_annotations/tasks/llms.py.

Copied from: platform/conversation_analysis/conversation_analysis/ai_aided_annotations/tasks/llms.py
Date: 2025-12-13
Modified for hackathon project independence
"""
from __future__ import annotations

from langchain_core.language_models import BaseChatModel  # noqa: TC002
from pydantic import BaseModel


class NodeLLMs(BaseModel):
    """A mapping of node names to their LLMs."""

    reason: BaseChatModel | None = None
    plan: BaseChatModel | None = None
    act: BaseChatModel | None = None
    validate: BaseChatModel | None = None

