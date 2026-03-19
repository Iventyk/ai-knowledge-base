from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.orm import Session

from src.services.document import DocumentService
from src.repositories.document import DocumentRepository
from src.db.session import get_db

documents_router = APIRouter(tags=["documents"])


@documents_router.post("/documents")
def upload_document(file: UploadFile, db: Session = Depends(get_db)):
    service = DocumentService(DocumentRepository(db))

    document = service.upload_document(file.filename)

    return {
        "document_id": str(document.id),
        "status": document.status
    }
