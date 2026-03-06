from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import cast

import httpx
import pytest

from openapi_to_sdk.runtime.base_client import AuthConfig
from openapi_to_sdk.runtime.clients import AsyncClient, SyncClient
from openapi_to_sdk.runtime.errors import BadRequestError, NotFoundError


@dataclass(slots=True)
class ParsedModel:
    """Represent ParsedModel.

    Attributes:
        name: Attribute value.
    """
    name: str

    @classmethod
    def model_validate(cls, payload: dict[str, str]) -> ParsedModel:
        """Run model validate.

        Args:
            cls: Argument value.
            payload: Argument value.
        """
        return cls(name=payload["name"])


@dataclass(slots=True)
class ParsedError:
    """Represent ParsedError.

    Attributes:
        code: Attribute value.
    """
    code: str

    @classmethod
    def model_validate(cls, payload: dict[str, str]) -> ParsedError:
        """Run model validate.

        Args:
            cls: Argument value.
            payload: Argument value.
        """
        return cls(code=payload["code"])


def test_sync_request_construction_and_auth_injection() -> None:
    """Test sync request construction and auth injection."""
    captured_url = ""
    captured_headers: dict[str, str] = {}
    captured_body = ""

    def handler(request: httpx.Request) -> httpx.Response:
        """Run handler.

        Args:
            request: Argument value.
        """
        nonlocal captured_url, captured_headers, captured_body
        captured_url = str(request.url)
        captured_headers = dict(request.headers)
        captured_body = request.content.decode("utf-8")
        return httpx.Response(200, json={"name": "example"})

    transport = httpx.MockTransport(handler)
    auth = AuthConfig(api_key="default-key", api_key_name="X-API-Key", bearer_token="default-token")
    sync_client = SyncClient(
        base_url="https://api.example.com",
        auth=auth,
        http_client=httpx.Client(transport=transport),
    )

    model = sync_client.request(
        method="GET",
        path="/pets/{pet_id}",
        path_params={"pet_id": "a/b"},
        query={"limit": 10, "cursor": None},
        headers={"X-Test": "1"},
        response_model=ParsedModel,
    )

    assert isinstance(model, ParsedModel)
    assert model.name == "example"
    assert captured_url == "https://api.example.com/pets/a%2Fb?limit=10"
    assert captured_headers["authorization"] == "Bearer default-token"
    assert captured_headers["x-api-key"] == "default-key"
    assert isinstance(captured_body, str)


def test_sync_auth_override_beats_default() -> None:
    """Test sync auth override beats default."""
    captured_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        """Run handler.

        Args:
            request: Argument value.
        """
        nonlocal captured_headers
        captured_headers = dict(request.headers)
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(handler)
    auth = AuthConfig(api_key="default-key", bearer_token="default-token")
    sync_client = SyncClient(
        base_url="https://api.example.com",
        auth=auth,
        http_client=httpx.Client(transport=transport),
    )

    sync_client.request(
        method="GET",
        path="/ping",
        bearer_token="override-token",
        api_key="override-key",
    )

    assert captured_headers["authorization"] == "Bearer override-token"
    assert captured_headers["x-api-key"] == "override-key"


def test_response_parsing_and_204_handling() -> None:
    """Test response parsing and 204 handling."""
    def handler(request: httpx.Request) -> httpx.Response:
        """Run handler.

        Args:
            request: Argument value.
        """
        if request.url.path.endswith("/one"):
            return httpx.Response(200, json={"name": "one"})
        return httpx.Response(204)

    transport = httpx.MockTransport(handler)
    sync_client = SyncClient(base_url="https://api.example.com", http_client=httpx.Client(transport=transport))

    parsed = sync_client.request(method="GET", path="/one", response_model=ParsedModel)
    empty = sync_client.request(method="GET", path="/two")

    assert isinstance(parsed, ParsedModel)
    assert parsed.name == "one"
    assert empty is None


def test_error_mapping_and_parsed_error_payload() -> None:
    """Test error mapping and parsed error payload."""
    def handler(request: httpx.Request) -> httpx.Response:
        """Run handler.

        Args:
            request: Argument value.
        """
        if request.url.path.endswith("/missing"):
            return httpx.Response(404, json={"code": "not_found"})
        return httpx.Response(400, json={"code": "bad_request"})

    transport = httpx.MockTransport(handler)
    sync_client = SyncClient(base_url="https://api.example.com", http_client=httpx.Client(transport=transport))

    with pytest.raises(NotFoundError) as not_found:
        sync_client.request(
            method="GET",
            path="/missing",
            error_model=ParsedError,
        )

    assert not_found.value.status_code == 404
    assert isinstance(not_found.value.parsed_error, ParsedError)
    assert not_found.value.parsed_error.code == "not_found"

    with pytest.raises(BadRequestError):
        sync_client.request(method="GET", path="/bad")


def test_async_request_construction_and_response_parse() -> None:
    """Test async request construction and response parse."""
    captured_url = ""

    async def run() -> ParsedModel:
        """Run run."""
        def handler(request: httpx.Request) -> httpx.Response:
            """Run handler.

            Args:
                request: Argument value.
            """
            nonlocal captured_url
            captured_url = str(request.url)
            return httpx.Response(200, json={"name": "async"})

        transport = httpx.MockTransport(handler)
        async_client = AsyncClient(
            base_url="https://api.example.com",
            http_client=httpx.AsyncClient(transport=transport),
        )

        try:
            raw_result = await async_client.request(
                method="GET",
                path="/items/{item_id}",
                path_params={"item_id": "hello world"},
                response_model=ParsedModel,
            )
            return cast(ParsedModel, raw_result)
        finally:
            await async_client.aclose()

    result = asyncio.run(run())
    assert isinstance(result, ParsedModel)
    assert captured_url == "https://api.example.com/items/hello%20world"
