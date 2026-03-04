"""Shared sync/async HTTP client logic."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

from openapi_to_sdk.runtime.errors import (
    ApiError,
    BadRequestError,
    ClientError,
    ForbiddenError,
    NotFoundError,
    ServerError,
    UnauthorizedError,
)


@dataclass(slots=True)
class AuthConfig:
    api_key: str | None = None
    api_key_name: str = "X-API-Key"
    api_key_in: str = "header"
    bearer_token: str | None = None


class BaseClient:
    """Common request construction and response parsing behavior."""

    def __init__(
        self,
        *,
        base_url: str,
        auth: AuthConfig | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = auth or AuthConfig()
        self.timeout = timeout

    def _build_url(self, path: str, path_params: dict[str, str] | None = None) -> str:
        resolved = path
        for key, value in sorted((path_params or {}).items()):
            resolved = resolved.replace("{" + key + "}", quote(str(value), safe=""))
        return f"{self.base_url}{resolved}"

    def _build_query(self, query: dict[str, object] | None) -> dict[str, object]:
        if not query:
            return {}
        return {key: value for key, value in sorted(query.items()) if value is not None}

    def _build_headers(
        self,
        headers: dict[str, str] | None,
        *,
        bearer_token: str | None,
        api_key: str | None,
    ) -> dict[str, str]:
        built: dict[str, str] = {}
        if headers:
            built.update(headers)

        selected_bearer = bearer_token if bearer_token is not None else self.auth.bearer_token
        if selected_bearer:
            built["Authorization"] = f"Bearer {selected_bearer}"

        selected_api_key = api_key if api_key is not None else self.auth.api_key
        if selected_api_key and self.auth.api_key_in == "header":
            built[self.auth.api_key_name] = selected_api_key

        return dict(sorted(built.items()))

    def _build_request_kwargs(
        self,
        *,
        path: str,
        path_params: dict[str, str] | None,
        query: dict[str, object] | None,
        headers: dict[str, str] | None,
        json_body: object | None,
        bearer_token: str | None,
        api_key: str | None,
    ) -> dict[str, Any]:
        return {
            "url": self._build_url(path, path_params),
            "params": self._build_query(query),
            "headers": self._build_headers(headers, bearer_token=bearer_token, api_key=api_key),
            "json": json_body,
        }

    def _parse_success_response(self, response: httpx.Response, response_model: type[Any] | None) -> Any:
        if response.status_code == 204 or not response.content:
            return None

        if response_model is None:
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return response.json()
            return response.text

        payload = response.json()
        if hasattr(response_model, "model_validate"):
            return response_model.model_validate(payload)
        return response_model(payload)

    def _raise_for_error(
        self,
        response: httpx.Response,
        error_model: type[Any] | None = None,
    ) -> None:
        parsed_error: Any | None = None
        content_type = response.headers.get("content-type", "")
        body_text = response.text

        if "application/json" in content_type and body_text:
            try:
                json_body = response.json()
                parsed_error = (
                    error_model.model_validate(json_body)
                    if error_model is not None and hasattr(error_model, "model_validate")
                    else json_body
                )
            except (json.JSONDecodeError, ValueError):
                parsed_error = None

        exc_cls = _status_to_error(response.status_code)
        raise exc_cls(
            message=f"HTTP request failed with status {response.status_code}",
            status_code=response.status_code,
            headers=dict(response.headers.items()),
            body=body_text,
            parsed_error=parsed_error,
        )


def _status_to_error(status_code: int) -> type[ApiError]:
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
