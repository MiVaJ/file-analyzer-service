from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.downloaded_file import (
    DownloadedFilesNotFoundError,
)
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
    ) -> None:
        """Идемпотентно сохраняет информацию о скачанном файле."""

        stmt = (
            pg_insert(DownloadedFile)
            .values(
                filename=filename,
                path=path,
                downloaded_at=datetime.now(
                    timezone.utc,
                ),
            )
            .on_conflict_do_nothing(
                index_elements=["filename"],
            )
        )

        await self._session.execute(stmt)

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

    async def get_by_ids(
        self,
        file_ids: list[int],
    ) -> list[DownloadedFile]:
        """Возвращает скачанные файлы по идентификаторам."""

        result = await self._session.execute(
            select(
                DownloadedFile,
            ).where(
                DownloadedFile.id.in_(
                    file_ids,
                ),
            ),
        )

        files = list(
            result.scalars().all(),
        )

        found_ids = {file.id for file in files}

        missing_ids = set(file_ids) - found_ids

        if missing_ids:
            raise DownloadedFilesNotFoundError(
                list(missing_ids),
            )

        return files

    async def get_all_ids(
        self,
    ) -> list[int]:
        """Возвращает идентификаторы всех скачанных файлов."""

        result = await self._session.execute(
            select(
                DownloadedFile.id,
            ).order_by(
                DownloadedFile.downloaded_at.desc(),
            ),
        )

        return list(
            result.scalars().all(),
        )
