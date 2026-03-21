from pathlib import Path
from uuid import UUID

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.models.chunk_embedding import ChunkEmbedding
from src.repositories.chunk_embedding import ChunkEmbeddingRepository
from src.repositories.document import DocumentRepository
from src.schemas.document import DocumentStatus
from src.services.ai import get_embeddings, get_llm


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
            return

        try:
            chunks = await self._load_and_split(document.file_path)
            vectors = self.embedding_model.embed_documents(
                [chunk.page_content for chunk in chunks]
            )

            rows = [
                ChunkEmbedding(
                    document_id=document.id,
                    chunk_id=index,
                    content=chunk.page_content,
                    embedding=vector,
                    source_document=document.name,
                )
                for index, (chunk, vector) in enumerate(
                    zip(chunks, vectors, strict=False), start=1
                )
            ]

            await self.embeddings.bulk_create(rows)

            document.chunks_count = len(rows)
            document.status = DocumentStatus.PROCESSED.value
            document.summary = await self._generate_summary(chunks)
            document.error_message = None

            await self.session.commit()

        except Exception as exc:
            document.status = DocumentStatus.FAILED.value
            document.error_message = str(exc)
            await self.session.commit()
            raise

    async def generate_summary(self, document_id: UUID) -> None:
        document = await self.documents.get(document_id)
        if document is None:
            return

        if not document.summary:
            chunks = await self._load_and_split(document.file_path)
            document.summary = await self._generate_summary(chunks)
            await self.session.commit()

    async def _load_and_split(self, file_path: str):
        suffix = Path(file_path).suffix.lower()

        if suffix == ".pdf":
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, autodetect_encoding=True)

        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        return splitter.split_documents(docs)

    def _normalize_llm_output(self, content: str | list) -> str:
        """Normalize LLM output to string."""
        if isinstance(content, str):
            return content

        return " ".join(str(item) for item in content)

    async def _generate_summary(self, chunks) -> str:
        context = "\n\n".join(chunk.page_content for chunk in chunks[:3])

        response = self.llm.invoke(
            "Summarize the document briefly for cataloging purposes.\n\n"
            + context
        )

        return self._normalize_llm_output(response.content)
