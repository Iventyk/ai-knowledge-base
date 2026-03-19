from src.repositories.document import DocumentRepository
from src.tasks.document import process_document_task


class DocumentService:
    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    def upload_document(self, filename: str):
        document = self.repository.create(name=filename)

        process_document_task.delay(str(document.id))

        return document
