from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, File, HTTPException, Path, UploadFile

from api.dependencies import DocumentStoreDep, SettingsDep
from api.schemas import (
    DeleteDocumentResponse,
    DocumentListResponse,
    DocumentRecord,
    ErrorResponse,
    UploadResponse,
)
from api.services.storage import DocumentConflictError
from api.services.validation import validate_upload

router = APIRouter(tags=["Documents"])


def error_response(description: str, detail: str) -> dict:
    return {
        "description": description,
        "model": ErrorResponse,
        "content": {"application/json": {"example": {"detail": detail}}},
    }


@router.post(
    "/upload",
    status_code=201,
    form_limits={"max_files": 1, "max_fields": 0},
    responses={
        400: error_response("Invalid filename, format or contents.", "The file is empty."),
        409: error_response("Filename conflict.", "A document with this filename already exists."),
        413: error_response("Upload exceeds the size limit.", "File exceeds the 10 MB limit."),
    },
)
def upload_document(
    file: Annotated[UploadFile, File(description="A PDF or UTF-8 TXT document.")],
    settings: SettingsDep,
    store: DocumentStoreDep,
) -> UploadResponse:
    """Store one PDF or UTF-8 TXT file (default limit 10 MB). Filenames must be unique
    ignoring case. Scanned PDFs/OCR are not supported for text extraction.
    """
    upload = validate_upload(file, settings)
    record = DocumentRecord(
        doc_id=uuid4(),
        filename=upload.filename,
        file_type=upload.file_type,
        size_bytes=len(upload.raw_bytes),
        uploaded_at=datetime.now(timezone.utc),
        status="stored_mock",
    )
    try:
        store.add(record, upload.raw_bytes)
    except DocumentConflictError as exc:
        raise HTTPException(409, str(exc)) from exc
    # TODO (Day 5 Backend Integration): Enqueue Furqan's PDF/TXT extraction and
    # chunking for this stored doc_id, then persist its indexed or failed status.
    return UploadResponse(document=record, message="Document stored.")


@router.get("/documents")
def list_documents(store: DocumentStoreDep) -> DocumentListResponse:
    """Return document metadata, newest upload first."""
    documents = store.list_all()
    return DocumentListResponse(documents=documents, total=len(documents))


@router.delete(
    "/documents/{doc_id:uuid}",
    responses={404: error_response("Unknown document ID.", "Document not found.")},
)
def delete_document(
    doc_id: Annotated[UUID, Path(description="Document ID returned by POST /upload.")],
    store: DocumentStoreDep,
) -> DeleteDocumentResponse:
    """Remove a stored document and release its filename for reuse."""
    if not store.delete(doc_id):
        raise HTTPException(404, "Document not found.")
    return DeleteDocumentResponse(doc_id=doc_id, deleted=True, message="Document deleted.")
