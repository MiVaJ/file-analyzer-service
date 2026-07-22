from datetime import datetime

from pydantic import BaseModel


class DownloadProgress(BaseModel):
    """Модель прогресса скачивания файлов."""

    status: str
    received_names: int
    downloaded: int
    failed: int
    started_at: datetime
