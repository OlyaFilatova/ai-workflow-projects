"""Sync and async runtime clients built on a shared core."""

from __future__ import annotations

from typing import Any

import httpx

from openapi_to_sdk.runtime.base_client import AuthConfig, BaseClient
from openapi_to_sdk.runtime.errors import TransportError


class SyncClient(BaseClient):
    def __init__(
        self,
        *,
        base_url: str,
        auth: AuthConfig | None = None,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(base_url=base_url, auth=auth, timeout=timeout)
        self._client = http_client or httpx.Client(timeout=timeout)

    def close(self) -> None:
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
    def __init__(
        self,
        *,
        base_url: str,
        auth: AuthConfig | None = None,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(base_url=base_url, auth=auth, timeout=timeout)
        self._client = http_client or httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
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
