from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.downloaded_file import DownloadedFile


class DownloadedFileService:
    """Сервис работы со скачанными файлами."""

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def create(
        self,
        filename: str,
        path: str,
    ) -> DownloadedFile:
        """Сохраняет информацию о скачанном файле."""

        file = DownloadedFile(
            filename=filename,
            path=path,
            downloaded_at=datetime.now(
                timezone.utc,
            ),
        )

        self._session.add(
            file,
        )

        await self._session.flush()

        return file

    async def get_files(
        self,
        page: int,
        limit: int,
    ) -> tuple[list[DownloadedFile], int]:
        """Возвращает список файлов с пагинацией."""

        total = await self._session.scalar(
            select(func.count()).select_from(DownloadedFile)
        )

        result = await self._session.execute(
            select(DownloadedFile)
            .order_by(
                DownloadedFile.downloaded_at.desc(),
            )
            .offset(
                (page - 1) * limit,
            )
            .limit(
                limit,
            )
        )

        files = list(
            result.scalars().all(),
        )

        return files, total or 0
