import os
import uuid
import hashlib
from fastapi import UploadFile
from app.core.config import settings

async def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file to storage and return path."""
    storage_dir = settings.STORAGE_PATH
    os.makedirs(storage_dir, exist_ok=True)

    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(storage_dir, unique_name)

    # Read content and compute hash
    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()

    # Validate size
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise ValueError(f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB")

    # Write to disk
    with open(file_path, "wb") as f:
        f.write(content)

    return file_path

def get_file_path(relative_path: str) -> str:
    """Get absolute file path."""
    return os.path.abspath(relative_path)

def delete_file(file_path: str) -> bool:
    """Delete file from storage."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False