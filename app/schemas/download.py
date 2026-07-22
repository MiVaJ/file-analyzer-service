from pydantic import BaseModel

from app.schemas.download_progress import DownloadProgress


class StartDownloadResponse(BaseModel):
    """Ответ запуска скачивания."""

    download_id: str
    status: str


class DownloadProgressResponse(BaseModel):
    """Ответ получения прогресса."""

    progress: DownloadProgress
