"""
Storage abstraction for evidence and other uploads.

Step 9: local file storage. Designed so backends (S3, R2, Supabase) can be swapped later.
"""

import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings


@dataclass(frozen=True)
class StorageSaveResult:
    """Result of saving an uploaded file."""

    stored_path: str  # path relative to upload_dir, e.g. "evidence/abc.pdf"
    file_url: str  # URL path for clients, e.g. "/uploads/evidence/abc.pdf"
    original_filename: str
    detected_content_type: str | None


def _safe_extension(original_filename: str, allowed_extensions: list[str]) -> str:
    """Extract and validate extension; return lowercase without dot or 'bin' if invalid."""
    base, _, ext = original_filename.rpartition(".")
    ext = ext.strip().lower() if ext else ""
    if ext and ext in allowed_extensions:
        return ext
    return "bin"


def _sanitize_filename(name: str) -> str:
    """Keep only safe characters for display; not used for stored path."""
    return re.sub(r"[^\w\s\-\.]", "", name).strip() or "file"


def save_upload(
    file_content: bytes,
    original_filename: str,
    content_type: str | None,
    destination_subdir: str,
) -> StorageSaveResult:
    """
    Save uploaded content to local disk under upload_dir/destination_subdir.
    Returns stored_path (relative), file_url, original_filename, detected_content_type.
    """
    settings = get_settings()
    allowed = settings.allowed_evidence_extensions_list
    ext = _safe_extension(original_filename, allowed)
    if ext == "bin" and original_filename:
        ext = _safe_extension(original_filename, allowed)
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    stored_relative = f"{destination_subdir.strip('/')}/{unique_name}"
    root = Path(settings.upload_dir).resolve()
    full_path = root / stored_relative
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(file_content)
    file_url = build_public_url(stored_relative)
    return StorageSaveResult(
        stored_path=stored_relative,
        file_url=file_url,
        original_filename=_sanitize_filename(original_filename) or unique_name,
        detected_content_type=content_type,
    )


def delete_file(storage_path: str) -> None:
    """Delete file at storage_path (relative to upload_dir). No-op if missing."""
    settings = get_settings()
    root = Path(settings.upload_dir).resolve()
    full = root / storage_path
    if full.is_file():
        full.unlink()


def build_public_url(storage_path: str) -> str:
    """Build URL path for static serving, e.g. /uploads/evidence/foo.pdf."""
    path = storage_path.replace("\\", "/").lstrip("/")
    return f"/uploads/{path}"
