"""Statement splitting utilities."""

from __future__ import annotations

from ..errors import ParseError
from ..models import ParseEvent, Statement


def split_statements(text: str) -> list[ParseEvent]:
    """Split SQL dump text into semicolon-terminated statement events.

    Handles quoted strings and comment blocks commonly seen in mysqldump output.
    """

    if "\x00" in text:
        raise ParseError("NUL byte detected in dump text")

    events: list[ParseEvent] = []
    buffer: list[str] = []
    in_single = False
    in_double = False
    in_backtick = False
    in_line_comment = False
    in_block_comment = False
    escaped = False
    statement_start_line = 1
    line = 1

    idx = 0
    while idx < len(text):
        char = text[idx]
        nxt = text[idx + 1] if idx + 1 < len(text) else ""

        if not buffer and not in_line_comment and not in_block_comment and char.isspace():
            if char == "\n":
                line += 1
                statement_start_line = line
            idx += 1
            continue

        if not buffer:
            statement_start_line = line

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
                line += 1
            idx += 1
            continue

        if in_block_comment:
            if char == "*" and nxt == "/":
                in_block_comment = False
                idx += 2
                continue
            if char == "\n":
                line += 1
            idx += 1
            continue

        if not in_single and not in_double and not in_backtick:
            if char == "#":
                in_line_comment = True
                idx += 1
                continue
            if char == "-" and nxt == "-":
                prev = text[idx - 1] if idx > 0 else "\n"
                next_after = text[idx + 2] if idx + 2 < len(text) else ""
                if prev.isspace() and (next_after.isspace() or not next_after):
                    in_line_comment = True
                    idx += 2
                    continue
            if char == "/" and nxt == "*":
                in_block_comment = True
                idx += 2
                continue

        if char == "\\" and (in_single or in_double):
            escaped = not escaped
            buffer.append(char)
            idx += 1
            continue

        if char == "'" and not in_double and not in_backtick and not escaped:
            in_single = not in_single
        elif char == '"' and not in_single and not in_backtick and not escaped:
            in_double = not in_double
        elif char == "`" and not in_single and not in_double:
            in_backtick = not in_backtick

        if escaped and char != "\\":
            escaped = False

        buffer.append(char)

        if char == ";" and not in_single and not in_double and not in_backtick:
            statement_text = "".join(buffer).strip()
            if statement_text:
                dialect = _detect_dialect(statement_text)
                events.append(
                    ParseEvent(
                        statement=Statement(text=statement_text, line=statement_start_line, dialect=dialect)
                    )
                )
            buffer.clear()

        if char == "\n":
            line += 1

        idx += 1

    statement_text = "".join(buffer).strip()
    if statement_text:
        dialect = _detect_dialect(statement_text)
        events.append(
            ParseEvent(statement=Statement(text=statement_text, line=statement_start_line, dialect=dialect))
        )

    return events


def _detect_dialect(statement: str) -> str:
    upper = statement.upper()
    if "`" in statement or "LOCK TABLES" in upper or "ENGINE=" in upper:
        return "mysql"
    if upper.startswith("COPY "):
        return "postgres"
    return "generic"
