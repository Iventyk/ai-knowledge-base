import asyncio
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import AsyncSessionLocal
from src.services.document_processor import DocumentProcessorService
from src.tasks.celery import celery_app

logger = structlog.get_logger(__name__)


async def _run_processor(document_id: UUID) -> None:
    async with AsyncSessionLocal() as session:
        processor = DocumentProcessorService(session)
        await processor.process_document(document_id)


async def _run_summary(document_id: UUID) -> None:
    async with AsyncSessionLocal() as session:
        processor = DocumentProcessorService(session)
        await processor.generate_summary(document_id)


@celery_app.task(name="process_document")
def process_document_task(document_id: str) -> None:
    logger.info("celery_process_document_started", document_id=document_id)
    asyncio.run(_run_processor(UUID(document_id)))


@celery_app.task(name="generate_summary")
def generate_summary_task(document_id: str) -> None:
    logger.info("celery_generate_summary_started", document_id=document_id)
    asyncio.run(_run_summary(UUID(document_id)))
