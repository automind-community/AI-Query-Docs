"""Validate untrusted multipart filenames and contents before storage."""

import ntpath
import re
import unicodedata
from dataclasses import dataclass

from fastapi import HTTPException, UploadFile

from api.config import Settings
from api.schemas import FileType

_BINARY_CONTROLS = re.compile(rb"[\x00-\x08\x0e-\x1f\x7f]")


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    file_type: FileType
    raw_bytes: bytes


def validate_upload(file: UploadFile, settings: Settings) -> ValidatedUpload:
    """Read a spooled file in the route's worker thread, with a hard byte limit."""
    filename = unicodedata.normalize("NFC", ntpath.basename(file.filename or "").strip())
    if not filename or filename in {".", ".."}:
        raise HTTPException(400, "A filename is required.")
    if not filename.isprintable() or ":" in filename:
        raise HTTPException(400, "The filename contains an invalid character.")

    extension = ntpath.splitext(filename)[1].lower()
    if extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Unsupported extension. Upload a .pdf or .txt file.")

    limit = settings.max_file_size_bytes
    too_large = f"File exceeds the {settings.MAX_FILE_SIZE_MB} MB limit."
    if file.size is not None and file.size > limit:
        raise HTTPException(413, too_large)
    raw_bytes = file.file.read(limit + 1)
    if len(raw_bytes) > limit:
        raise HTTPException(413, too_large)
    if not raw_bytes:
        raise HTTPException(400, "The file is empty.")

    if extension == ".pdf":
        if not raw_bytes.startswith(b"%PDF-"):
            raise HTTPException(400, "PDF files must start with the %PDF- header.")
        return ValidatedUpload(filename, "PDF", raw_bytes)

    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "TXT files must be valid UTF-8.") from exc
    if _BINARY_CONTROLS.search(raw_bytes):
        raise HTTPException(400, "TXT files must contain text without binary control characters.")
    if not text.strip():
        raise HTTPException(400, "TXT files must contain non-whitespace text.")
    return ValidatedUpload(filename, "TXT", raw_bytes)
