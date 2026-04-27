from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.document import ErrorResponse as AskErrorResponse


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    document_ids: list[UUID] = Field(min_length=1)


class AskSource(BaseModel):
    document: str
    chunk_id: int


class AskResponse(BaseModel):
    answer: str
    sources: list[AskSource]
