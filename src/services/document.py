from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.repositories.chunk_embedding import ChunkEmbeddingRepository
from src.repositories.document import DocumentRepository
from src.schemas.document import DocumentListItem
from src.services.storage import FileStorageService
from src.tasks.document import generate_summary_task, process_document_task

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
        suffix = (
            "." + file.filename.rsplit(".", maxsplit=1)[-1].lower()
            if "." in file.filename
            else ""
        )
        if suffix not in ALLOWED_SUFFIXES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supported file types: txt, pdf, md",
            )

        name, file_path = await self.storage.save(file)
        document = await self.repository.create(name=name, file_path=file_path)
        logger.info(
            "document_created",
            document_id=str(document.id),
            filename=document.name,
        )
        process_document_task.delay(str(document.id))
        generate_summary_task.delay(str(document.id))
        return document

    async def list_documents(self) -> list[DocumentListItem]:
        documents = await self.repository.list_all()
        return [
            DocumentListItem.from_model(document) for document in documents
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
        self.storage.remove(document.file_path)
        logger.info(
            "document_deleted",
            document_id=str(document.id),
            filename=document.name,
        )
