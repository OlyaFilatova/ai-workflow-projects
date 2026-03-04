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
