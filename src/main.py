from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.logging import setup_logging
from src.db.init_db import init_db
from src.routers import ask_router, documents_router

setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    logger.info("server_started")
    yield


app = FastAPI(
    title="AI Knowledge Base API", version="1.0.0", lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(ask_router)
