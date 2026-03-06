"""Snapshot tests for stable parser and renderer outputs."""

from __future__ import annotations

import json
from pathlib import Path

from docdiff.diff import diff_documents
from docdiff.parsers import parse_html, parse_markdown
from docdiff.renderers import render_text

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def _assert_matches_snapshot(snapshot_name: str, actual_output: str) -> None:
    """Compare a generated output string with a committed snapshot file.

    Args:
        snapshot_name: Snapshot filename under tests/snapshots.
        actual_output: Current output produced by the system under test.
    """
    expected_output = (SNAPSHOT_DIR / snapshot_name).read_text(encoding="utf-8")
    assert actual_output == expected_output


def test_markdown_parser_snapshot_mixed_blocks() -> None:
    """Markdown parsing output should match the committed document snapshot."""
    content = """# Release Plan

This release prepares a stable API surface.
It also improves deterministic behavior.

- Normalize whitespace
- Keep predictable block IDs

| Module | Status |
| ------ | ------ |
| model  | ready  |
| parser | wip    |

Final notes paragraph with extra detail.
"""

    document = parse_markdown(content)
    serialized_document = json.dumps(document.to_dict(), indent=2) + "\n"

    _assert_matches_snapshot("markdown_parser_mixed_blocks.json", serialized_document)


def test_html_parser_snapshot_noise_and_order() -> None:
    """HTML parsing output should match the committed document snapshot."""
    html = """
    <html>
      <head>
        <style>.x { color: red; }</style>
        <script>console.log('ignore');</script>
      </head>
      <body>
        <h1>Release Plan</h1>
        <p>First paragraph for the report.</p>
        <ul>
          <li>Deterministic output</li>
          <li>Parser boundaries</li>
        </ul>
        <table>
          <tr><th>Module</th><th>Status</th></tr>
          <tr><td>html</td><td>ready</td></tr>
        </table>
      </body>
    </html>
    """

    document = parse_html(html)
    serialized_document = json.dumps(document.to_dict(), indent=2) + "\n"

    _assert_matches_snapshot("html_parser_noise_and_order.json", serialized_document)


def test_rendered_diff_snapshot_markdown_flow() -> None:
    """Rendered end-to-end markdown diff should match committed text snapshot."""
    before_markdown = """# Release Summary

Parser status is in progress.

- markdown parser
- html parser
"""
    after_markdown = """# Release Summary

Parser status is ready.

- markdown parser
- html parser
- docx parser
"""

    before_document = parse_markdown(before_markdown)
    after_document = parse_markdown(after_markdown)
    diff_result = diff_documents(before_document, after_document, granularity="block+word")
    rendered_report = render_text(diff_result) + "\n"

    _assert_matches_snapshot("rendered_markdown_flow.txt", rendered_report)
