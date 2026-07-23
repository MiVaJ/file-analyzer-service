from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.schemas.files import (
    DownloadedFileResponse,
    FilesListResponse,
)
from app.services.downloaded_file import DownloadedFileService

router = APIRouter(
    prefix="/api/files",
    tags=["Файлы"],
)


@router.get(
    "",
    response_model=FilesListResponse,
    summary="Получить список скачанных файлов",
    description=(
        "Возвращает список файлов, которые были скачаны сервисом. "
        "Поддерживает пагинацию и сортировку по времени скачивания."
    ),
)
async def get_files(
    page: int = Query(
        1,
        ge=1,
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
    ),
    session: AsyncSession = Depends(get_db),
) -> FilesListResponse:
    """Возвращает скачанные файлы с пагинацией."""

    service = DownloadedFileService(
        session,
    )

    files, total = await service.get_files(
        page,
        limit,
    )

    return FilesListResponse(
        items=[
            DownloadedFileResponse.model_validate(
                file,
            )
            for file in files
        ],
        page=page,
        limit=limit,
        total=total,
    )


@router.get(
    "/ids",
    summary="Получить идентификаторы скачанных файлов",
    description=(
        "Возвращает идентификаторы всех скачанных файлов "
        "для выбора всех файлов при расчёте статистики."
    ),
)
async def get_file_ids(
    session: AsyncSession = Depends(
        get_db,
    ),
) -> dict[str, list[int]]:
    """Возвращает идентификаторы всех файлов."""

    service = DownloadedFileService(
        session,
    )

    return {
        "file_ids": await service.get_all_ids(),
    }
