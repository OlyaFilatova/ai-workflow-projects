"""Input format parsers that convert sources to NDM."""

from .markdown_parser import parse_markdown, parse_markdown_file

__all__ = ["parse_markdown", "parse_markdown_file"]
