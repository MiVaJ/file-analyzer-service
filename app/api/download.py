from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter

from app.schemas.download import (
    DownloadProgressResponse,
    StartDownloadResponse,
)
from app.schemas.download_progress import DownloadProgress
from app.tasks.download_tasks import download_catalog

router = APIRouter(
    prefix="/api/download",
    tags=["Скачивание"],
)


@router.post(
    "/start",
    summary="Запустить скачивание каталога",
    description=(
        "Запускает процесс скачивания файлов из внешнего каталога. "
        "Скачивание выполняется в фоновом режиме до полного получения каталога."
    ),
    response_model=StartDownloadResponse,
)
async def start_download() -> StartDownloadResponse:
    """Запускает процесс скачивания каталога."""

    download_id = str(uuid4())

    download_catalog.delay(
        download_id,
    )

    return StartDownloadResponse(
        download_id=download_id,
        status="started",
    )


@router.get(
    "/progress/{download_id}",
    summary="Получить прогресс скачивания",
    description=(
        "Возвращает текущий статус процесса скачивания, "
        "количество полученных названий файлов и количество скачанных файлов."
    ),
    response_model=DownloadProgressResponse,
)
async def get_download_progress(
    download_id: str,
) -> DownloadProgressResponse:
    """Возвращает текущий прогресс загрузки."""

    return DownloadProgressResponse(
        progress=DownloadProgress(
            status="running",
            received_names=0,
            downloaded=0,
            failed=0,
            started_at=datetime.now(),
        ),
    )
