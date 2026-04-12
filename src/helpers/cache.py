import json
import os
from typing import Callable


def cached(file_path: str, compute_fn: Callable[[], list[dict]]) -> list[dict]:
    if os.path.exists(file_path):
        print(f"Loading from cache: {file_path}...")
        return _load_jsonl(file_path)
    print(f"Computing and caching to {file_path}...")
    result = compute_fn()
    _save_as_jsonl(result, file_path)
    return result


def _save_as_jsonl(data: list[dict], file_path: str):
    with open(file_path, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")


def _load_jsonl(file_path: str) -> list[dict]:
    with open(file_path, "r") as f:
        return [json.loads(line) for line in f]
