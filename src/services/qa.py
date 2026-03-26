from __future__ import annotations
import structlog
from fastapi import HTTPException, status
from langchain_core.documents import Document as LangChainDocument
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.db.models.document import Document
from src.repositories.chunk_embedding import ChunkEmbeddingRepository
from src.schemas.ask import AskRequest, AskResponse, AskSource
from src.schemas.document import DocumentStatus
from src.services.ai import get_embeddings, get_llm

logger = structlog.get_logger(__name__)


class QuestionAnswerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.embedding_repository = ChunkEmbeddingRepository(session)
        self.embedding_model = get_embeddings()
        self.llm = get_llm()
        self.prompt = ChatPromptTemplate.from_template(
            "You answer questions about uploaded documents. "
            "Use only the provided context. "
            "If the answer is missing, clearly say that "
            "the documents do not contain it.\n\n"
            "Question: {question}\n\n"
            "Context:\n{context}"
        )

    async def ask(self, payload: AskRequest) -> AskResponse:
        result = await self.session.execute(
            select(Document).where(Document.id.in_(payload.document_ids))
        )
        documents = result.scalars().all()
        if not documents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No documents were found for the provided ids",
            )

        processed_ids = [
            document.id
            for document in documents
            if document.status == DocumentStatus.PROCESSED.value
        ]
        if not processed_ids:
            document_statuses = {
                str(document.id): document.status for document in documents
            }
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": (
                        "Selected documents are not ready for questions yet. "
                        "Only documents with status 'processed' can be used."
                    ),
                    "document_statuses": document_statuses,
                },
            )

        question_embedding = self.embedding_model.embed_query(payload.question)
        chunks = await self.embedding_repository.similarity_search(
            embedding=question_embedding,
            document_ids=processed_ids,
            limit=settings.top_k,
        )
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "No indexed chunks were found for the selected "
                    "documents"
                ),
            )

        context_documents = [
            LangChainDocument(
                page_content=chunk.content,
                metadata={
                    "document": chunk.source_document,
                    "chunk_id": chunk.chunk_id,
                },
            )
            for chunk in chunks
        ]
        context = "\n\n".join(
            (
                f"[{doc.metadata['document']}#"
                f"{doc.metadata['chunk_id']}] {doc.page_content}"
            )
            for doc in context_documents
        )
        prompt_message = self.prompt.invoke(
            {"question": payload.question, "context": context}
        )
        raw_answer = self.llm.invoke(prompt_message).content
        answer = (
            raw_answer
            if isinstance(raw_answer, str)
            else "".join(map(str, raw_answer))
        )

        logger.info(
            "ai_question_answered",
            question=payload.question,
            document_ids=[
                str(document_id) for document_id in payload.document_ids
            ],
            chunks=len(chunks),
        )
        return AskResponse(
            answer=answer,
            sources=[
                AskSource(
                    document=chunk.source_document, chunk_id=chunk.chunk_id
                )
                for chunk in chunks
            ],
        )
