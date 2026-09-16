from __future__ import annotations

from pathlib import Path

from app.core.config import settings


def ensure_storage_directories() -> None:
    for directory in (settings.upload_dir, settings.processed_dir):
        Path(directory).mkdir(parents=True, exist_ok=True)


def save_upload(file_bytes: bytes, filename: str) -> str:
    ensure_storage_directories()
    destination = Path(settings.upload_dir) / filename
    destination.write_bytes(file_bytes)
    return str(destination)


def move_to_processed(filename: str) -> str:
    source = Path(settings.upload_dir) / filename
    destination = Path(settings.processed_dir) / filename
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
        source.unlink(missing_ok=True)
    return str(destination)
