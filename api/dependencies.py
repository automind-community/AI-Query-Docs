"""FastAPI dependency providers for services owned by each app instance."""

from typing import Annotated

from fastapi import Depends, Request

from api.config import Settings
from api.services.qa import QAService
from api.services.storage import DocumentStore


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_document_store(request: Request) -> DocumentStore:
    return request.app.state.document_store


def get_qa_service(request: Request) -> QAService:
    return request.app.state.qa_service


SettingsDep = Annotated[Settings, Depends(get_settings)]
DocumentStoreDep = Annotated[DocumentStore, Depends(get_document_store)]
QAServiceDep = Annotated[QAService, Depends(get_qa_service)]
