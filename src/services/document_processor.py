from __future__ import annotations
import re
from pathlib import Path
from typing import Any
from uuid import UUID

import structlog
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.models.chunk_embedding import ChunkEmbedding
from src.repositories.chunk_embedding import ChunkEmbeddingRepository
from src.repositories.document import DocumentRepository
from src.schemas.document import DocumentStatus
from src.services.ai import get_embeddings, get_llm

logger = structlog.get_logger(__name__)


class DocumentProcessorService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.documents = DocumentRepository(session)
        self.embeddings = ChunkEmbeddingRepository(session)
        self.embedding_model = get_embeddings()
        self.llm = get_llm()

    async def process_document(self, document_id: UUID) -> None:
        document = await self.documents.get(document_id)
        if document is None:
            logger.warning(
                "document_not_found_for_processing",
                document_id=str(document_id),
            )
            return

        logger.info(
            "document_processing_started", document_id=str(document.id)
        )

        try:
            chunks = await self._load_and_split(document.file_path)
            vectors = self.embedding_model.embed_documents(
                [chunk.page_content for chunk in chunks]
            )
            await self._validate_vector_dimensions(vectors)

            rows = [
                ChunkEmbedding(
                    document_id=document.id,
                    chunk_id=index,
                    content=chunk.page_content,
                    embedding=vector,
                    source_document=document.name,
                )
                for index, (chunk, vector) in enumerate(
                    zip(chunks, vectors, strict=True), start=1
                )
            ]

            await self.embeddings.delete_by_document_id(document.id)
            await self.embeddings.bulk_create(rows)

            document.chunks_count = len(rows)
            document.status = DocumentStatus.PROCESSED.value
            document.summary = await self._generate_summary(chunks)
            document.error_message = None

            await self.session.commit()

            logger.info(
                "document_processing_finished",
                document_id=str(document.id),
                chunks_count=len(rows),
            )

        except Exception as exc:
            await self.session.rollback()
            document = await self.documents.get(document_id)
            if document is None:
                logger.exception(
                    "document_processing_failed_document_missing_after_rollback",
                    document_id=str(document_id),
                    error=str(exc),
                )
                raise
            document.status = DocumentStatus.FAILED.value
            document.error_message = str(exc)
            await self.session.commit()
            logger.exception(
                "document_processing_failed",
                document_id=str(document.id),
                error=str(exc),
            )
            raise

    async def _validate_vector_dimensions(
            self, vectors: list[list[float]]
    ) -> None:
        if not vectors:
            return

        dimensions = {len(vector) for vector in vectors}
        if len(dimensions) > 1:
            raise ValueError(
                "Embedding model returned mixed vector dimensions for "
                "chunks in the same document"
            )

        actual_dimensions = dimensions.pop()
        if actual_dimensions != settings.vector_dimensions:
            raise ValueError(
                "Embedding dimensions mismatch: "
                f"VECTOR_DIMENSIONS={settings.vector_dimensions}, "
                f"model_output={actual_dimensions}. "
                "Update VECTOR_DIMENSIONS and reprocess documents."
            )

        database_dimensions = await self._get_database_vector_dimensions()
        if (
                database_dimensions is not None
                and database_dimensions != actual_dimensions
        ):
            raise ValueError(
                "Embedding dimensions mismatch with database schema: "
                f"database_vector_dimensions={database_dimensions}, "
                f"model_output={actual_dimensions}. "
                "Run a migration (or recreate schema) so the "
                "chunk_embeddings.embedding column matches the "
                "configured embedding model dimensions."
            )

    async def _get_database_vector_dimensions(self) -> int | None:
        query = text(
            "SELECT format_type(a.atttypid, a.atttypmod) "
            "FROM pg_attribute AS a "
            "WHERE a.attrelid = 'chunk_embeddings'::regclass "
            "AND a.attname = 'embedding' "
            "AND NOT a.attisdropped"
        )
        result = await self.session.execute(query)
        type_repr = result.scalar_one_or_none()
        if not isinstance(type_repr, str):
            return None

        match = re.fullmatch(r"vector\((\d+)\)", type_repr)
        if match is None:
            return None

        return int(match.group(1))

    async def generate_summary(self, document_id: UUID) -> None:
        document = await self.documents.get(document_id)
        if document is None or document.summary:
            return

        chunks = await self._load_and_split(document.file_path)
        document.summary = await self._generate_summary(chunks)
        await self.session.commit()

    async def _load_and_split(self, file_path: str):
        loader = self._build_loader(file_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        return splitter.split_documents(docs)

    def _build_loader(self, file_path: str) -> Any:
        suffix = Path(file_path).suffix.lower()
        if suffix == ".pdf":
            return PyPDFLoader(file_path)
        return TextLoader(file_path, autodetect_encoding=True)

    async def _generate_summary(self, chunks) -> str:
        context = "\n\n".join(chunk.page_content for chunk in chunks[:3])
        response = self.llm.invoke(
            "Summarize the document briefly for cataloging purposes.\n\n"
            f"{context}"
        )
        content = response.content
        return (
            content
            if isinstance(content, str)
            else " ".join(map(str, content))
        )
