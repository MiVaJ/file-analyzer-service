from collections import deque

from app.services.source_api_client import (
    DownloadedFilePayload,
    SourceApiClient,
)

DOWNLOAD_BATCH_SIZE = 3


class CatalogDownloader:
    """Сервис управления скачивания файлов из каталога."""

    def __init__(
        self,
        client: SourceApiClient,
    ) -> None:
        self._client = client

        self._queue: deque[str] = deque()
        self._queued_names: set[str] = set()

        self._catalog_finished = False

    async def download_next_batch(self) -> list[DownloadedFilePayload]:
        """Скачивает следующую доступную группу файлов."""

        await self._fill_queue()

        file_names = self._take_batch()

        if not file_names:
            return []

        files = await self._client.download_files(
            file_names,
        )

        await self._client.mark_files_downloaded(
            file_names,
        )

        return files

    async def _fill_queue(self) -> None:
        """Получает новые имена, если в очереди недостаточно файлов."""

        if self._catalog_finished:
            return

        if len(self._queue) >= DOWNLOAD_BATCH_SIZE:
            return

        file_names = await self._client.get_file_names()

        self._add_unique_names(
            file_names,
        )

        if len(file_names) < DOWNLOAD_BATCH_SIZE:
            self._catalog_finished = True

    def _add_unique_names(
        self,
        file_names: list[str],
    ) -> None:
        """Добавляет новые имена файлов без дубликатов."""

        for filename in file_names:
            if filename in self._queued_names:
                continue

            self._queue.append(
                filename,
            )

            self._queued_names.add(
                filename,
            )

    def _take_batch(self) -> list[str]:
        """Извлекает следующую пачку файлов из очереди."""

        batch: list[str] = []

        while self._queue and len(batch) < DOWNLOAD_BATCH_SIZE:
            file_names = self._queue.popleft()

            self._queued_names.remove(
                file_names,
            )

            batch.append(
                file_names,
            )

        return batch
