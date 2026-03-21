from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, *, name: str, file_path: str, status: str = "processing"
    ) -> Document:
        document = Document(name=name, file_path=file_path, status=status)
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get(self, document_id: UUID) -> Document | None:
        return await self.session.get(Document, document_id)

    async def list_all(self) -> Sequence[Document]:
        result = await self.session.execute(
            select(Document).order_by(Document.created_at.desc())
        )
        return result.scalars().all()

    async def delete(self, document: Document) -> None:
        await self.session.delete(document)
        await self.session.commit()
