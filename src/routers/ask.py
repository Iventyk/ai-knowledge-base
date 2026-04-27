from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.ask import AskErrorResponse, AskRequest, AskResponse
from src.services.qa import QuestionAnswerService

router = APIRouter(tags=["ask"])


def get_question_answer_service(
    db: AsyncSession = Depends(get_db),
) -> QuestionAnswerService:
    return QuestionAnswerService(db)


@router.post(
    "/ask",
    response_model=AskResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": AskErrorResponse},
        status.HTTP_409_CONFLICT: {"model": AskErrorResponse},
    },
)
async def ask_question(
    payload: AskRequest,
    service: QuestionAnswerService = Depends(get_question_answer_service),
) -> AskResponse:
    return await service.ask(payload)
