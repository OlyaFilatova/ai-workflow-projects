"""Shared SQL definition parsing helpers."""

from __future__ import annotations


def split_definitions(body: str) -> list[str]:
    """Split a CREATE TABLE body on top-level commas.

    Args:
        body: SQL text inside ``CREATE TABLE (...)``.
    """

    parts: list[str] = []
    start = 0
    depth = 0
    in_single = False
    in_double = False
    for idx, char in enumerate(body):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif not in_single and not in_double:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == "," and depth == 0:
                parts.append(body[start:idx])
                start = idx + 1
    parts.append(body[start:])
    return parts
