"""Public JSON contracts and examples shared by the routes and OpenAPI."""

from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, field_validator

FileType = Literal["PDF", "TXT"]
_SOURCE = {"doc": "handbook.pdf", "page": 3, "snippet": "Submit claims within 30 days."}
_DOC_ID = "70c3a0a6-a030-4c9d-b4a1-e1e930d48d02"
_DOCUMENT = {
    "doc_id": _DOC_ID,
    "filename": "handbook.pdf",
    "file_type": "PDF",
    "size_bytes": 18432,
    "uploaded_at": "2026-11-29T09:30:00Z",
    "status": "stored_mock",
}


class APIModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class HealthResponse(APIModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"status": "ok", "app": "AI QueryDocs", "environment": "development"}]
    })
    status: Literal["ok"] = Field(description="Service liveness indicator.")
    app: str = Field(min_length=1, description="Configured application name.")
    environment: str = Field(min_length=1, description="Deployment environment.")


class AskRequest(APIModel):
    # Existing clients may send additional metadata alongside the question.
    model_config = ConfigDict(extra="ignore", json_schema_extra={
        "examples": [{"question": "How long do I have to submit a claim?"}]
    })
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        description="Question to answer, containing at least one non-whitespace character."
    )


class SourceItem(APIModel):
    model_config = ConfigDict(json_schema_extra={"examples": [_SOURCE]})
    doc: str = Field(min_length=1, description="Filename of the cited document.")
    page: int = Field(ge=1, description="One-based page number.")
    snippet: str = Field(min_length=1, description="Excerpt supporting the answer.")


class AskResponse(APIModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"answer": "Claims are due within 30 days [1].", "sources": [_SOURCE]}]
    })
    answer: str = Field(min_length=1, description="Answer with numbered references to sources.")
    sources: list[SourceItem] = Field(description="Citation details in reference order.")


class DocumentRecord(APIModel, frozen=True):
    model_config = ConfigDict(json_schema_extra={"examples": [_DOCUMENT]})
    doc_id: UUID = Field(description="Unique document identifier.")
    filename: str = Field(min_length=1, description="Sanitized basename, preserving case.")
    file_type: FileType = Field(description="Validated document format.")
    size_bytes: int = Field(gt=0, description="Original file length in bytes.")
    uploaded_at: AwareDatetime = Field(description="ISO 8601 upload timestamp in UTC.")
    status: Literal["stored_mock", "indexed", "failed"] = Field(
        description="Processing state. The in-memory implementation creates stored_mock records."
    )

    @field_validator("uploaded_at")
    @classmethod
    def normalize_to_utc(cls, value: datetime) -> datetime:
        return value.astimezone(timezone.utc)


class UploadResponse(APIModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"document": _DOCUMENT, "message": "Document stored."}]
    })
    document: DocumentRecord = Field(description="Metadata for the newly stored document.")
    message: str = Field(min_length=1, description="Upload confirmation.")


class DocumentListResponse(APIModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"documents": [_DOCUMENT], "total": 1}]
    })
    documents: list[DocumentRecord] = Field(description="Stored documents, newest first.")
    total: int = Field(ge=0, description="Number of documents in this list.")


class DeleteDocumentResponse(APIModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"doc_id": _DOC_ID, "deleted": True, "message": "Document deleted."}]
    })
    doc_id: UUID = Field(description="Identifier of the deleted document.")
    deleted: bool = Field(description="True when the document has been removed.")
    message: str = Field(min_length=1, description="Deletion confirmation.")


class ErrorResponse(APIModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"detail": "Document not found."}]})
    detail: str = Field(min_length=1, description="Human-readable reason the request failed.")
