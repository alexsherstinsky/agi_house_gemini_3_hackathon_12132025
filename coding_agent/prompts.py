"""Prompt configuration models copied from conversation_analysis/ai_aided_annotations/tasks/prompts.py.

Copied from: platform/conversation_analysis/conversation_analysis/ai_aided_annotations/tasks/prompts.py
Date: 2025-12-13
Modified for hackathon project independence
"""
from __future__ import annotations

from pydantic import BaseModel


class SystemAndUserPromptPair(BaseModel):
    """A pair of system and user prompts for a node."""

    system_prompt: str
    user_prompt: str


class NodePrompts(BaseModel):
    """A mapping of node names to their prompt pairs."""

    reason: SystemAndUserPromptPair | None = None
    plan: SystemAndUserPromptPair | None = None
    act: SystemAndUserPromptPair | None = None
    validate: SystemAndUserPromptPair | None = None

