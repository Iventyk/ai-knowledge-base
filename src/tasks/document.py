import asyncio
import threading
from uuid import UUID
from collections.abc import Coroutine
from typing import Any

import structlog
from celery.signals import worker_process_shutdown

from src.db.session import AsyncSessionLocal
from src.services.document_processor import DocumentProcessorService
from src.tasks.celery import celery_app

logger = structlog.get_logger(__name__)
_worker_loop: asyncio.AbstractEventLoop | None = None
_worker_loop_lock = threading.Lock()


def _get_worker_loop() -> asyncio.AbstractEventLoop:
    global _worker_loop
    with _worker_loop_lock:
        if _worker_loop is None or _worker_loop.is_closed():
            _worker_loop = asyncio.new_event_loop()
        return _worker_loop


def _run_in_worker_loop(coro: Coroutine[Any, Any, None]) -> None:
    loop = _get_worker_loop()
    loop.run_until_complete(coro)


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
    _run_in_worker_loop(_run_processor(UUID(document_id)))


@celery_app.task(name="generate_summary")
def generate_summary_task(document_id: str) -> None:
    logger.info("celery_generate_summary_started", document_id=document_id)
    _run_in_worker_loop(_run_summary(UUID(document_id)))


@worker_process_shutdown.connect
def _close_worker_loop(**_: object) -> None:
    global _worker_loop
    with _worker_loop_lock:
        if _worker_loop is not None and not _worker_loop.is_closed():
            _worker_loop.close()
            _worker_loop = None
