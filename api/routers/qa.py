from fastapi import APIRouter

from api.dependencies import QAServiceDep
from api.schemas import AskRequest, AskResponse

router = APIRouter(tags=["Q&A"])


@router.post("/ask")
def ask_question(payload: AskRequest, service: QAServiceDep) -> AskResponse:
    """Return the mock answer and its citations."""
    return service.answer(payload.question)
