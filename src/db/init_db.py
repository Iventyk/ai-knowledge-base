from sqlalchemy import text

from src.db.base import Base
from src.db.models import ChunkEmbedding, Document  # noqa: F401
from src.db.session import engine


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.create_all)
