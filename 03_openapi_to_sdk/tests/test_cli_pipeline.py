from __future__ import annotations

import json
from pathlib import Path

from openapi_to_sdk.cli.main import main


def _write_spec(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "Pet API", "version": "1.0.0"},
                "paths": {
                    "/pets/{pet_id}": {
                        "get": {
                            "operationId": "getPet",
                            "parameters": [
                                {
                                    "name": "pet_id",
                                    "in": "path",
                                    "required": True,
                                    "schema": {"type": "string"},
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "ok",
                                    "content": {
                                        "application/json": {
                                            "schema": {"$ref": "#/components/schemas/Pet"}
                                        }
                                    },
                                }
                            },
                        }
                    }
                },
                "components": {
                    "schemas": {
                        "Pet": {
                            "type": "object",
                            "required": ["id"],
                            "properties": {
                                "id": {"type": "string"},
                            },
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def _read_tree(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for item in sorted(root.rglob("*")):
        if item.is_file():
            files[str(item.relative_to(root))] = item.read_text(encoding="utf-8")
    return files


def test_cli_generate_smoke(tmp_path: Path, capsys) -> None:
    spec = tmp_path / "spec.json"
    out = tmp_path / "out"
    _write_spec(spec)

    exit_code = main(["generate", "--spec", str(spec), "--output", str(out)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Generated SDK into:" in captured.out
    assert (out / "pet_api" / "models.py").exists()
    assert (out / "pet_api" / "client.py").exists()


def test_cli_reports_invalid_spec(tmp_path: Path, capsys) -> None:
    out = tmp_path / "out"

    exit_code = main(["generate", "--spec", str(tmp_path / "missing.json"), "--output", str(out)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "error:" in captured.err


def test_cli_overwrite_behavior(tmp_path: Path, capsys) -> None:
    spec = tmp_path / "spec.json"
    out = tmp_path / "out"
    _write_spec(spec)

    first_exit = main(["generate", "--spec", str(spec), "--output", str(out)])
    assert first_exit == 0

    second_exit = main(["generate", "--spec", str(spec), "--output", str(out)])
    second = capsys.readouterr()
    assert second_exit == 1
    assert "--overwrite" in second.err

    third_exit = main(["generate", "--spec", str(spec), "--output", str(out), "--overwrite"])
    assert third_exit == 0


def test_cli_supports_config_file(tmp_path: Path, capsys) -> None:
    spec = tmp_path / "spec.json"
    out = tmp_path / "out"
    config = tmp_path / "config.json"
    _write_spec(spec)
    config.write_text(
        json.dumps({"spec": str(spec), "output": str(out), "overwrite": True}),
        encoding="utf-8",
    )

    exit_code = main(["generate", "--config", str(config)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Generated SDK into:" in captured.out


def test_generation_is_idempotent(tmp_path: Path) -> None:
    spec = tmp_path / "spec.json"
    out_a = tmp_path / "out_a"
    out_b = tmp_path / "out_b"
    _write_spec(spec)

    assert main(["generate", "--spec", str(spec), "--output", str(out_a)]) == 0
    assert main(["generate", "--spec", str(spec), "--output", str(out_b)]) == 0

    assert _read_tree(out_a) == _read_tree(out_b)
