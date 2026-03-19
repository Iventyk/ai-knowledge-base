from src.repositories.document import DocumentRepository
from src.tasks.document import process_document_task
from src.db.models.document import Document


class DocumentService:
    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    async def upload_document(self, filename: str) -> Document:
        document = await self.repository.create(name=filename)
        process_document_task.delay(str(document.id))
        return document
