"""A small disk cache for LLM results, so re-running the tests during development is free.

Each result is saved as a JSON file in .cache/<namespace>/<hash>.json. The hash is built from
everything that affects the result (question, model, temperature, prompt text...), so changing
any of those automatically means a cache miss and a fresh call.

Bypass it with `pytest --no-llm-cache` or by setting RAG_EVAL_NO_CACHE=1.
"""

import hashlib
import json
import os
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from src.config import ROOT

CACHE_DIR = ROOT / ".cache"
T = TypeVar("T", bound=BaseModel)

# Results already produced in this process. Always used, even with the disk cache off, so that
# within one test run the faithfulness and correctness tests grade the very same answer.
_memory: dict[str, BaseModel] = {}


def cache_enabled() -> bool:
    return os.environ.get("RAG_EVAL_NO_CACHE") != "1"


def cache_key(data: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


def cached(namespace: str, key_data: dict[str, Any], model: type[T], compute: Callable[[], T]) -> T:
    """Return the saved result for key_data if there is one, otherwise compute and save it."""
    key = f"{namespace}/{cache_key(key_data)}"
    path = CACHE_DIR / f"{key}.json"
    if key not in _memory:
        if cache_enabled() and path.exists():
            _memory[key] = model.model_validate_json(path.read_text())
        else:
            _memory[key] = compute()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(_memory[key].model_dump_json(indent=2))  # also with --no-llm-cache, to refresh it
    return _memory[key]
