from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.document import DocumentService
from src.repositories.document import DocumentRepository
from src.db.session import get_db

documents_router = APIRouter(tags=["documents"])


@documents_router.post("/documents")
async def upload_document(
    file: UploadFile, db: AsyncSession = Depends(get_db)
):
    if file.filename is None:
        raise HTTPException(
            status_code=400, detail="File must have a filename"
        )

    service = DocumentService(DocumentRepository(db))
    document = await service.upload_document(file.filename)

    return {"document_id": str(document.id), "status": document.status}
