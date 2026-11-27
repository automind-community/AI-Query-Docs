"""FastAPI application entrypoint and route definitions."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.schemas import AskRequest, AskResponse, HealthResponse, SourceItem

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API for AI QueryDocs - Upload documents and ask questions with citations."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check() -> HealthResponse:
    """Return service health and runtime environment metadata."""
    return HealthResponse(
        status="ok",
        app=settings.APP_NAME,
        environment=settings.APP_ENV,
    )


@app.post("/ask", response_model=AskResponse, tags=["Q&A"])
def ask_question(payload: AskRequest) -> AskResponse:
    """Answer a user question with citations (Day 1 stub response)."""
    # Temporary stub response until the RAG pipeline is integrated.
    _ = payload
    return AskResponse(
        answer="Test answer [1]",
        sources=[
            SourceItem(
                doc="file.pdf",
                page=3,
                snippet="...",
            )
        ],
    )
