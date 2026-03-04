"""Statement splitting utilities."""

from __future__ import annotations

from ..errors import ParseError
from ..models import ParseEvent, Statement


def split_statements(text: str) -> list[ParseEvent]:
    """Split SQL dump text into semicolon-terminated statement events.

    This splitter intentionally supports a minimal baseline and is expanded in later steps.
    """

    if "\x00" in text:
        raise ParseError("NUL byte detected in dump text")

    events: list[ParseEvent] = []
    buffer: list[str] = []
    start_line = 1
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not buffer and not stripped:
            continue
        if not buffer:
            start_line = line_number
        buffer.append(raw_line)
        if stripped.endswith(";"):
            statement = Statement(text="\n".join(buffer), line=start_line)
            events.append(ParseEvent(statement=statement))
            buffer.clear()

    if buffer:
        statement = Statement(text="\n".join(buffer), line=start_line)
        events.append(ParseEvent(statement=statement))
    return events
