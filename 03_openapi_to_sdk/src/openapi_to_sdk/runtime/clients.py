"""Sync and async runtime clients built on a shared core."""

from __future__ import annotations

from typing import Any

import httpx

from openapi_to_sdk.runtime.base_client import AuthConfig, BaseClient
from openapi_to_sdk.runtime.errors import TransportError


class SyncClient(BaseClient):
    """Synchronous runtime HTTP client."""

    def __init__(
        self,
        *,
        base_url: str,
        auth: AuthConfig | None = None,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Initialize a synchronous client instance.

        Args:
            base_url: Base URL used for all requests.
            auth: Optional default authentication configuration.
            timeout: Request timeout in seconds.
            http_client: Optional preconfigured `httpx.Client`.
        """
        super().__init__(base_url=base_url, auth=auth, timeout=timeout)
        self._client = http_client or httpx.Client(timeout=timeout)

    def close(self) -> None:
        """Close the underlying synchronous HTTP client."""
        self._client.close()

    def request(
        self,
        *,
        method: str,
        path: str,
        path_params: dict[str, str] | None = None,
        query: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        json_body: object | None = None,
        bearer_token: str | None = None,
        api_key: str | None = None,
        response_model: type[Any] | None = None,
        error_model: type[Any] | None = None,
    ) -> Any:
        """Execute one synchronous API request.

        Args:
            method: HTTP method name.
            path: Path template relative to the base URL.
            path_params: Optional path parameter values.
            query: Optional query parameter values.
            headers: Optional caller-provided headers.
            json_body: Optional JSON payload object.
            bearer_token: Optional per-request bearer token override.
            api_key: Optional per-request API key override.
            response_model: Optional model type for successful payload parsing.
            error_model: Optional model type for error payload parsing.
        """
        kwargs = self._build_request_kwargs(
            path=path,
            path_params=path_params,
            query=query,
            headers=headers,
            json_body=json_body,
            bearer_token=bearer_token,
            api_key=api_key,
        )

        try:
            response = self._client.request(method=method, **kwargs)
        except httpx.HTTPError as exc:
            raise TransportError(str(exc)) from exc

        return self._handle_response(response, response_model, error_model)


class AsyncClient(BaseClient):
    """Asynchronous runtime HTTP client."""

    def __init__(
        self,
        *,
        base_url: str,
        auth: AuthConfig | None = None,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize an asynchronous client instance.

        Args:
            base_url: Base URL used for all requests.
            auth: Optional default authentication configuration.
            timeout: Request timeout in seconds.
            http_client: Optional preconfigured `httpx.AsyncClient`.
        """
        super().__init__(base_url=base_url, auth=auth, timeout=timeout)
        self._client = http_client or httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        """Close the underlying asynchronous HTTP client."""
        await self._client.aclose()

    async def request(
        self,
        *,
        method: str,
        path: str,
        path_params: dict[str, str] | None = None,
        query: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        json_body: object | None = None,
        bearer_token: str | None = None,
        api_key: str | None = None,
        response_model: type[Any] | None = None,
        error_model: type[Any] | None = None,
    ) -> Any:
        """Execute one asynchronous API request.

        Args:
            method: HTTP method name.
            path: Path template relative to the base URL.
            path_params: Optional path parameter values.
            query: Optional query parameter values.
            headers: Optional caller-provided headers.
            json_body: Optional JSON payload object.
            bearer_token: Optional per-request bearer token override.
            api_key: Optional per-request API key override.
            response_model: Optional model type for successful payload parsing.
            error_model: Optional model type for error payload parsing.
        """
        kwargs = self._build_request_kwargs(
            path=path,
            path_params=path_params,
            query=query,
            headers=headers,
            json_body=json_body,
            bearer_token=bearer_token,
            api_key=api_key,
        )

        try:
            response = await self._client.request(method=method, **kwargs)
        except httpx.HTTPError as exc:
            raise TransportError(str(exc)) from exc

        return self._handle_response(response, response_model, error_model)
