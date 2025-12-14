"""Time parser module for self-healing time expression parsing."""

from time_parser.parser import TimeParser
from time_parser.wrapper import intercept_parser_errors

__all__ = ["TimeParser", "intercept_parser_errors"]
