from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str) -> Document:
        document = Document(name=name)
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_all(self) -> list[Document]:
        result = await self.session.execute(select(Document))
        return list(result.scalars().all())

    async def delete(self, document: Document):
        await self.session.delete(document)
        await self.session.commit()
