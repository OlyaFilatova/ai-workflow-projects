"""Shared helpers for OpenAPI-to-IR mapping."""

from __future__ import annotations

import keyword
import re
from dataclasses import dataclass
from typing import Any


class UnsupportedSchemaError(ValueError):
    """Raised when schema features are outside the supported MVP subset."""


@dataclass(slots=True)
class MappingContext:
    openapi_version: str
    schema_name_map: dict[str, str]


class NameRegistry:
    def __init__(self) -> None:
        self._used: set[str] = set()

    def unique(self, base: str) -> str:
        clean = base or "item"
        if clean not in self._used:
            self._used.add(clean)
            return clean

        index = 2
        while True:
            candidate = f"{clean}_{index}"
            if candidate not in self._used:
                self._used.add(candidate)
                return candidate
            index += 1


def to_snake_case(raw: str) -> str:
    base = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_")
    if not base:
        return "item"
    base = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", base)
    snake = base.lower()
    if snake[0].isdigit():
        snake = f"n_{snake}"
    if keyword.iskeyword(snake):
        snake = f"{snake}_"
    return snake


def to_pascal_case(raw: str) -> str:
    tokens = [token for token in re.split(r"[^A-Za-z0-9]+", raw) if token]
    if not tokens:
        return "Model"
    pascal = "".join(token[:1].upper() + token[1:] for token in tokens)
    if pascal[0].isdigit():
        return f"Model{pascal}"
    return pascal


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
