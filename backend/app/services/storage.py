from __future__ import annotations

import hashlib
import os
import uuid

from app.core.config import settings

# Only these content types are accepted. Anything else is rejected before storage.
ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/tiff": ".tiff",
    "image/webp": ".webp",
}

# Magic-byte signatures used to confirm the declared content type matches the bytes.
_SIGNATURES: dict[str, list[bytes]] = {
    "application/pdf": [b"%PDF-"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/jpg": [b"\xff\xd8\xff"],
    "image/tiff": [b"II*\x00", b"MM\x00*"],
    "image/webp": [b"RIFF"],
}


class UploadValidationError(Exception):
    """Raised when an uploaded file fails validation."""


def validate_and_fingerprint(content: bytes, content_type: str) -> str:
    """Validate size, type, and magic bytes; return the sha256 hex digest."""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise UploadValidationError(f"Unsupported file type: {content_type}")

    if len(content) == 0:
        raise UploadValidationError("Uploaded file is empty.")

    if len(content) > settings.max_upload_size_bytes:
        raise UploadValidationError(
            f"File exceeds the {settings.max_upload_size_mb}MB limit."
        )

    signatures = _SIGNATURES.get(content_type, [])
    if signatures and not any(content.startswith(sig) for sig in signatures):
        raise UploadValidationError("File contents do not match the declared type.")

    return hashlib.sha256(content).hexdigest()


def save_file(content: bytes, content_type: str) -> str:
    """Persist bytes to the upload directory and return the absolute stored path."""
    os.makedirs(settings.upload_dir, exist_ok=True)
    extension = ALLOWED_CONTENT_TYPES.get(content_type, "")
    name = f"{uuid.uuid4().hex}{extension}"
    path = os.path.join(settings.upload_dir, name)
    with open(path, "wb") as handle:
        handle.write(content)
    return path


def read_file(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def delete_file(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
