from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentStatus(StrEnum):
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentCreateResponse(BaseModel):
    document_id: UUID
    status: DocumentStatus


class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: DocumentStatus
    chunks: int
    created_at: datetime

    @classmethod
    def from_model(cls, document) -> "DocumentListItem":
        return cls(
            id=document.id,
            name=document.name,
            status=document.status,
            chunks=document.chunks_count,
            created_at=document.created_at,
        )
