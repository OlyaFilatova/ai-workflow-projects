from __future__ import annotations

import time

from openapi_to_sdk.ir import build_api_ir


def test_build_api_ir_performance_smoke() -> None:
    paths: dict[str, object] = {}
    for idx in range(250):
        paths[f"/items/{idx}"] = {
            "get": {
                "operationId": f"getItem{idx}",
                "responses": {
                    "200": {
                        "description": "ok",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "properties": {"id": {"type": "integer"}}}
                            }
                        },
                    }
                },
            }
        }

    doc = {
        "openapi": "3.1.0",
        "info": {"title": "Perf", "version": "1.0.0"},
        "paths": paths,
    }

    start = time.perf_counter()
    ir = build_api_ir(doc)
    duration = time.perf_counter() - start

    assert len(ir.operations) == 250
    assert duration < 3.0
