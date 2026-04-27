from uuid import UUID
from pathlib import Path

import structlog
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.chunk_embedding import ChunkEmbeddingRepository
from src.repositories.document import DocumentRepository
from src.schemas.document import DocumentListItem
from src.schemas.document import DocumentStatus
from src.services.storage import FileStorageService
from src.tasks.document import process_document_task

logger = structlog.get_logger(__name__)
ALLOWED_SUFFIXES = {".txt", ".pdf", ".md"}


class DocumentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = DocumentRepository(session)
        self.embeddings = ChunkEmbeddingRepository(session)
        self.storage = FileStorageService()

    async def upload_document(self, file: UploadFile):
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must have a filename",
            )

        suffix = Path(file.filename).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supported file types: txt, pdf, md",
            )

        name, file_path = await self.storage.save(file)
        document = await self.repository.create(name=name, file_path=file_path)
        await self.session.commit()

        logger.info(
            "document_created",
            document_id=str(document.id),
            filename=document.name,
        )
        try:
            process_document_task.delay(str(document.id))
        except Exception as exc:
            document.status = DocumentStatus.FAILED.value
            document.error_message = "Unable to enqueue document processing"
            await self.session.commit()
            logger.exception(
                "document_processing_enqueue_failed",
                document_id=str(document.id),
                error=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to enqueue document processing task",
            ) from exc
        return document

    async def list_documents(self) -> list[DocumentListItem]:
        documents = await self.repository.list_all()
        return [
            DocumentListItem.model_validate(document) for document in documents
        ]

    async def delete_document(self, document_id: UUID) -> None:
        document = await self.repository.get(document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        await self.embeddings.delete_by_document_id(document.id)
        await self.repository.delete(document)
        await self.session.commit()
        await self.storage.remove(document.file_path)
        logger.info(
            "document_deleted",
            document_id=str(document.id),
            filename=document.name,
        )
