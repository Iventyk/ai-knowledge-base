import structlog
from langchain_core.documents import Document as LCDocument
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
            "You are an assistant answering questions about uploaded documents. "
            "Use only the provided context. If the answer is missing, say so.\n\n"
            "Question: {question}\n\nContext:\n{context}"
        )

    async def ask(self, payload: AskRequest) -> AskResponse:
        documents_result = await self.session.execute(
            select(Document).where(Document.id.in_(payload.document_ids))
        )
        documents = documents_result.scalars().all()
        if not documents:
            raise ValueError("No documents were found for the provided ids")

        processed_ids = [document.id for document in documents if document.status == DocumentStatus.PROCESSED.value]
        if not processed_ids:
            raise ValueError("Selected documents are not processed yet")

        question_embedding = self.embedding_model.embed_query(payload.question)
        chunks = await self.embedding_repository.similarity_search(
            embedding=question_embedding,
            document_ids=processed_ids,
            limit=4,
        )
        context_documents = [
            LCDocument(
                page_content=chunk.content,
                metadata={"document": chunk.source_document, "chunk_id": chunk.chunk_id},
            )
            for chunk in chunks
        ]
        context = "\n\n".join(
            f"[{doc.metadata['document']}#{doc.metadata['chunk_id']}] {doc.page_content}"
            for doc in context_documents
        )
        message = self.prompt.invoke({"question": payload.question, "context": context})
        answer = self.llm.invoke(message).content
        logger.info("ai_question_answered", question=payload.question, chunks=len(chunks))
        return AskResponse(
            answer=answer,
            sources=[
                AskSource(document=chunk.source_document, chunk_id=chunk.chunk_id)
                for chunk in chunks
            ],
        )
    