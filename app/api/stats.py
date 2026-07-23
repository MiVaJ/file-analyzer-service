from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.schemas.stats import (
    FileDigitStats,
    StatsRequest,
    StatsResponse,
)
from app.services.downloaded_file import DownloadedFileService
from app.services.stats_calculator import DigitStatisticsService

router = APIRouter(
    prefix="/api/stats",
    tags=["Статистика"],
)


@router.post(
    "/compute",
    response_model=StatsResponse,
    summary="Вычислить статистику по цифрам",
    description=(
        "Вычисляет количество вхождений каждой цифры "
        "во всех выбранных файлах и отдельно для каждого файла."
    ),
)
async def compute_statistics(
    request: StatsRequest,
    session: AsyncSession = Depends(
        get_db,
    ),
) -> StatsResponse:
    """Вычисляет статистику по выбранным файлам."""

    downloaded_file_service = DownloadedFileService(
        session,
    )

    files = await downloaded_file_service.get_by_ids(
        request.file_ids,
    )

    statistics_service = DigitStatisticsService()

    total_statistics, per_file_statistics = statistics_service.calculate_statistics(
        files,
    )

    return StatsResponse(
        total=total_statistics,
        files=[
            FileDigitStats(
                filename=filename,
                digits=digits,
            )
            for filename, digits in per_file_statistics.items()
        ],
    )
