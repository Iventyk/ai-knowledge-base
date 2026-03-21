from uuid import UUID

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.document import (
    DocumentCreateResponse,
    DocumentErrorResponse,
    DocumentListItem,
)
from src.services.document import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={status.HTTP_400_BAD_REQUEST: {"model": DocumentErrorResponse}},
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentCreateResponse:
    document = await DocumentService(db).upload_document(file)
    return DocumentCreateResponse(
        document_id=document.id, status=document.status
    )


@router.get("", response_model=list[DocumentListItem])
async def list_documents(
    db: AsyncSession = Depends(get_db),
) -> list[DocumentListItem]:
    return await DocumentService(db).list_documents()


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_404_NOT_FOUND: {"model": DocumentErrorResponse}},
)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    await DocumentService(db).delete_document(document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
