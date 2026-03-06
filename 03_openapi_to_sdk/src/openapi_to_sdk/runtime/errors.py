"""Runtime error types shared by generated clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ApiError(Exception):
    """Base exception for non-success API responses.

    Attributes:
        message: Human-readable error message.
        status_code: HTTP response status code.
        headers: Response headers from the failed request.
        body: Raw response body text.
        parsed_error: Parsed structured payload when available.
    """

    message: str
    status_code: int
    headers: dict[str, str]
    body: str
    parsed_error: Any | None = None

    def __str__(self) -> str:
        return f"{self.status_code}: {self.message}"


class BadRequestError(ApiError):
    """Raised for HTTP 400 responses."""
    pass


class UnauthorizedError(ApiError):
    """Raised for HTTP 401 responses."""
    pass


class ForbiddenError(ApiError):
    """Raised for HTTP 403 responses."""
    pass


class NotFoundError(ApiError):
    """Raised for HTTP 404 responses."""
    pass


class ClientError(ApiError):
    """Raised for HTTP 4xx responses not covered by specific subclasses."""
    pass


class ServerError(ApiError):
    """Raised for HTTP 5xx responses."""
    pass


class TransportError(Exception):
    """Raised when the underlying HTTP transport fails."""


def status_to_error(status_code: int) -> type[ApiError]:
    """Map an HTTP status code to a concrete runtime error type.

    Args:
        status_code: HTTP response status code.
    """
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
