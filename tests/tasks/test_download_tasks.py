from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.source_api_client import DownloadedFilePayload
from app.tasks.download_tasks import _download_catalog


@pytest.mark.asyncio
async def test_download_catalog_processes_single_batch() -> None:
    """Проверяет обработку одной пачки файлов."""

    payload = DownloadedFilePayload(
        filename="file_1.txt",
        content="123",
    )

    downloader = AsyncMock()
    downloader.download_next_batch.side_effect = [
        [payload],
        [],
    ]

    tracker = AsyncMock()
    storage = MagicMock()
    storage.save.return_value = "downloads/file_1.txt"

    file_service = AsyncMock()
    session = AsyncMock()

    redis = AsyncMock()
    redis.close = AsyncMock()

    with (
        patch("app.tasks.download_tasks.Redis.from_url", return_value=redis),
        patch("app.tasks.download_tasks.DownloadProgressTracker", return_value=tracker),
        patch("app.tasks.download_tasks.FileStorage", return_value=storage),
        patch("app.tasks.download_tasks.SourceApiClient") as client_cls,
        patch("app.tasks.download_tasks.CatalogDownloader", return_value=downloader),
        patch(
            "app.tasks.download_tasks.DownloadedFileService", return_value=file_service
        ),
        patch("app.tasks.download_tasks.AsyncSessionLocal") as session_factory,
    ):
        client = AsyncMock()
        client_cls.return_value = client

        session_factory.return_value.__aenter__.return_value = session

        await _download_catalog("download-id")

    tracker.create.assert_awaited_once_with("download-id")

    storage.save.assert_called_once_with(payload)

    file_service.create.assert_awaited_once_with(
        filename="file_1.txt",
        path="downloads/file_1.txt",
    )

    session.commit.assert_awaited_once()

    client.mark_files_downloaded.assert_awaited_once_with(
        ["file_1.txt"],
    )

    tracker.increment_downloaded.assert_awaited_once_with(
        "download-id",
        1,
    )

    tracker.mark_finished.assert_awaited_once_with(
        "download-id",
    )


@pytest.mark.asyncio
async def test_download_catalog_finishes_when_catalog_is_empty() -> None:
    """Проверяет завершение задачи при пустом каталоге."""

    downloader = AsyncMock()
    downloader.download_next_batch.return_value = []

    tracker = AsyncMock()

    redis = AsyncMock()
    redis.close = AsyncMock()

    with (
        patch("app.tasks.download_tasks.Redis.from_url", return_value=redis),
        patch("app.tasks.download_tasks.DownloadProgressTracker", return_value=tracker),
        patch("app.tasks.download_tasks.FileStorage"),
        patch("app.tasks.download_tasks.SourceApiClient"),
        patch("app.tasks.download_tasks.CatalogDownloader", return_value=downloader),
        patch("app.tasks.download_tasks.DownloadedFileService"),
        patch("app.tasks.download_tasks.AsyncSessionLocal") as session_factory,
    ):
        session_factory.return_value.__aenter__.return_value = AsyncMock()

        await _download_catalog("download-id")

    tracker.create.assert_awaited_once_with("download-id")

    tracker.increment_downloaded.assert_not_awaited()

    tracker.mark_finished.assert_awaited_once_with("download-id")


@pytest.mark.asyncio
async def test_download_catalog_processes_multiple_batches() -> None:
    """Проверяет обработку нескольких пачек файлов."""

    downloader = AsyncMock()

    downloader.download_next_batch.side_effect = [
        [
            DownloadedFilePayload(
                filename="file_1.txt",
                content="1",
            ),
            DownloadedFilePayload(
                filename="file_2.txt",
                content="2",
            ),
        ],
        [
            DownloadedFilePayload(
                filename="file_3.txt",
                content="3",
            ),
        ],
        [],
    ]

    tracker = AsyncMock()

    redis = AsyncMock()
    redis.close = AsyncMock()

    with (
        patch(
            "app.tasks.download_tasks.Redis.from_url",
            return_value=redis,
        ),
        patch(
            "app.tasks.download_tasks.DownloadProgressTracker",
            return_value=tracker,
        ),
        patch(
            "app.tasks.download_tasks.FileStorage",
        ) as storage_cls,
        patch(
            "app.tasks.download_tasks.SourceApiClient",
        ) as client_cls,
        patch(
            "app.tasks.download_tasks.CatalogDownloader",
            return_value=downloader,
        ),
        patch(
            "app.tasks.download_tasks.DownloadedFileService",
        ) as service_cls,
        patch(
            "app.tasks.download_tasks.AsyncSessionLocal",
        ) as session_factory,
    ):
        storage = MagicMock()
        storage.save.return_value = "downloads/file.txt"
        storage_cls.return_value = storage

        client = AsyncMock()
        client_cls.return_value = client

        service = AsyncMock()
        service_cls.return_value = service

        session = AsyncMock()
        session_factory.return_value.__aenter__.return_value = session

        await _download_catalog(
            "download-id",
        )

    assert downloader.download_next_batch.await_count == 3

    assert tracker.add_received_names.await_count == 2
    assert tracker.increment_downloaded.await_count == 2

    assert storage.save.call_count == 3
    assert service.create.await_count == 3

    assert client.mark_files_downloaded.await_count == 2

    tracker.mark_finished.assert_awaited_once_with(
        "download-id",
    )

    session.commit.assert_awaited()
    redis.close.assert_awaited_once()
