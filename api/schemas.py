"""Pydantic request and response schemas for the AI QueryDocs API."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response payload for the health check endpoint."""

    status: str
    app: str
    environment: str


class SourceItem(BaseModel):
    """Citation metadata for a retrieved document snippet."""

    doc: str
    page: int
    snippet: str


class AskRequest(BaseModel):
    """Request payload for asking a question."""

    question: str


class AskResponse(BaseModel):
    """Response payload containing an answer and cited sources."""

    answer: str
    sources: list[SourceItem]
