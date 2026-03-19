from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from src.routers import ask_router, documents_router
from src.core.logging import setup_logging
from src.db.session import engine
from src.db.base import Base

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    for attempt in range(5):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("DB connected ✅")
            break
        except Exception:
            print(f"DB not ready... retry {attempt + 1}/5")
            await asyncio.sleep(2)
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

app.include_router(ask_router)
app.include_router(documents_router)
