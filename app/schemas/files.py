from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DownloadedFileResponse(BaseModel):
    """Информация о скачанном файле."""

    model_config = ConfigDict(
        from_attributes=True,
    )
    id: int
    filename: str
    downloaded_at: datetime


class FilesListResponse(BaseModel):
    """Список скачанных файлов."""

    items: list[DownloadedFileResponse]
    page: int
    limit: int
    total: int
