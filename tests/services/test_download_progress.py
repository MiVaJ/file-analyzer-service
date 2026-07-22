import fakeredis.aioredis
import pytest

from app.services.download_progress import DownloadProgressTracker


@pytest.mark.asyncio
async def test_create_creates_initial_download_progress() -> None:
    """Проверяет создание начального прогресса загрузки."""

    redis = fakeredis.aioredis.FakeRedis()

    tracker = DownloadProgressTracker(
        redis,
    )

    progress = await tracker.create(
        "download-1",
    )

    assert progress.status == "running"
    assert progress.received_names == 0
    assert progress.downloaded == 0
    assert progress.failed == 0

    stored = await tracker.get(
        "download-1",
    )

    assert stored == progress


@pytest.mark.asyncio
async def test_add_received_names_updates_progress() -> None:
    """Проверяет увеличение количества полученных имён файлов."""

    redis = fakeredis.aioredis.FakeRedis()

    tracker = DownloadProgressTracker(
        redis,
    )

    await tracker.create(
        "download-1",
    )

    await tracker.add_received_names(
        "download-1",
        5,
    )

    progress = await tracker.get(
        "download-1",
    )

    assert progress is not None
    assert progress.received_names == 5


@pytest.mark.asyncio
async def test_increment_downloaded_updates_progress() -> None:
    """Проверяет увеличение количества скачанных файлов."""

    redis = fakeredis.aioredis.FakeRedis()

    tracker = DownloadProgressTracker(
        redis,
    )

    await tracker.create(
        "download-1",
    )

    await tracker.increment_downloaded(
        "download-1",
        3,
    )

    progress = await tracker.get(
        "download-1",
    )

    assert progress is not None
    assert progress.downloaded == 3


@pytest.mark.asyncio
async def test_increment_failed_updates_progress() -> None:
    """Проверяет увеличение количества файлов с ошибками."""

    redis = fakeredis.aioredis.FakeRedis()

    tracker = DownloadProgressTracker(
        redis,
    )

    await tracker.create(
        "download-1",
    )

    await tracker.increment_failed(
        "download-1",
    )

    progress = await tracker.get(
        "download-1",
    )

    assert progress is not None
    assert progress.failed == 1


@pytest.mark.asyncio
async def test_mark_finished_changes_status() -> None:
    """Проверяет изменение статуса загрузки на завершённый."""

    redis = fakeredis.aioredis.FakeRedis()

    tracker = DownloadProgressTracker(
        redis,
    )

    await tracker.create(
        "download-1",
    )

    await tracker.mark_finished(
        "download-1",
    )

    progress = await tracker.get(
        "download-1",
    )

    assert progress is not None
    assert progress.status == "finished"


@pytest.mark.asyncio
async def test_get_returns_none_for_missing_download() -> None:
    """Проверяет отсутствие прогресса для неизвестной загрузки."""

    redis = fakeredis.aioredis.FakeRedis()

    tracker = DownloadProgressTracker(
        redis,
    )

    progress = await tracker.get(
        "unknown",
    )

    assert progress is None
