from unittest.mock import AsyncMock

import pytest

from app.services.catalog_downloader import CatalogDownloader
from app.services.source_api_client import DownloadedFilePayload


@pytest.mark.asyncio
async def test_downloader_downloads_batch_from_empty_queue() -> None:
    """Проверяет скачивание полной пачки при пустой очереди."""
    client = AsyncMock()

    client.get_file_names.return_value = [
        "file_1.txt",
        "file_2.txt",
        "file_3.txt",
    ]

    client.download_files.return_value = [
        DownloadedFilePayload(
            filename="file_1.txt",
            content="data",
        ),
        DownloadedFilePayload(
            filename="file_2.txt",
            content="data",
        ),
        DownloadedFilePayload(
            filename="file_3.txt",
            content="data",
        ),
    ]

    downloader = CatalogDownloader(
        client=client,
    )

    result = await downloader.download_next_batch()

    assert len(result) == 3

    client.get_file_names.assert_awaited_once()

    client.download_files.assert_awaited_once_with(
        [
            "file_1.txt",
            "file_2.txt",
            "file_3.txt",
        ],
    )

    client.mark_files_downloaded.assert_awaited_once_with(
        [
            "file_1.txt",
            "file_2.txt",
            "file_3.txt",
        ],
    )


@pytest.mark.asyncio
async def test_downloader_refills_queue_when_not_enough_files_left() -> None:
    """Проверяет дозаполнение очереди при недостаточном количестве файлов."""
    client = AsyncMock()

    client.get_file_names.side_effect = [
        [
            "file_1.txt",
            "file_2.txt",
            "file_3.txt",
            "file_4.txt",
        ],
        [
            "file_5.txt",
            "file_6.txt",
        ],
    ]

    client.download_files.side_effect = [
        [
            DownloadedFilePayload(
                filename="file_1.txt",
                content="data",
            ),
            DownloadedFilePayload(
                filename="file_2.txt",
                content="data",
            ),
            DownloadedFilePayload(
                filename="file_3.txt",
                content="data",
            ),
        ],
        [
            DownloadedFilePayload(
                filename="file_4.txt",
                content="data",
            ),
            DownloadedFilePayload(
                filename="file_5.txt",
                content="data",
            ),
            DownloadedFilePayload(
                filename="file_6.txt",
                content="data",
            ),
        ],
    ]

    downloader = CatalogDownloader(client)

    first = await downloader.download_next_batch()
    second = await downloader.download_next_batch()

    assert len(first) == 3
    assert len(second) == 3

    assert client.get_file_names.await_count == 2


@pytest.mark.asyncio
async def test_downloader_removes_duplicates_inside_catalog_response() -> None:
    """Проверяет удаление дубликатов из ответа каталога."""
    client = AsyncMock()

    client.get_file_names.return_value = [
        "file_1.txt",
        "file_1.txt",
        "file_2.txt",
    ]

    client.download_files.return_value = []

    downloader = CatalogDownloader(client)

    await downloader.download_next_batch()

    client.download_files.assert_awaited_once_with(
        [
            "file_1.txt",
            "file_2.txt",
        ],
    )


@pytest.mark.asyncio
async def test_downloader_marks_catalog_finished_after_short_response() -> None:
    """Проверяет завершение каталога после короткого ответа."""
    client = AsyncMock()

    client.get_file_names.return_value = [
        "file_1.txt",
    ]

    client.download_files.return_value = []

    downloader = CatalogDownloader(client)

    first = await downloader.download_next_batch()
    second = await downloader.download_next_batch()

    assert first == []
    assert second == []

    client.get_file_names.assert_awaited_once()


@pytest.mark.asyncio
async def test_downloader_returns_empty_when_catalog_has_no_files() -> None:
    """Проверяет пустой результат при отсутствии файлов в каталоге."""
    client = AsyncMock()

    client.get_file_names.return_value = []

    downloader = CatalogDownloader(client)

    result = await downloader.download_next_batch()

    assert result == []

    client.download_files.assert_not_awaited()
    client.mark_files_downloaded.assert_not_awaited()
