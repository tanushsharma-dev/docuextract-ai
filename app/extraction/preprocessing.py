from __future__ import annotations

from pathlib import Path


def normalize_document_path(file_path: str | Path) -> str:
    return str(Path(file_path).resolve())


def preprocess_bytes(data: bytes) -> bytes:
    return data.strip()
