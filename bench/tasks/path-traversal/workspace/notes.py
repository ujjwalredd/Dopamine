from pathlib import Path


def read_note(base: str | Path, name: str) -> str:
    return (Path(base) / name).read_text(encoding="utf-8")
