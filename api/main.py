"""FastAPI application factory and Uvicorn entry point."""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint

from api.config import Settings
from api.routers import documents, health, qa
from api.services.qa import MockQAService, QAService
from api.services.storage import DocumentStore, InMemoryDocumentStore


def create_app(
    *,
    settings: Settings | None = None,
    document_store: DocumentStore | None = None,
    qa_service: QAService | None = None,
) -> FastAPI:
    settings = settings if settings is not None else Settings.from_env()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Store PDF and TXT documents and ask questions with citations. "
        "The default services use process-local storage and return a mock answer.",
        openapi_tags=[
            {"name": "System", "description": "Service health and environment."},
            {"name": "Q&A", "description": "Questions, answers and source citations."},
            {"name": "Documents", "description": "Document uploads, inventory and deletion."},
        ],
    )
    app.state.settings = settings
    # TODO (Day 5 Backend Integration): Supply Muniba's Supabase DocumentStore here,
    # with durable file bytes, a unique filename key and vector cleanup on deletion.
    app.state.document_store = (
        document_store if document_store is not None else InMemoryDocumentStore()
    )
    app.state.qa_service = qa_service if qa_service is not None else MockQAService()

    @app.middleware("http")
    async def json_upload_errors(request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        # The multipart body limiter can emit a plain-text 413 before routing.
        content_type = response.headers.get("content-type", "")
        if response.status_code == 413 and content_type.startswith("text/plain"):
            return JSONResponse(
                {"detail": "Multipart request exceeds the upload size limit."}, status_code=413
            )
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.include_router(health.router)
    app.include_router(qa.router)
    # Bound multipart parsing itself while allowing room for the file's headers and framing.
    app.include_router(documents.router, max_body_size=settings.max_file_size_bytes + 64 * 1024)
    return app


app = create_app()
