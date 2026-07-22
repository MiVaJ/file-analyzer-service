from datetime import datetime

from pydantic import BaseModel


class DownloadedFileSchema(BaseModel):
    """Схема скачанного файла для API."""

    id: int
    filename: str
    downloaded_at: datetime

    model_config = {
        "from_attributes": True,
    }
