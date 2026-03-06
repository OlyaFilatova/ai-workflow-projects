"""Runtime error types shared by generated clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ApiError(Exception):
    """Base exception for non-success API responses."""

    message: str
    status_code: int
    headers: dict[str, str]
    body: str
    parsed_error: Any | None = None

    def __str__(self) -> str:
        return f"{self.status_code}: {self.message}"


class BadRequestError(ApiError):
    pass


class UnauthorizedError(ApiError):
    pass


class ForbiddenError(ApiError):
    pass


class NotFoundError(ApiError):
    pass


class ClientError(ApiError):
    pass


class ServerError(ApiError):
    pass


class TransportError(Exception):
    """Raised when the underlying HTTP transport fails."""


def status_to_error(status_code: int) -> type[ApiError]:
    """Map HTTP status codes to concrete API error types."""
    if status_code == 400:
        return BadRequestError
    if status_code == 401:
        return UnauthorizedError
    if status_code == 403:
        return ForbiddenError
    if status_code == 404:
        return NotFoundError
    if 400 <= status_code < 500:
        return ClientError
    if status_code >= 500:
        return ServerError
    return ApiError
