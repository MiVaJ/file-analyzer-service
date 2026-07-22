from datetime import datetime, timezone

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
