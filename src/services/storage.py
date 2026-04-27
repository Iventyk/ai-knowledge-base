import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from src.core.config import settings


class FileStorageService:
    async def save(self, file: UploadFile) -> tuple[str, str]:
        safe_name = file.filename or f"document-{uuid4()}.txt"
        file_id = uuid4()
        destination = settings.upload_dir / f"{file_id}_{safe_name}"
        await asyncio.to_thread(
            destination.parent.mkdir, parents=True, exist_ok=True
        )
        await asyncio.to_thread(destination.write_bytes, b"")
        with destination.open("ab") as stream:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await asyncio.to_thread(stream.write, chunk)
        await file.close()
        return safe_name, str(destination)

    async def remove(self, file_path: str) -> None:
        path = Path(file_path)
        if path.exists():
            await asyncio.to_thread(path.unlink)
