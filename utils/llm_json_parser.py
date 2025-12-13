"""Parser for LLM JSON responses with robust error handling and repair capabilities.

Copied and adapted from: DO_NOT_COMMIT/llm_json_parser.py
Date: 2025-12-13
Modified for hackathon project independence
"""

from __future__ import annotations

import json
import logging
import re
from typing import (
    Any,
)

from langchain_core.exceptions import (
    OutputParserException,
)
from langchain_core.output_parsers import (
    JsonOutputParser,
)

from utils.json_helpers import is_valid_json

logger = logging.getLogger(__name__)


class LLMJsonParser:
    """Parser for LLM JSON responses with robust error handling and repair capabilities.

    This class provides utilities for parsing JSON responses from LLMs, including
    handling malformed JSON, JSONL format, and various formatting wrappers.
    """

    def __init__(self) -> None:
        """Initialize the LLM JSON parser with a JsonOutputParser instance."""
        self._json_output_parser: JsonOutputParser = JsonOutputParser()

    def parse_llm_json_extraction_response(
        self,
        response_content: str,
        fail_fast: bool = False,
        context_identifier: tuple[str, str] = ("Context", "unknown"),
        debug_logging: bool = False,
    ) -> list[dict[str, Any]] | None:
        """Parse LLM JSON extraction response with robust error handling.

        Args:
            response_content: The raw response content from the LLM.
            fail_fast: Whether to fail fast on parsing errors.
            context_identifier: Tuple of (tag, context) for logging.
            debug_logging: Whether to enable debug logging.

        Returns:
            List of parsed dictionaries, or None if parsing fails completely.
        """
        tag: str
        context: str
        tag, context = context_identifier

        # Debug logging: Original response
        if debug_logging:
            logger.debug(
                f"[{tag}] Original response content length: {len(response_content)} chars"
            )
            if len(response_content) > 500:
                logger.debug(
                    f"[{tag}] Original response preview (first 250 + last 250): "
                    f"{response_content[:250]}... [truncated {len(response_content) - 500} chars] ...{response_content[-250:]}"
                )
            else:
                logger.debug(f"[{tag}] Original response content: {response_content}")

        cleaned: str = self._strip_formatting_wrappers(text=response_content)

        # Debug logging: After cleaning
        if debug_logging:
            logger.debug(
                f"[{tag}] After cleaning (removed markdown/prefixes): length={len(cleaned)} chars"
            )
            if len(cleaned) > 500:
                logger.debug(
                    f"[{tag}] Cleaned content preview (first 250 + last 250): "
                    f"{cleaned[:250]}... [truncated {len(cleaned) - 500} chars] ...{cleaned[-250:]}"
                )
            else:
                logger.debug(f"[{tag}] Cleaned content: {cleaned}")

        repaired: str = self._preprocess_and_repair_json_text(text=cleaned)

        # Debug logging: After repair
        if debug_logging:
            is_valid: bool = is_valid_json(json_string=repaired)
            logger.debug(
                f"[{tag}] After repair: length={len(repaired)} chars, "
                f"is_valid_json={is_valid}"
            )
            if len(repaired) > 500:
                logger.debug(
                    f"[{tag}] Repaired content preview (first 250 + last 250): "
                    f"{repaired[:250]}... [truncated {len(repaired) - 500} chars] ...{repaired[-250:]}"
                )
            else:
                logger.debug(f"[{tag}] Repaired content: {repaired}")

        try:
            return self._parse_json_or_jsonl(
                text=repaired, fail_fast=fail_fast, tag=tag, context=context
            )
        except ValueError:
            # Let ValueError propagate for fail_fast behavior.
            raise
        except Exception as e:
            logger.warning(
                f"[{tag}] Failed to parse response in context '{context}': {e}."
            )
            return None

    def _strip_formatting_wrappers(self, text: str) -> str:
        """Remove Markdown fences and think tags from the text.

        Args:
            text: The text to clean.

        Returns:
            The cleaned text without formatting wrappers.
        """
        # Remove Markdown fences (opening and closing, with or without language tag, and any whitespace/newlines).
        text = re.sub(
            pattern=r"(?im)^```(?:json|jsonl)?\s*$",
            repl="",
            string=text,
        )
        text = re.sub(
            pattern=r"(?im)^```\s*$",
            repl="",
            string=text,
        )
        text = re.sub(
            pattern=r"(?im)^```(?:json|jsonl)?[ \t]*\n",
            repl="",
            string=text,
        )
        text = re.sub(
            pattern=r"(?im)^```[ \t]*\n",
            repl="",
            string=text,
        )
        text = re.sub(
            pattern=r"(?im)```[ \t]*$",
            repl="",
            string=text,
        )
        # Remove <think> tags.
        text = re.sub(
            pattern=r"(?i)<think>.*?</think>",
            repl="",
            string=text,
            flags=re.DOTALL,
        )

        # Remove common text prefixes that LLMs sometimes add before JSON.
        # Match patterns like "Response:", "Answer:", "Here is the JSON:", etc. at the start.
        # This handles cases where LLMs add explanatory text before the JSON block.
        text = re.sub(
            pattern=r"(?i)^(?:Response|Answer|Here is the JSON|JSON response|Here's the JSON|The JSON is|Output):\s*\n?",
            repl="",
            string=text,
            flags=re.MULTILINE,
        )

        return text.strip()

    def _preprocess_and_repair_json_text(self, text: str) -> str:
        """Preprocess and repair JSON text by fixing common issues.

        Args:
            text: The JSON text to repair.

        Returns:
            The repaired JSON text.
        """
        # Try parsing the original text first.
        if is_valid_json(json_string=text):
            return text

        # Remove trailing commas first.
        repaired_text: str = self._remove_trailing_commas(text=text)
        if is_valid_json(json_string=repaired_text):
            return repaired_text

        # Repair unescaped quotes next.
        repaired_text = self._repair_unescaped_quotes(text=repaired_text)
        if is_valid_json(json_string=repaired_text):
            return repaired_text

        # Additional repairs for common JSON malformations.
        repaired_text = self._repair_missing_quotes_around_keys(text=repaired_text)
        if is_valid_json(json_string=repaired_text):
            return repaired_text

        repaired_text = self._repair_extra_commas_in_arrays(text=repaired_text)
        if is_valid_json(json_string=repaired_text):
            return repaired_text

        return repaired_text

    def _remove_trailing_commas(self, text: str) -> str:
        """Remove trailing commas from JSON objects and arrays.

        Args:
            text: The JSON text to clean.

        Returns:
            The cleaned JSON text.
        """
        text = re.sub(r",\s*]", "]", text)
        text = re.sub(r",\s*}", "}", text)
        return text

    def _repair_unescaped_quotes(self, text: str) -> str:
        """Repair unescaped quotes in JSON string values.

        Args:
            text: The JSON text to repair.

        Returns:
            The repaired JSON text.
        """
        # This approach attempts to escape unescaped quotes inside string values.
        # It does not attempt to fully parse JSON, but tries to fix common LLM output errors.
        in_string: bool = False
        escaped: bool = False
        result: list[str] = []
        for idx, char in enumerate(text):
            if char == '"' and not escaped:
                if in_string:
                    # Possible end of string, or an unescaped quote inside a string value.
                    # Look ahead: if next non-whitespace is ':' or ',' or '}' or ']', treat as end of string.
                    lookahead: str = text[idx + 1 :].lstrip()[:1]
                    if lookahead in [":", ",", "}", "]", ""]:
                        in_string = False
                        result.append(char)
                    else:
                        # Unescaped quote inside string value, escape it.
                        result.append('\\"')
                else:
                    in_string = True
                    result.append(char)
            else:
                if char == "\\" and not escaped:
                    escaped = True
                    result.append(char)
                    continue
                escaped = False
                result.append(char)
        return "".join(result)

    def _repair_missing_quotes_around_keys(self, text: str) -> str:
        """Repair missing quotes around JSON keys.

        Args:
            text: The JSON text to repair.

        Returns:
            The repaired JSON text.
        """
        # This is a placeholder for more sophisticated key quote repair.
        # For now, return the text as-is to avoid over-engineering.
        return text

    def _repair_extra_commas_in_arrays(self, text: str) -> str:
        """Repair extra commas in JSON arrays.

        Args:
            text: The JSON text to repair.

        Returns:
            The repaired JSON text.
        """
        text = re.sub(r",\s*]", "]", text)
        text = re.sub(r",\s*}", "}", text)
        return text

    def _parse_json_or_jsonl(
        self, text: str, fail_fast: bool, tag: str, context: str
    ) -> list[dict[str, Any]] | None:
        """Parse JSON or JSONL text with fallback strategies.

        Args:
            text: The text to parse.
            fail_fast: Whether to fail fast on parsing errors.
            tag: Tag for logging.
            context: Context for logging.

        Returns:
            List of parsed dictionaries, or None if parsing fails.
        """
        # First, try full JSON block.
        if is_valid_json(json_string=text):
            try:
                logger.debug(
                    f"[{tag}] Attempting full JSON block parse (text length: {len(text)} chars)"
                )
                parsed: (
                    dict[str, Any]
                    | list[dict[str, Any]]
                    | str
                    | int
                    | float
                    | bool
                    | None
                ) = self._json_output_parser.parse(text=text)
                logger.debug(
                    f"[{tag}] Full JSON block parse succeeded, type: {type(parsed).__name__}"
                )
                return self._normalize_output(parsed=parsed, tag=tag, context=context)
            except OutputParserException as e:
                logger.debug(
                    f"[{tag}] Full block JSON parse failed: {e}. Falling back to JSONL parsing."
                )

        # Try JSONL (line-delimited).
        logger.debug(
            f"[{tag}] Attempting JSONL parsing (line-by-line). Text has {len(text.splitlines())} lines"
        )
        return self._parse_jsonl_lines(
            text=text, fail_fast=fail_fast, tag=tag, context=context
        )

    def _normalize_output(
        self,
        parsed: dict[str, Any] | list[dict[str, Any]] | list[Any] | Any,
        tag: str,
        context: str,
    ) -> list[dict[str, Any]]:
        """Normalize parsed output to a list of dictionaries.

        Args:
            parsed: The parsed JSON data.
            tag: Tag for logging.
            context: Context for logging.

        Returns:
            List of dictionaries.
        """
        if isinstance(parsed, list):
            dict_count: int = sum(1 for item in parsed if isinstance(item, dict))
            logger.debug(
                f"[{tag}] Normalizing list output: {len(parsed)} items, {dict_count} dict(s)"
            )
            return [item for item in parsed if isinstance(item, dict)]
        elif isinstance(parsed, dict):
            logger.debug(f"[{tag}] Normalizing dict output: single dict")
            return [parsed]
        else:
            logger.warning(
                f"[{tag}] Unexpected JSON root type '{type(parsed).__name__}' in context '{context}'. Expected list or dict. Content: {repr(parsed)}"
            )
            logger.debug(
                f"[{tag}] Unexpected type in normalize_output: {type(parsed).__name__}, "
                f"content (first 200 chars): {repr(str(parsed)[:200])}"
            )
            return []

    def _parse_jsonl_lines(
        self, text: str, fail_fast: bool, tag: str, context: str
    ) -> list[dict[str, Any]] | None:
        """Parse JSONL text line by line.

        Args:
            text: The text to parse.
            fail_fast: Whether to fail fast on parsing errors.
            tag: Tag for logging.
            context: Context for logging.

        Returns:
            List of parsed dictionaries, or None if parsing fails.
        """
        records: list[dict[str, Any]] = []
        failed_lines: list[int] = []
        lines: list[str] = text.splitlines()
        logger.debug(
            f"[{tag}] JSONL parsing: Processing {len(lines)} lines (non-empty: {sum(1 for line in lines if line.strip())})"
        )
        for idx, raw_line in enumerate(lines):
            stripped_line: str = raw_line.strip()
            if not stripped_line:
                continue
            try:
                parsed_dicts: list[dict[str, Any]] | None = self._parse_jsonl_line(
                    line=stripped_line,
                    idx=idx,
                    fail_fast=fail_fast,
                    tag=tag,
                    context=context,
                )
                if parsed_dicts:
                    records.extend(parsed_dicts)
                    logger.debug(
                        f"[{tag}] JSONL line {idx + 1} parsed successfully: {len(parsed_dicts)} dict(s)"
                    )
                else:
                    failed_lines.append(idx + 1)
                    logger.debug(
                        f"[{tag}] JSONL line {idx + 1} parsed but returned no dicts. Line content (first 100 chars): {stripped_line[:100]}"
                    )
            except Exception as e:
                logger.warning(
                    f"[{tag}] Skipping malformed line {idx + 1} in context '{context}': {e}."
                )
                logger.debug(
                    f"[{tag}] JSONL line {idx + 1} failed. Line content (first 100 chars): {stripped_line[:100]}"
                )
                failed_lines.append(idx + 1)
                if fail_fast:
                    raise ValueError(
                        f"[{tag}] Failed to parse line {idx + 1} in context '{context}': {e}."
                    ) from e
        if records:
            logger.debug(
                f"[{tag}] JSONL parsing succeeded: {len(records)} record(s) from {len(lines)} lines, {len(failed_lines)} failed lines"
            )
            return records
        if fail_fast:
            # Always raise if no records were parsed and fail_fast is True.
            raise ValueError(
                f"[{tag}] Failed to parse any lines in context '{context}'."
            )
        logger.debug(
            f"[{tag}] JSONL parsing failed: No records parsed from {len(lines)} lines, {len(failed_lines)} failed lines"
        )
        return None

    def _parse_jsonl_line(
        self, line: str, idx: int, fail_fast: bool, tag: str, context: str
    ) -> list[dict[str, Any]] | None:
        """Parse a single JSONL line, handling direct and repair attempts.

        Args:
            line: The line to parse.
            idx: The line index.
            fail_fast: Whether to fail fast on parsing errors.
            tag: Tag for logging.
            context: Context for logging.

        Returns:
            List of parsed dictionaries, or None if parsing fails.
        """
        # First, assume the line is not malformed and try to parse it directly.
        if is_valid_json(json_string=line):
            parsed: (
                dict[str, Any] | list[dict[str, Any]] | str | int | float | bool | None
            ) = self._json_output_parser.parse(text=line)
            normalized: list[dict[str, Any]] = self._normalize_output(
                parsed=parsed, tag=tag, context=context
            )
            added: bool = False
            result: list[dict[str, Any]] = []
            for item in normalized:
                if isinstance(item, dict) and item:
                    result.append(item)
                    added = True
            if not added:
                if fail_fast:
                    raise ValueError(
                        f"[{tag}] Failed to parse line {idx + 1} in context '{context}': Empty or invalid dict."
                    )
                return None
            return result
        # If direct parsing failed, try repairs.
        repaired: str = self._preprocess_and_repair_json_text(text=line)
        if not repaired or not is_valid_json(json_string=repaired):
            if fail_fast:
                raise ValueError(
                    f"[{tag}] Failed to parse line {idx + 1} in context '{context}': Invalid JSON after repair."
                )
            return None
        parsed: (
            dict[str, Any] | list[dict[str, Any]] | str | int | float | bool | None
        ) = self._json_output_parser.parse(text=repaired)
        normalized: list[dict[str, Any]] = self._normalize_output(
            parsed=parsed, tag=tag, context=context
        )
        added: bool = False
        result: list[dict[str, Any]] = []
        for item in normalized:
            if isinstance(item, dict) and item:
                result.append(item)
                added = True
        if not added:
            if fail_fast:
                raise ValueError(
                    f"[{tag}] Failed to parse line {idx + 1} in context '{context}': Empty or invalid dict."
                )
            return None
        return result

