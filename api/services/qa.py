"""Question-answering interface and the original cited mock response."""

from typing import Protocol

from api.schemas import AskResponse, SourceItem


class QAService(Protocol):
    def answer(self, question: str) -> AskResponse: ...


class MockQAService:
    def answer(self, question: str) -> AskResponse:
        # TODO (Day 5 Backend Integration): Bind Muniba's vector retrieval and RAG
        # implementation of QAService in create_app and return citations in this schema.
        return AskResponse(
            answer="Test answer [1]",
            sources=[SourceItem(doc="file.pdf", page=3, snippet="...")],
        )
