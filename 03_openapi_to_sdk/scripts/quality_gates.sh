#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

python3 -m py_compile $(find src tests -name '*.py' | tr '\n' ' ')
python3 -m ruff check .
python3 -m mypy .
python3 -m pytest
