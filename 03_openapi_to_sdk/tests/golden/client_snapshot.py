from __future__ import annotations

from typing import Any

from openapi_to_sdk.runtime.clients import AsyncClient as RuntimeAsyncClient
from openapi_to_sdk.runtime.clients import SyncClient as RuntimeSyncClient

from .models import *


class Client(RuntimeSyncClient):
    pass


class AsyncClient(RuntimeAsyncClient):
    pass
