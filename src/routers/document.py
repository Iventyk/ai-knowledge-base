from uuid import UUID

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.document import (
    DocumentCreateResponse,
    DocumentListItem,
    ErrorResponse,
)
from src.services.document import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service(
    db: AsyncSession = Depends(get_db),
) -> DocumentService:
    return DocumentService(db)


@router.post(
    "",
    response_model=DocumentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse}},
)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
) -> DocumentCreateResponse:
    document = await service.upload_document(file)
    return DocumentCreateResponse(
        document_id=document.id, status=document.status
    )


@router.get("", response_model=list[DocumentListItem])
async def list_documents(
    service: DocumentService = Depends(get_document_service),
) -> list[DocumentListItem]:
    return await service.list_documents()


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
async def delete_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
) -> Response:
    await service.delete_document(document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
