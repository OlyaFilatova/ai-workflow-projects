"""SQL INSERT batching helpers for loading."""

from __future__ import annotations

import re

_INSERT_VALUES_RE = re.compile(
    r"^(INSERT\s+INTO\s+.+?\s+VALUES\s*)(.+?)(;?)$",
    re.IGNORECASE | re.DOTALL,
)


def batch_insert_statement(sql: str, batch_size: int) -> list[str]:
    match = _INSERT_VALUES_RE.match(sql.strip())
    if not match:
        return [sql]

    prefix, values_blob, trailing_semicolon = match.groups()
    tuples = _split_tuples(values_blob)
    if len(tuples) <= batch_size:
        has_semicolon = bool(trailing_semicolon) or sql.rstrip().endswith(";")
        return [f"{prefix}{values_blob}{'' if has_semicolon else ';'}"]

    batched: list[str] = []
    for idx in range(0, len(tuples), batch_size):
        chunk = tuples[idx : idx + batch_size]
        batched.append(f"{prefix}{', '.join(chunk)};")
    return batched


def _split_tuples(values_blob: str) -> list[str]:
    tuples: list[str] = []
    start = 0
    depth = 0
    in_single = False
    in_double = False
    escaped = False

    for idx, char in enumerate(values_blob):
        if char == "\\" and (in_single or in_double):
            escaped = not escaped
            continue

        if char == "'" and not in_double and not escaped:
            in_single = not in_single
        elif char == '"' and not in_single and not escaped:
            in_double = not in_double
        elif not in_single and not in_double:
            if char == "(":
                if depth == 0:
                    start = idx
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    tuples.append(values_blob[start : idx + 1].strip())
        if escaped and char != "\\":
            escaped = False

    return tuples
