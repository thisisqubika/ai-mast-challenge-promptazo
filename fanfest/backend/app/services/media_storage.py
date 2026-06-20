"""Local filesystem media storage backend."""

import os
import uuid
from pathlib import Path

MEDIA_ROOT = Path("media")

ALLOWED_MIME_TYPES: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "video/mp4": "mp4",
    "video/quicktime": "mov",
}


def is_allowed(content_type: str) -> bool:
    return content_type in ALLOWED_MIME_TYPES


def media_type_for(content_type: str) -> str:
    return "video" if content_type.startswith("video/") else "photo"


def save_file(event_id: str, content_type: str, file_bytes: bytes) -> tuple[str, str]:
    """Write bytes to disk. Returns (filename, url_path)."""
    ext = ALLOWED_MIME_TYPES[content_type]
    filename = f"{uuid.uuid4()}.{ext}"
    dest = MEDIA_ROOT / event_id / filename
    os.makedirs(dest.parent, exist_ok=True)
    dest.write_bytes(file_bytes)
    return filename, f"/media/{event_id}/{filename}"
