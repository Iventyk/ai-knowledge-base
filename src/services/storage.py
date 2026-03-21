from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from src.core.config import settings


class FileStorageService:
    async def save(self, file: UploadFile) -> tuple[str, str]:
        safe_name = file.filename or f"document-{uuid4()}.txt"
        file_id = uuid4()
        destination = settings.upload_dir / f"{file_id}_{safe_name}"
        content = await file.read()
        destination.write_bytes(content)
        await file.close()
        return safe_name, str(destination)

    def remove(self, file_path: str) -> None:
        path = Path(file_path)
        if path.exists():
            path.unlink()
