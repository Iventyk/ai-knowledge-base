from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentStatus(str, Enum):
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentCreateResponse(BaseModel):
    document_id: UUID
    status: DocumentStatus


class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    name: str
    status: DocumentStatus
    chunks: int = Field(alias="chunks_count")
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str
