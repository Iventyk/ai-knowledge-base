from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.chunk_embedding import ChunkEmbedding


class ChunkEmbeddingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_create(self, chunks: Sequence[ChunkEmbedding]) -> None:
        self.session.add_all(list(chunks))
        await self.session.commit()

    async def delete_by_document_id(self, document_id: UUID) -> None:
        await self.session.execute(delete(ChunkEmbedding).where(ChunkEmbedding.document_id == document_id))
        await self.session.commit()

    async def similarity_search(self, *, embedding: list[float], document_ids: Sequence[UUID], limit: int) -> Sequence[ChunkEmbedding]:
        statement = (
            select(ChunkEmbedding)
            .where(ChunkEmbedding.document_id.in_(document_ids))
            .order_by(ChunkEmbedding.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()
