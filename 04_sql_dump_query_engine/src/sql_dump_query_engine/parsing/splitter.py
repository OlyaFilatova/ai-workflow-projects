"""Statement splitting stubs."""

from __future__ import annotations

from ..models import Statement


def split_statements(text: str) -> list[Statement]:
    """Split SQL dump text into statements.

    Current scaffold implementation returns semicolon-terminated blocks.
    """

    statements: list[Statement] = []
    buffer: list[str] = []
    line = 1
    start_line = 1
    for raw_line in text.splitlines():
        if not buffer:
            start_line = line
        buffer.append(raw_line)
        if raw_line.rstrip().endswith(";"):
            statements.append(Statement(text="\n".join(buffer), line=start_line))
            buffer.clear()
        line += 1
    if buffer:
        statements.append(Statement(text="\n".join(buffer), line=start_line))
    return statements
