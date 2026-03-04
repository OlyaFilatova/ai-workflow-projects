"""Input format parsers that convert sources to NDM."""

from .docx_parser import parse_docx_file
from .html_parser import parse_html, parse_html_file
from .markdown_parser import parse_markdown, parse_markdown_file

__all__ = [
    "parse_docx_file",
    "parse_html",
    "parse_html_file",
    "parse_markdown",
    "parse_markdown_file",
]
