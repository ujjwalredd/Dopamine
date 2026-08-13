import json
from pathlib import Path


def save_json(path: str | Path, value: object) -> None:
    with Path(path).open("w", encoding="utf-8") as stream:
        json.dump(value, stream)
